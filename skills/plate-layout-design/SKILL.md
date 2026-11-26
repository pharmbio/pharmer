---
name: plate-layout-design
description: "Designs microplate layouts (96, 384 or 1536-well) for compound screens, dose-response and Cell Painting assays with the PLAID constraint solver from iPLAID. Places compounds, concentrations, replicates, positive/negative controls and DMSO/vehicle wells so dose series spread over different rows and columns, controls are balanced across the plate, and edge wells stay empty. Writes an iPLAID-compatible layout CSV, a plate-map grid and figure, and checks the result. Use when the user asks for a plate layout, plate map, well assignment, a randomized or balanced plate design, where to put controls, or mentions PLAID or iPLAID; also to check an existing layout CSV."
---

# Plate layout design (PLAID / iPLAID)

Turns "these compounds, these concentrations, this many replicates and controls"
into a well-by-well layout using PLAID, the MiniZinc constraint model behind
iPLAID's *Design with PLAID*. A good result has every replicate count exact, the
edge ring empty, no dose series stacked in one row or column, controls spread over
the whole plate, a figure the user can eyeball, and a check report with no FAIL.

All commands run from this skill's folder. `scripts/plaid_core/` is the solver
wrapper; do not rewrite it, call `scripts/design_layout.py`.

## Setup (once per machine)

```bash
pip install -r requirements.txt          # pandas, matplotlib
minizinc --solvers | grep -i gecode      # must print a Gecode line
```

No MiniZinc: macOS `brew install minizinc` (brings Gecode); Linux: the MiniZinc
bundle from https://www.minizinc.org/downloads/ (includes Gecode), put `bin/` on
PATH or set `MINIZINC_PATH=/path/to/minizinc`. Ask before installing software on
the user's machine.

## Workflow (follow in order)

### 1. Collect the design

You need, per item: name, concentrations (µM) and replicates. Ask for what is
missing; do not invent compounds or concentrations. Use these defaults when the
user says nothing, and list the ones you used in the final answer:

| Setting | Default |
|---|---|
| Plate | 384-well; 96 if everything (compounds + controls + vehicle) fits in 60 wells and the user hasn't named a format |
| Edge | `empty_edge: 1` (outer ring left for medium/buffer) |
| Vehicle | DMSO solvent wells, about 8% of the compound wells, at least 8 per plate |
| Positive control | only if the user names one; never pick a compound for them |
| Dose series | different rows **and** columns per replicate |
| Replicates | together on one plate (`replicates_on_different_plates: false`) |

If the user has a list of compounds in a file (CSV/Excel with names, doses,
replicates), convert it to the spec; if it is already an iPLAID feeder CSV
(`compound_name,concentration_uM,replicate_number,role`), pass it straight in.

### 2. Write the spec

Write the spec as `<experiment>.json` (e.g. `viability_96.json`) in the user's
working or data folder; output files are prefixed with its name. Format and every
option: `references/spec_format.md`.

```json
{
  "plate_format": 384,
  "empty_edge": 1,
  "compounds": [{"name": "Etoposide", "concentrations_uM": [0.1, 1, 10], "replicates": 3}],
  "controls":  [{"name": "Staurosporine", "concentrations_uM": [1], "replicates": 16}],
  "solvents":  [{"name": "DMSO", "replicates": 24}]
}
```

Compounds are dose series (spread over rows/columns); controls are balanced
over the plate; solvents are vehicle-only wells (`CONCuM = 0`).

### 3. Preflight

```bash
python scripts/design_layout.py <experiment>.json --dry-run
```

Prints usable wells, plates needed, fill % and any ERROR. Every ERROR says what
to change. Fix the spec only in ways the user agreed to; if a fix changes the
science (fewer replicates, fewer controls, another plate format), ask first.

Check the plate count: PLAID uses `ceil(wells / usable wells)` plates, and the
script refuses more than 3. For larger screens, split the compounds into batches
of ≤ 3 plates, one spec each, and give every batch the same controls.

When the design needs more than one plate, tell the user before solving: with
the default (`replicates_on_different_plates: false`) every replicate of a
compound lands on the same plate, so plate effects are confounded with compound.
The alternative, `true`, puts each replicate on a different plate and needs at
least as many plates as replicates. A larger plate format avoids the question.

### 4. Solve

```bash
python scripts/design_layout.py <experiment>.json --out <out_dir>
```

PLAID's search is randomised and its run time is heavy-tailed, so the script
races 4 seeds (one CPU each) and keeps the first layout; if none finishes in
120 s it starts a new round with fresh seeds (3 rounds, so at most ~6 min).
Typical times: small 96-well designs < 5 s; a single 384 plate with ≤ ~36 wells
per control type seconds to ~1 min; a completely full 384 plate ~1.5 min.
Always pass `--out` (a folder in the user's project, never inside this skill).
Run it in the background when you expect more than a minute. It prints
`[solve] seed N solved in X s`, then the check report and the output paths.

What makes PLAID slow, from testing: one control type with more than ~36 wells
on a plate, some specific control-count combinations (40 + 16 never solved,
36 + 20 solved in 4 s), multi-plate designs above ~85% fill, and large 1536-well
designs (144 wells solved in 5 s; 432 wells timed out). The preflight warns
about the first three.

Exit code 2 = no layout found. Do not loosen constraints on your own. Read
`references/solver_troubleshooting.md`, pick the least invasive change, and
ask the user before changing replicate or control counts. Show them what you
measured ("36 DMSO + 20 staurosporine solves; 40 + 16 does not").

### 5. Check

`design_layout.py` runs the checker and writes `<name>_check.txt` (exit code 3
means a layout was written but a check failed). To re-check:

```bash
python scripts/check_layout.py <out_dir>/<name>_layout.csv --spec <out_dir>/<name>_design.json
```

- Any **FAIL** → the layout is not deliverable. Re-run with another `--seed`; if
  it repeats, report it as a bug with the check output. Never edit wells by hand
  to make a check pass.
- **WARN** on control balance → tell the user which control is lopsided; try one
  more seed before delivering.
- Open `<name>_layout.png` and look at it: edge ring empty, controls scattered
  over all four quadrants, no band of dark (high-dose) wells in one region.

**Checking a layout the user brought** (hand-made, from another tool): write a
spec from the design they describe and pass it with `--spec`, so counts and
dose spreading are checked too; without a design, `--plate-format 384
--empty-edge 1` checks structure only. The dose-series check finds whether the
wells can be grouped into replicate series with distinct rows/columns, which
the CSV does not record. Report each FAIL in plain words and recommend a PLAID
layout instead; do not repair their file well by well unless they ask.

### 6. Deliver

Give the user:
- `<name>_layout.csv` (the layout; iPLAID-compatible), `<name>_platemap.csv`
  (spreadsheet grid), `<name>_layout.png`, `<name>_design.json` (reproduces the
  layout: same spec + seed);
- a short summary: plates, filled wells per plate, empty wells, the defaults you
  chose, the seed, and the check result;
- the reminders below.

## Rules

- Never hand-edit or hand-make a layout and present it as a PLAID design. Every
  delivered layout comes from `design_layout.py` and passes `check_layout.py`.
- Keep names exactly as the user wrote them (iPLAID matches the metadata by
  exact name). Commas and double quotes are not allowed in names; ask for a
  replacement name rather than silently altering it.
- `plateID` values are logical (`plate_1`, ...). Tell the user to map them to
  physical barcodes before dispensing.
- The layout only says what goes where. Stock concentrations, DMSO %, transfer
  volumes and dispenser files are out of scope; for iPLAID the user also needs a
  metadata CSV (`cmpdname,highest_stock_mM,solvent`, including a `DMSO,0,DMSO`
  row per solvent).
- Cite PLAID when the layout goes into a paper: Francisco Rodríguez M.A.,
  Carreras Puigvert J., Spjuth O. *Designing microplate layouts using artificial
  intelligence.* AI in the Life Sciences 3, 100073 (2023).
  doi:10.1016/j.ailsci.2023.100073

## Helpers

| File | What it does |
|---|---|
| `scripts/design_layout.py` | Spec/feeder → preflight → PLAID solve → layout CSV, plate map, figure, design JSON, check. `--help` for flags. |
| `scripts/check_layout.py` | Checks any layout CSV: wells, duplicates, empty edge, replicate counts, dose spreading, control balance. |
| `scripts/plot_layout.py` | Plate-map figure (identity + concentration panels) from a layout CSV. |
| `scripts/plaid_core/` | PLAID solver wrapper + MiniZinc model (Apache-2.0, from pharmbio/plaid via iPLAID). Read only. |
| `references/spec_format.md` | Spec fields, defaults, feeder CSV, output columns, what PLAID guarantees. |
| `references/solver_troubleshooting.md` | What to do when the solver times out or reports the design impossible. |

## Known limits

- One cell line per plate (PLAID's cell-line split is not supported here).
- Concentrations are per well; no combination (drug A + drug B) wells.
- Max 3 plates per solve; split larger screens into batches.
- Solve time depends on control counts and multi-plate fill (step 4); some
  designs need nearby counts to solve at all.
