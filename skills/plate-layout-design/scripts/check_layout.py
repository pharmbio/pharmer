#!/usr/bin/env python3
"""Check a plate layout CSV against its design spec.

    python scripts/check_layout.py results/x_layout.csv --spec results/x_design.json
    python scripts/check_layout.py someone_elses_layout.csv --plate-format 384 --empty-edge 1

The spec can be the *_design.json written by design_layout.py or the original
spec JSON. Without a spec only the structural checks run.

Each line of the report is PASS, WARN or FAIL. Exit code 1 if any FAIL.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

WELL_RE = re.compile(r"^([A-Za-z]+)0*(\d+)$")
PLATE_FORMATS = {6: (2, 3), 12: (3, 4), 24: (4, 6), 48: (6, 8), 96: (8, 12), 384: (16, 24), 1536: (32, 48)}


def parse_well(well: str):
    m = WELL_RE.match(str(well).strip())
    if not m:
        return None
    row = 0
    for ch in m.group(1).upper():
        row = row * 26 + (ord(ch) - 64)
    return row, int(m.group(2))  # 1-based


def _series_partition_exists(wells_by_conc, check_rows, check_cols, limit=200_000):
    """Can the wells be grouped into series (one well per concentration each)
    so that no series repeats a row (and/or column)?

    wells_by_conc: list over concentrations of [(row, col), ...]. Returns True,
    False, or None when the search hit `limit` nodes. Series whose
    concentrations have unequal well counts on this plate are not checkable as
    full series; the shortest count is used and leftovers must still fit.
    """
    lists = sorted(wells_by_conc, key=len, reverse=True)
    n_series = len(lists[0])
    series = [(set(), set()) for _ in range(n_series)]
    nodes = [0]

    def place(ci, wi):
        if ci == len(lists):
            return True
        if wi == len(lists[ci]):
            return place(ci + 1, 0)
        nodes[0] += 1
        if nodes[0] > limit:
            raise TimeoutError
        r, c = lists[ci][wi]
        used = set()  # series already taken by an earlier well of this concentration
        for w2 in range(wi):
            used.add(assign[(ci, w2)])
        for si, (rows, cols) in enumerate(series):
            if si in used or (check_rows and r in rows) or (check_cols and c in cols):
                continue
            if check_rows:
                rows.add(r)
            if check_cols:
                cols.add(c)
            assign[(ci, wi)] = si
            if place(ci, wi + 1):
                return True
            rows.discard(r)  # safe: r was not in rows before (or rows unused)
            cols.discard(c)
            del assign[(ci, wi)]
        return False

    assign = {}
    try:
        return place(0, 0)
    except (TimeoutError, RecursionError):
        return None


def _r(status, name, detail):
    return {"status": status, "check": name, "detail": detail}


def load_spec(path: Path | None) -> dict | None:
    if path is None:
        return None
    data = json.loads(Path(path).read_text())
    if "spec" in data:  # *_design.json
        return data["spec"]
    from design_layout import normalise  # raw spec: resolve defaults the same way
    spec = normalise(data, {})
    out = {k: v for k, v in spec.items() if k != "items"}
    for role, key in (("compound", "compounds"), ("control", "controls"), ("solvent", "solvents")):
        out[key] = [
            {"name": i["name"], "concentrations_uM": [c for c, _ in i["entries"]], "replicates": [r for _, r in i["entries"]]}
            if role != "solvent" else {"name": i["name"], "replicates": i["entries"][0][1]}
            for i in spec["items"] if i["role"] == role
        ]
    return out


def expected_counts(spec: dict) -> dict[tuple[str, str], int]:
    exp = {}
    for key in ("compounds", "controls"):
        for item in spec.get(key, []):
            concs = item["concentrations_uM"]
            reps = item["replicates"] if isinstance(item["replicates"], list) else [item["replicates"]] * len(concs)
            for c, r in zip(concs, reps):
                exp[(item["name"], f"{float(c):.6g}")] = r
    for item in spec.get("solvents", []):
        exp[(item["name"], "0")] = item["replicates"]
    return exp


def run_checks(layout_path, spec_path=None, plate_rows=None, plate_cols=None, empty_edge=None) -> list[dict]:
    res: list[dict] = []
    spec = load_spec(Path(spec_path)) if spec_path else None
    df = pd.read_csv(layout_path, dtype=str).fillna("")

    # 1. schema -------------------------------------------------------------
    need = ["plateID", "well", "cmpdname", "CONCuM"]
    missing = [c for c in need if c not in df.columns]
    if missing:
        return [_r("FAIL", "columns", f"missing {missing}; expected plateID,well,cmpdname,CONCuM[,cmpdnum,role]")]
    blank = df[(df["cmpdname"].str.strip() == "") | (df["well"].str.strip() == "")]
    res.append(_r("FAIL" if len(blank) else "PASS", "columns", f"{len(df)} rows" + (f"; {len(blank)} rows have no well or name" if len(blank) else "")))
    df = df.drop(blank.index)
    df["conc"] = pd.to_numeric(df["CONCuM"], errors="coerce")
    df["conc_key"] = df["conc"].map(lambda v: f"{v:.6g}" if pd.notna(v) else "nan")

    # geometry ----------------------------------------------------------------
    if spec:
        plate_rows, plate_cols = spec["plate_rows"], spec["plate_cols"]
        empty_edge = spec.get("empty_edge", 1) if empty_edge is None else empty_edge
    parsed = df["well"].map(parse_well)
    bad = df[parsed.isna()]
    if len(bad):
        res.append(_r("FAIL", "well names", f"unparseable wells: {bad['well'].head(5).tolist()}"))
        df, parsed = df[parsed.notna()], parsed[parsed.notna()]
    df["row"] = parsed.map(lambda p: p[0])
    df["col"] = parsed.map(lambda p: p[1])
    if plate_rows is None or plate_cols is None:
        plate_rows, plate_cols = (16, 24) if (df["row"].max() > 8 or df["col"].max() > 12) else (8, 12)
        res.append(_r("WARN", "plate size", f"no spec/plate format given; assuming {plate_rows}x{plate_cols}"))
    outside = df[(df["row"] > plate_rows) | (df["col"] > plate_cols)]
    res.append(_r("FAIL" if len(outside) else "PASS", "wells on plate",
                  f"{len(outside)} wells outside a {plate_rows}x{plate_cols} plate" if len(outside) else f"all wells fit {plate_rows}x{plate_cols}"))

    dup = df[df.duplicated(["plateID", "row", "col"], keep=False)]
    res.append(_r("FAIL" if len(dup) else "PASS", "unique wells",
                  f"duplicate wells: {sorted(set(dup['plateID'] + '/' + dup['well']))[:10]}" if len(dup) else "no well used twice"))

    if empty_edge:
        e = int(empty_edge)
        on_edge = df[(df["row"] <= e) | (df["row"] > plate_rows - e) | (df["col"] <= e) | (df["col"] > plate_cols - e)]
        res.append(_r("FAIL" if len(on_edge) else "PASS", "edge wells empty",
                      f"{len(on_edge)} samples in the outer {e} row/col ring: {on_edge['well'].head(8).tolist()}" if len(on_edge)
                      else f"outer {e} ring empty (fill these with medium/buffer to limit evaporation)"))

    plates = sorted(df["plateID"].unique(), key=lambda p: (len(p), p))
    n_plates = len(plates)
    e = int(empty_edge or 0)
    inner = (plate_rows - 2 * e) * (plate_cols - 2 * e)
    used = df.groupby("plateID").size().to_dict()
    res.append(_r("PASS", "fill", ", ".join(f"{p}: {used[p]}/{inner} usable wells" for p in plates)))

    if not spec:
        return res

    # 2. counts vs spec -------------------------------------------------------
    exp = expected_counts(spec)
    got = Counter(zip(df["cmpdname"], df["conc_key"]))
    problems = []
    for key, n in exp.items():
        if got.get(key, 0) != n:
            problems.append(f"{key[0]} @ {key[1]} µM: expected {n}, found {got.get(key, 0)}")
    for key in got:
        if key not in exp:
            problems.append(f"{key[0]} @ {key[1]} µM: not in the spec ({got[key]} wells)")
    res.append(_r("FAIL" if problems else "PASS", "replicate counts",
                  "; ".join(problems[:10]) if problems else f"{len(exp)} condition(s), all counts match the spec"))

    # 3. dose series spread over rows / columns -------------------------------
    # PLAID requires each replicate *series* (one well per concentration) to use
    # distinct rows/columns. The CSV does not say which well belongs to which
    # series, so search for a grouping that satisfies the rule.
    use_rows = spec.get("concentrations_on_different_rows", True)
    use_cols = spec.get("concentrations_on_different_columns", True)
    if use_rows or use_cols:
        in_rows = plate_rows - 2 * e
        viol, unknown = [], []
        for item in spec.get("compounds", []):
            concs = [f"{float(c):.6g}" for c in item["concentrations_uM"]]
            if len(concs) < 2:
                continue
            reps = item["replicates"] if isinstance(item["replicates"], list) else [item["replicates"]] * len(concs)
            groups = defaultdict(list)
            for c, r in zip(concs, reps):
                groups[r].append(c)
            sub = df[df["cmpdname"] == item["name"]]
            for plate, pdf in sub.groupby("plateID"):
                for gconcs in groups.values():
                    if len(gconcs) < 2:
                        continue
                    wells = [list(zip(pdf.loc[pdf["conc_key"] == c, "row"], pdf.loc[pdf["conc_key"] == c, "col"]))
                             for c in gconcs]
                    check_rows = use_rows and len(gconcs) <= in_rows  # PLAID only spreads the first `rows` levels
                    ok = _series_partition_exists(wells, check_rows, use_cols)
                    if ok is False:
                        viol.append(f"{item['name']} on {plate}")
                    elif ok is None:
                        unknown.append(f"{item['name']} on {plate}")
        axes = " and ".join(x for x, f in (("rows", use_rows), ("columns", use_cols)) if f)
        if viol:
            res.append(_r("FAIL", f"dose series on different {axes}",
                          "no way to split these wells into replicate series with distinct " + axes + ": " + "; ".join(viol[:6])))
        elif unknown:
            res.append(_r("WARN", f"dose series on different {axes}", "could not verify (search limit): " + "; ".join(unknown[:6])))
        else:
            res.append(_r("PASS", f"dose series on different {axes}", "every compound's wells split into replicate series with distinct " + axes))

    # 4. replicates on different plates ------------------------------------
    if spec.get("replicates_on_different_plates") and n_plates > 1:
        viol = []
        for (name, conc), sub in df.groupby(["cmpdname", "conc_key"]):
            if (name, conc) not in exp:
                continue
            cap = math.ceil(exp[(name, conc)] / n_plates)
            worst = sub.groupby("plateID").size().max()
            if worst > cap:
                viol.append(f"{name} @ {conc}: {worst} on one plate (max {cap})")
        res.append(_r("FAIL" if viol else "PASS", "replicates on different plates", "; ".join(viol[:6]) if viol else "replicates split across plates"))

    # 5. control / solvent balance (warn only) ------------------------------
    r_mid = e + (plate_rows - 2 * e) / 2
    c_mid = e + (plate_cols - 2 * e) / 2
    ctl_names = [i["name"] for i in spec.get("controls", [])] + [i["name"] for i in spec.get("solvents", [])]
    notes, warn = [], False
    for name in ctl_names:
        for plate, pdf in df[df["cmpdname"] == name].groupby("plateID"):
            n = len(pdf)
            if n < 4:
                continue
            top = int((pdf["row"] <= r_mid).sum())
            left = int((pdf["col"] <= c_mid).sum())
            quad = Counter(zip(pdf["row"] <= r_mid, pdf["col"] <= c_mid))
            q = [quad.get(k, 0) for k in ((True, True), (True, False), (False, True), (False, False))]
            tol = max(2, math.ceil(0.25 * n))
            bad = abs(top - (n - top)) > tol or abs(left - (n - left)) > tol or (n >= 8 and min(q) == 0)
            warn |= bad
            notes.append(f"{name}/{plate}: n={n} top/bottom {top}/{n - top}, left/right {left}/{n - left}, quadrants {q}" + (" <- unbalanced" if bad else ""))
    if notes:
        res.append(_r("WARN" if warn else "PASS", "control balance", "; ".join(notes)))
    return res


def format_report(results: list[dict]) -> str:
    lines = [f"{r['status']:4}  {r['check']}: {r['detail']}" for r in results]
    n_fail = sum(r["status"] == "FAIL" for r in results)
    n_warn = sum(r["status"] == "WARN" for r in results)
    lines.append(f"==> {'FAILED' if n_fail else 'OK'}: {n_fail} fail, {n_warn} warn")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("layout", type=Path)
    ap.add_argument("--spec", type=Path, help="*_design.json or the original spec JSON")
    ap.add_argument("--plate-format", type=int, choices=sorted(PLATE_FORMATS))
    ap.add_argument("--empty-edge", type=int)
    args = ap.parse_args(argv)
    rows = cols = None
    if args.plate_format:
        rows, cols = PLATE_FORMATS[args.plate_format]
    results = run_checks(args.layout, args.spec, rows, cols, args.empty_edge)
    print(format_report(results))
    return 1 if any(r["status"] == "FAIL" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
