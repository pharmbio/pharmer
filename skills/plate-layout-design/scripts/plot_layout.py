#!/usr/bin/env python3
"""Draw a plate map from a layout CSV (plateID,well,cmpdname,CONCuM[,role]).

    python scripts/plot_layout.py results/x_layout.csv results/x_layout.png --plate-format 384 --empty-edge 1

Two panels per plate:
  * Identity: every well is labelled with a short code (legend maps codes to names).
    Controls and solvents get a fixed colour each; compounds get a colour only when
    there are 8 or fewer entities in total, otherwise a neutral fill + the code.
  * Concentration: one-hue sequential scale on log10(µM); solvent wells hollow.
    Use it to spot dose levels piling up in one region of the plate.
"""
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, LogNorm  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

PLATE_FORMATS = {6: (2, 3), 12: (3, 4), 24: (4, 6), 48: (6, 8), 96: (8, 12), 384: (16, 24), 1536: (32, 48)}
CATEGORICAL = ["#257de0", "#f47230", "#00b894", "#f2a600", "#ee7fac", "#008a17", "#6a4ce2", "#ec4647"]
SEQ = LinearSegmentedColormap.from_list("blue_seq", ["#cce3fd", "#84b9f3", "#338ced", "#2370cd", "#1757ac", "#0e3d7e"])
NEUTRAL = "#d9d9d9"
TEXT = "#1f1f1f"
MUTED = "#8a8a8a"
WELL_RE = re.compile(r"^([A-Za-z]+)0*(\d+)$")


def _rc(well):
    m = WELL_RE.match(str(well).strip())
    row = 0
    for ch in m.group(1).upper():
        row = row * 26 + (ord(ch) - 64)
    return row, int(m.group(2))


def _ink(hex_color):
    """Black or white text, whichever reads better on the fill."""
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return TEXT if lum > 0.45 else "white"


def _row_label(i):
    return chr(64 + i) if i <= 26 else "A" + chr(64 + i - 26)


def plot_layout(layout_csv, out_png, plate_rows=16, plate_cols=24, empty_edge=1):
    df = pd.read_csv(layout_csv, dtype={"plateID": str, "well": str, "cmpdname": str})
    df["conc"] = pd.to_numeric(df["CONCuM"], errors="coerce").fillna(0)
    if "role" not in df.columns:
        df["role"] = np.where(df["conc"] > 0, "compound", "solvent")
    df[["row", "col"]] = df["well"].apply(lambda w: pd.Series(_rc(w)))

    order = {"solvent": 0, "control": 1, "compound": 2}
    ents = (df[["cmpdname", "role"]].drop_duplicates()
            .assign(o=lambda d: d["role"].map(order)).sort_values(["o", "cmpdname"], kind="stable"))
    names = ents["cmpdname"].tolist()
    roles = dict(zip(ents["cmpdname"], ents["role"]))
    color_all = len(names) <= len(CATEGORICAL)
    colors, codes = {}, {}
    slot, ci, ki, si = 0, 0, 0, 0
    for n in names:
        r = roles[n]
        if r == "compound":
            ci += 1
            codes[n] = f"C{ci}"
        elif r == "control":
            ki += 1
            codes[n] = f"K{ki}"
        else:
            si += 1
            codes[n] = f"S{si}" if si > 1 else "S"
        if color_all or r != "compound":
            colors[n] = CATEGORICAL[slot % len(CATEGORICAL)]
            slot += 1
        else:
            colors[n] = NEUTRAL

    plates = sorted(df["plateID"].unique(), key=lambda p: (len(p), p))
    w = max(6.0, plate_cols * 0.42)
    h = max(3.0, plate_rows * 0.42)
    fig, axes = plt.subplots(len(plates), 2, figsize=(2 * w + 1.5, len(plates) * (h + 1.2) + 1.2), squeeze=False)
    pitch_pt = 72 * min(w / (plate_cols + 0.2), h / (plate_rows + 0.2))  # well pitch in points
    marker = (0.82 * pitch_pt) ** 2
    fsize = 6 if plate_rows * plate_cols >= 384 else 8
    concs = df.loc[df["conc"] > 0, "conc"]
    norm = LogNorm(vmin=concs.min(), vmax=max(concs.max(), concs.min() * 1.0001)) if len(concs) else None

    for pi, plate in enumerate(plates):
        pdf = df[df["plateID"] == plate]
        for k, ax in enumerate(axes[pi]):
            ax.set_xlim(0.4, plate_cols + 0.6)
            ax.set_ylim(plate_rows + 0.6, 0.4)
            ax.set_aspect("equal")
            ax.set_xticks(range(1, plate_cols + 1))
            ax.set_xticklabels([str(c) for c in range(1, plate_cols + 1)], fontsize=fsize, color=MUTED)
            ax.set_yticks(range(1, plate_rows + 1))
            ax.set_yticklabels([_row_label(r) for r in range(1, plate_rows + 1)], fontsize=fsize, color=MUTED)
            ax.tick_params(length=0)
            for s in ax.spines.values():
                s.set_visible(False)
            rr, cc = np.meshgrid(range(1, plate_rows + 1), range(1, plate_cols + 1))
            ax.scatter(cc.ravel(), rr.ravel(), s=marker, facecolor="none", edgecolor="#e6e6e6", linewidth=0.8)
            if empty_edge:
                e = empty_edge
                ax.add_patch(plt.Rectangle((e + 0.5, e + 0.5), plate_cols - 2 * e, plate_rows - 2 * e,
                                           fill=False, edgecolor=MUTED, linewidth=0.8, linestyle="--"))
            if k == 0:
                for _, r in pdf.iterrows():
                    ax.scatter(r["col"], r["row"], s=marker, color=colors[r["cmpdname"]], edgecolor="white", linewidth=0.6)
                    ax.text(r["col"], r["row"], codes[r["cmpdname"]], ha="center", va="center", fontsize=fsize - 1,
                            color=_ink(colors[r["cmpdname"]]))
                ax.set_title(f"{plate} - identity", fontsize=10, loc="left", color=TEXT)
            else:
                sol = pdf[pdf["conc"] <= 0]
                ax.scatter(sol["col"], sol["row"], s=marker, facecolor="white", edgecolor=MUTED, linewidth=1.0)
                for _, r in sol.iterrows():
                    ax.text(r["col"], r["row"], codes[r["cmpdname"]], ha="center", va="center", fontsize=fsize - 1, color=MUTED)
                pos = pdf[pdf["conc"] > 0]
                if norm is not None and len(pos):
                    sc = ax.scatter(pos["col"], pos["row"], s=marker, c=pos["conc"], cmap=SEQ, norm=norm,
                                    edgecolor="white", linewidth=0.6)
                    cb = fig.colorbar(sc, ax=ax, fraction=0.025, pad=0.01)
                    cb.set_label("µM (log scale)", fontsize=8, color=TEXT)
                    cb.ax.tick_params(labelsize=7)
                ax.set_title(f"{plate} - concentration", fontsize=10, loc="left", color=TEXT)

    handles = [Line2D([0], [0], marker="o", linestyle="", markersize=7, markerfacecolor=colors[n],
                      markeredgecolor="white", label=f"{codes[n]} = {n}") for n in names]
    ncol = min(len(handles), 6)
    fig.legend(handles=handles, loc="lower center", ncol=ncol, fontsize=8, frameon=False,
               bbox_to_anchor=(0.5, 0.0))
    nrows_leg = math.ceil(len(handles) / ncol)
    fig.tight_layout(rect=(0, 0.03 + 0.025 * nrows_leg, 1, 1))
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=200, facecolor="white")
    plt.close(fig)
    return out_png


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("layout", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--plate-format", type=int, default=384, choices=sorted(PLATE_FORMATS))
    ap.add_argument("--empty-edge", type=int, default=1)
    a = ap.parse_args(argv)
    rows, cols = PLATE_FORMATS[a.plate_format]
    print(plot_layout(a.layout, a.out, rows, cols, a.empty_edge))


if __name__ == "__main__":
    main()
