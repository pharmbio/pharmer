#!/usr/bin/env python3
"""Design a microplate layout with PLAID (MiniZinc constraint solver).

Input is a design spec (JSON) or an iPLAID "PLAID feeder" CSV
(compound_name,concentration_uM,replicate_number,role).

    python scripts/design_layout.py spec.json --out results/
    python scripts/design_layout.py feeder.csv --plate-format 384 --out results/
    python scripts/design_layout.py spec.json --dry-run      # preflight only, no solve

Outputs (in --out, prefixed by --name):
    <name>_layout.csv     plateID,well,cmpdname,CONCuM,cmpdnum,role   (iPLAID layout format)
    <name>_platemap.csv   one grid per plate, cell = "name @ conc"
    <name>_layout.png     plate map figure
    <name>_design.json    resolved spec + solver settings + seed (for reproducing)
    <name>_check.txt      output of check_layout.py

Exit codes: 0 = layout written and all checks passed, 1 = bad input / preflight
error, 2 = solver found no layout, 3 = layout written but a check failed.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from collections import OrderedDict, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from plaid_core import Compound, Control, PlateConfig, PlateDesigner  # noqa: E402
from plaid_core.exceptions import (  # noqa: E402
    NoSolutionFoundError,
    PLAIDError,
    SolverError,
)
from plaid_core.validators import validate_minizinc_available  # noqa: E402

PLATE_FORMATS = {6: (2, 3), 12: (3, 4), 24: (4, 6), 48: (6, 8), 96: (8, 12), 384: (16, 24), 1536: (32, 48)}

DEFAULTS = {
    "plate_format": 384,
    "empty_edge": 1,
    "concentrations_on_different_rows": True,
    "concentrations_on_different_columns": True,
    "replicates_on_different_plates": False,
    "allow_empty_wells": True,
    "timeout_seconds": 300,
    "threads": 8,
    "seed": 1,
    "attempts": 1,
}

ROLES = ("compound", "control", "solvent")
FEEDER_ROLE_MAP = {
    "treatment": "compound", "compound": "compound", "sample": "compound",
    "control": "control", "positive_control": "control", "negative_control": "control",
    "solvent": "solvent", "vehicle": "solvent",
}


class SpecError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def fmt_conc(value: float) -> str:
    """Short, stable text for a µM value (0.1 -> '0.1', 10.0 -> '10')."""
    return f"{float(value):.6g}"


def load_feeder_csv(path: Path) -> dict:
    """iPLAID feeder CSV -> spec dict (compounds/controls/solvents only)."""
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cols = {c.strip().lower(): c for c in (reader.fieldnames or [])}
        need = ["compound_name", "concentration_um", "replicate_number"]
        missing = [c for c in need if c not in cols]
        if missing:
            raise SpecError(
                f"{path.name}: missing columns {missing}. A feeder CSV needs "
                "compound_name,concentration_uM,replicate_number[,role]."
            )
        groups: dict[tuple[str, str], list[tuple[float, int]]] = OrderedDict()
        for i, row in enumerate(reader, start=2):
            name = (row[cols["compound_name"]] or "").strip()
            if not name:
                continue
            raw_role = (row.get(cols.get("role", ""), "") or "treatment").strip().lower()
            role = FEEDER_ROLE_MAP.get(raw_role)
            if role is None:
                raise SpecError(f"{path.name} line {i}: unknown role '{raw_role}'. Use treatment, control or solvent.")
            try:
                conc = float(row[cols["concentration_um"]])
                reps = int(float(row[cols["replicate_number"]]))
            except (TypeError, ValueError):
                raise SpecError(f"{path.name} line {i}: concentration_uM and replicate_number must be numbers.")
            groups.setdefault((role, name), []).append((conc, reps))

    spec: dict = {"compounds": [], "controls": [], "solvents": []}
    for (role, name), rows in groups.items():
        if role == "solvent":
            spec["solvents"].append({"name": name, "replicates": sum(r for _, r in rows)})
        else:
            key = "compounds" if role == "compound" else "controls"
            spec[key].append({
                "name": name,
                "concentrations_uM": [c for c, _ in rows],
                "replicates": [r for _, r in rows],
            })
    return spec


def load_spec(path: Path) -> dict:
    if not path.exists():
        raise SpecError(f"Input file not found: {path}")
    if path.suffix.lower() == ".csv":
        return load_feeder_csv(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SpecError(f"{path.name} is not valid JSON: {exc}")


# ---------------------------------------------------------------------------
# Normalisation + preflight
# ---------------------------------------------------------------------------

def _check_name(name: str, where: str) -> str:
    name = str(name).strip()
    if not name:
        raise SpecError(f"{where}: empty name.")
    for bad in (",", '"', "\n"):
        if bad in name:
            raise SpecError(f'{where}: name "{name}" contains {bad!r}; remove it (it breaks the layout CSV).')
    return name


def _entries(item: dict, role: str, idx: int) -> list[tuple[float, int]]:
    where = f"{role} #{idx + 1} ({item.get('name', '?')})"
    if role == "solvent":
        reps = item.get("replicates")
        if not isinstance(reps, int) or reps < 1:
            raise SpecError(f"{where}: 'replicates' must be an integer >= 1.")
        return [(0.0, reps)]
    concs = item.get("concentrations_uM", item.get("concentration_uM"))
    if concs is None:
        raise SpecError(f"{where}: give 'concentrations_uM' (list of µM values).")
    if not isinstance(concs, list):
        concs = [concs]
    if not concs:
        raise SpecError(f"{where}: 'concentrations_uM' is empty.")
    concs = [float(c) for c in concs]
    if any(c <= 0 for c in concs):
        raise SpecError(f"{where}: concentrations must be > 0 µM. Put vehicle-only wells under 'solvents'.")
    if len({fmt_conc(c) for c in concs}) != len(concs):
        raise SpecError(f"{where}: duplicate concentration values {concs}.")
    reps = item.get("replicates")
    if isinstance(reps, list):
        if len(reps) != len(concs):
            raise SpecError(f"{where}: 'replicates' list must have one entry per concentration.")
    else:
        reps = [reps] * len(concs)
    if any(not isinstance(r, int) or r < 1 for r in reps):
        raise SpecError(f"{where}: replicates must be integers >= 1.")
    return list(zip(concs, reps))


def normalise(raw: dict, overrides: dict) -> dict:
    spec = dict(DEFAULTS)
    spec.update({k: v for k, v in raw.items() if k not in ("compounds", "controls", "solvents")})
    spec.update({k: v for k, v in overrides.items() if v is not None})

    if "plate_rows" in spec and "plate_cols" in spec and "plate_format" not in raw and overrides.get("plate_format") is None:
        rows, cols = int(spec["plate_rows"]), int(spec["plate_cols"])
    else:
        fmt = int(spec["plate_format"])
        if fmt not in PLATE_FORMATS:
            raise SpecError(f"plate_format {fmt} unknown; use one of {sorted(PLATE_FORMATS)} or give plate_rows/plate_cols.")
        rows, cols = PLATE_FORMATS[fmt]
    spec["plate_rows"], spec["plate_cols"] = rows, cols
    spec["plate_format"] = rows * cols

    seen: dict[str, str] = {}
    items = []
    for role, key in (("compound", "compounds"), ("control", "controls"), ("solvent", "solvents")):
        for idx, item in enumerate(raw.get(key) or []):
            name = _check_name(item.get("name", ""), f"{role} #{idx + 1}")
            low = name.casefold()
            if low in seen:
                raise SpecError(f'"{name}" is listed twice (as {seen[low]} and {role}). Merge the entries.')
            seen[low] = role
            items.append({"name": name, "role": role, "entries": _entries(item, role, idx)})
    if not items:
        raise SpecError("Spec has no compounds, controls or solvents.")
    spec["items"] = items
    return spec


def build_plaid_groups(spec: dict):
    """Split each item into PLAID entities with uniform replicate counts.

    PLAID needs one replicate count per compound. A compound whose
    concentrations have different replicate counts becomes one PLAID compound
    per replicate count (the spreading constraint then holds within each group).
    Returns (compounds, controls, lookup) where lookup maps
    (internal_name, conc_label) -> (display_name, conc_uM, role).
    """
    compounds, controls, lookup = [], [], {}
    for n, item in enumerate(spec["items"], start=1):
        by_reps: dict[int, list[float]] = OrderedDict()
        for conc, reps in item["entries"]:
            by_reps.setdefault(reps, []).append(conc)
        for g, (reps, concs) in enumerate(by_reps.items(), start=1):
            internal = f"{item['role'][:3]}{n}g{g}"
            labels = [f"L{i}" for i in range(1, len(concs) + 1)]
            for lab, conc in zip(labels, concs):
                lookup[(internal, lab)] = (item["name"], conc, item["role"])
            if item["role"] == "compound":
                compounds.append(Compound(name=internal, concentrations=len(concs), replicates=reps, concentration_names=labels))
            else:
                controls.append(Control(name=internal, concentration_levels=len(concs), replicates=reps, concentration_names=labels))
    return compounds, controls, lookup


def preflight(spec: dict, compounds, controls) -> tuple[list[str], list[str], dict]:
    """Mirror the MiniZinc model's own asserts so failures come with a fix."""
    errors, warnings = [], []
    rows, cols, edge = spec["plate_rows"], spec["plate_cols"], int(spec["empty_edge"])
    in_rows, in_cols = rows - 2 * edge, cols - 2 * edge
    if in_rows <= 0 or in_cols <= 0:
        errors.append(f"empty_edge={edge} leaves no usable wells on a {rows}x{cols} plate.")
        return errors, warnings, {}
    if in_rows % 2 or in_cols % 2:
        errors.append(
            f"PLAID needs an even number of usable rows and columns; {rows}x{cols} with empty_edge={edge} "
            f"leaves {in_rows}x{in_cols}. Change empty_edge (e.g. {edge + 1 if (rows - 2 * (edge + 1)) % 2 == 0 else max(edge - 1, 0)})."
        )
    inner = in_rows * in_cols
    total = sum(c.concentrations * c.replicates for c in compounds) + sum(c.concentration_levels * c.replicates for c in controls)
    n_plates = max(math.ceil(total / inner), 1)
    empty = n_plates * inner - total
    n_controls = sum(c.concentration_levels * c.replicates for c in controls)
    summary = {
        "plate": f"{rows}x{cols}", "usable_area": f"{in_rows}x{in_cols}", "usable_wells_per_plate": inner,
        "sample_wells": total, "control_and_solvent_wells": n_controls, "plates_needed": n_plates,
        "empty_usable_wells": empty, "fill_pct": round(100 * total / (n_plates * inner), 1),
    }

    if empty and not spec["allow_empty_wells"]:
        errors.append(
            f"{empty} usable wells would stay empty but allow_empty_wells=false. Add {empty} replicate wells "
            "(e.g. more solvent wells) or set allow_empty_wells=true."
        )
    if compounds:
        reps = [c.replicates for c in compounds]
        concs = [c.concentrations for c in compounds]
        ctl_floor = sum((c.concentration_levels * c.replicates) // n_plates for c in controls)
        e01 = math.ceil(sum(reps) / n_plates) * min(concs) + ctl_floor
        e02 = (sum(reps) // n_plates - 1) * min(concs) + max(concs) + ctl_floor
        if e01 > inner or e02 > inner:
            errors.append(
                "Compounds and controls cannot be divided evenly across plates (PLAID E01/E02). Reduce replicates, "
                "make the total sample count fit whole plates better, or use a larger plate format."
            )
        if max(concs) > in_rows and spec["concentrations_on_different_rows"]:
            warnings.append(
                f"A compound has {max(concs)} concentrations but only {in_rows} usable rows; only the first "
                f"{in_rows} can be forced onto different rows."
            )
        if spec["replicates_on_different_plates"] and max(reps) > n_plates:
            errors.append(
                f"replicates_on_different_plates=true needs at least {max(reps)} plates but the design fills only "
                f"{n_plates}. Set it to false, or reduce replicates to {n_plates}."
            )
    if len(controls) == 1:
        c = controls[0]
        if c.replicates > math.ceil(inner / 4) * n_plates:
            errors.append(
                f"Only one control/solvent type with {c.replicates} replicates; PLAID allows at most "
                f"{math.ceil(inner / 4) * n_plates} when there is a single control type. Reduce it or split it "
                "(e.g. add a second control)."
            )
    if n_plates > 3:
        errors.append(
            f"The design needs {n_plates} plates. PLAID solves are slow beyond ~3 plates; split the compounds "
            "into separate designs (one per plate or batch) and run them separately."
        )
    if summary["fill_pct"] >= 95:
        warnings.append(
            f"Plates are {summary['fill_pct']}% full. Near-full designs are the hardest to solve: expect long "
            "solves and use --attempts 3 or more."
        )
    if total and n_controls / total > 0.25:
        warnings.append(
            f"{n_controls} of {total} wells are controls/solvents. Many controls make the control-balancing "
            "constraints hard; expect longer solves."
        )
    return errors, warnings, summary


# ---------------------------------------------------------------------------
# Solve + write
# ---------------------------------------------------------------------------

def well_sort_key(well: str):
    letters = "".join(ch for ch in well if ch.isalpha())
    digits = "".join(ch for ch in well if ch.isdigit())
    row = 0
    for ch in letters.upper():
        row = row * 26 + (ord(ch) - 64)
    return row, int(digits or 0)


def layout_rows(layout, lookup) -> list[dict]:
    out = []
    for w in layout.wells:
        key = (w["cmpdname"], w["CONCuM"])
        if key not in lookup:
            raise PLAIDError(f"Solver returned an unknown entity {key}; the layout cannot be mapped back.")
        name, conc, role = lookup[key]
        well = w["well"].strip()
        letters = "".join(ch for ch in well if ch.isalpha()).upper()  # PLAID writes row 27 as "Aa"
        number = int("".join(ch for ch in well if ch.isdigit()))
        out.append({
            "plateID": w["plateID"], "well": f"{letters}{number:02d}", "cmpdname": name,
            "CONCuM": fmt_conc(conc), "cmpdnum": f"{name}_{fmt_conc(conc)}", "role": role,
        })
    out.sort(key=lambda r: (int(r["plateID"].split("_")[-1]), well_sort_key(r["well"])))
    return out


def write_outputs(rows: list[dict], spec: dict, out: Path, name: str, solve_info: dict) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        "layout": out / f"{name}_layout.csv",
        "platemap": out / f"{name}_platemap.csv",
        "figure": out / f"{name}_layout.png",
        "design": out / f"{name}_design.json",
        "check": out / f"{name}_check.txt",
    }
    with paths["layout"].open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["plateID", "well", "cmpdname", "CONCuM", "cmpdnum", "role"])
        writer.writeheader()
        writer.writerows(rows)

    n_rows, n_cols = spec["plate_rows"], spec["plate_cols"]
    row_labels = [chr(65 + i) if i < 26 else "A" + chr(65 + i - 26) for i in range(n_rows)]
    by_plate: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in rows:
        by_plate[r["plateID"]][r["well"]] = r
    with paths["platemap"].open("w", newline="") as fh:
        writer = csv.writer(fh)
        for plate in sorted(by_plate, key=lambda p: int(p.split("_")[-1])):
            writer.writerow([plate] + [str(c) for c in range(1, n_cols + 1)])
            for ri, lab in enumerate(row_labels):
                cells = []
                for c in range(1, n_cols + 1):
                    r = by_plate[plate].get(f"{lab}{c:02d}")
                    cells.append("" if r is None else (r["cmpdname"] if r["role"] == "solvent" else f"{r['cmpdname']} @ {r['CONCuM']}"))
                writer.writerow([lab] + cells)
            writer.writerow([])

    public = {k: v for k, v in spec.items() if k != "items"}
    public["compounds"] = [_item_json(i) for i in spec["items"] if i["role"] == "compound"]
    public["controls"] = [_item_json(i) for i in spec["items"] if i["role"] == "control"]
    public["solvents"] = [{"name": i["name"], "replicates": i["entries"][0][1]} for i in spec["items"] if i["role"] == "solvent"]
    paths["design"].write_text(json.dumps({"spec": public, "solve": solve_info}, indent=2))
    return paths


def _item_json(item):
    concs = [c for c, _ in item["entries"]]
    reps = [r for _, r in item["entries"]]
    return {"name": item["name"], "concentrations_uM": concs, "replicates": reps[0] if len(set(reps)) == 1 else reps}


def solve(spec, compounds, controls) -> tuple[object, dict]:
    designer = PlateDesigner()
    seed = int(spec["seed"])
    last_error = None
    for attempt in range(int(spec["attempts"])):
        cfg = PlateConfig(
            plate_rows=spec["plate_rows"], plate_cols=spec["plate_cols"], empty_edge=int(spec["empty_edge"]),
            compounds=compounds, controls=controls,
            concentrations_on_different_rows=bool(spec["concentrations_on_different_rows"]),
            concentrations_on_different_columns=bool(spec["concentrations_on_different_columns"]),
            replicates_on_same_plate=not spec["replicates_on_different_plates"],
            replicates_on_different_plates=bool(spec["replicates_on_different_plates"]),
            allow_empty_wells=bool(spec["allow_empty_wells"]),
            timeout_seconds=int(spec["timeout_seconds"]), num_threads=int(spec["threads"]),
            random_seed=seed + attempt,
        )
        t0 = time.time()
        print(f"[solve] attempt {attempt + 1}/{spec['attempts']}: seed={seed + attempt}, "
              f"timeout={spec['timeout_seconds']}s, threads={spec['threads']} ...", flush=True)
        try:
            layout = designer.design(cfg)
            info = {"seed": seed + attempt, "attempt": attempt + 1, "seconds": round(time.time() - t0, 1),
                    "plates": layout.num_plates, "wells": len(layout.wells)}
            print(f"[solve] solved in {info['seconds']} s", flush=True)
            return layout, info
        except NoSolutionFoundError as exc:
            last_error = exc
            print(f"[solve] no layout after {time.time() - t0:.0f} s: {exc}", flush=True)
            if "UNSATISFIABLE" in str(exc) or "No valid plate layout exists" in str(exc):
                break  # proven impossible; another seed will not help
    raise last_error


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path, help="design spec .json or PLAID feeder .csv")
    ap.add_argument("--out", type=Path, default=Path("plate_layout"), help="output directory")
    ap.add_argument("--name", default=None, help="file prefix (default: input file stem)")
    ap.add_argument("--plate-format", type=int, choices=sorted(PLATE_FORMATS))
    ap.add_argument("--empty-edge", type=int)
    ap.add_argument("--timeout", type=int, dest="timeout_seconds", help="seconds per attempt")
    ap.add_argument("--threads", type=int)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--attempts", type=int, help="retry with seed+1, seed+2 ... after a timeout")
    ap.add_argument("--dry-run", action="store_true", help="preflight only; do not call the solver")
    args = ap.parse_args(argv)

    overrides = {k: getattr(args, k) for k in ("plate_format", "empty_edge", "timeout_seconds", "threads", "seed", "attempts")}
    try:
        spec = normalise(load_spec(args.input), overrides)
        compounds, controls, lookup = build_plaid_groups(spec)
    except (SpecError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    errors, warnings, summary = preflight(spec, compounds, controls)
    print("[preflight] " + ", ".join(f"{k}={v}" for k, v in summary.items()))
    for w in warnings:
        print(f"[preflight] WARNING: {w}")
    for e in errors:
        print(f"[preflight] ERROR: {e}", file=sys.stderr)
    if errors:
        return 1
    if args.dry_run:
        print("[preflight] OK (dry run, solver not called)")
        return 0
    if not validate_minizinc_available():
        print("ERROR: MiniZinc not found. Install it (macOS: `brew install minizinc`; Linux: MiniZinc bundle from "
              "https://www.minizinc.org/downloads/) or set MINIZINC_PATH to the minizinc binary.", file=sys.stderr)
        return 1

    try:
        layout, info = solve(spec, compounds, controls)
    except NoSolutionFoundError as exc:
        print(f"ERROR: no layout found. {exc}\nSee references/solver_troubleshooting.md for what to change.", file=sys.stderr)
        return 2
    except (SolverError, PLAIDError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    rows = layout_rows(layout, lookup)
    name = args.name or args.input.stem
    paths = write_outputs(rows, spec, args.out, name, info)

    from check_layout import run_checks, format_report  # local module
    results = run_checks(paths["layout"], paths["design"])
    report = format_report(results)
    paths["check"].write_text(report + "\n")
    print(report)

    try:
        from plot_layout import plot_layout
        plot_layout(paths["layout"], paths["figure"], plate_rows=spec["plate_rows"], plate_cols=spec["plate_cols"],
                    empty_edge=int(spec["empty_edge"]))
    except Exception as exc:  # plotting must never hide a valid layout
        print(f"WARNING: could not draw the plate map: {exc}", file=sys.stderr)

    for key, path in paths.items():
        if path.exists():
            print(f"[out] {key}: {path}")
    return 0 if all(r["status"] != "FAIL" for r in results) else 3


if __name__ == "__main__":
    raise SystemExit(main())
