# Design spec and output formats

Contents
- [Spec JSON](#spec-json)
- [Field reference](#field-reference)
- [PLAID feeder CSV](#plaid-feeder-csv-alternative-input)
- [Outputs](#outputs)
- [What PLAID guarantees](#what-plaid-guarantees)
- [Using the layout in iPLAID](#using-the-layout-in-iplaid)

## Spec JSON

```json
{
  "plate_format": 384,
  "empty_edge": 1,
  "compounds": [
    {"name": "Etoposide", "concentrations_uM": [0.1, 1, 10], "replicates": 3},
    {"name": "Olaparib",  "concentrations_uM": [0.3, 3, 30], "replicates": [3, 3, 6]}
  ],
  "controls": [
    {"name": "Staurosporine", "concentrations_uM": [1], "replicates": 16}
  ],
  "solvents": [
    {"name": "DMSO", "replicates": 24}
  ],
  "concentrations_on_different_rows": true,
  "concentrations_on_different_columns": true,
  "replicates_on_different_plates": false,
  "allow_empty_wells": true,
  "timeout_seconds": 300,
  "threads": 8,
  "seed": 1,
  "attempts": 1
}
```

Only `compounds`, `controls` or `solvents` (at least one of them) are required.
Everything else has the default shown above.

## Field reference

| Field | Meaning | Default |
|---|---|---|
| `plate_format` | 6, 12, 24, 48, 96, 384 or 1536. Or give `plate_rows` + `plate_cols` instead. | 384 |
| `empty_edge` | Rows/columns left empty on every side (evaporation / edge effect). The usable area must have an even number of rows and columns. | 1 |
| `compounds[]` | Test items. `concentrations_uM`: list of µM values > 0. `replicates`: one int, or one int per concentration. | — |
| `controls[]` | Positive/negative/reference controls with a concentration. Same fields as compounds. PLAID balances controls across the plate (rows, columns, halves, quadrants) instead of spreading them as a dose series. | — |
| `solvents[]` | Vehicle-only wells (DMSO, water, ...). `replicates` only; written with `CONCuM = 0`. | — |
| `concentrations_on_different_rows` | Each replicate of a compound's dose series uses a different row for every concentration. | true |
| `concentrations_on_different_columns` | Same for columns. | true |
| `replicates_on_different_plates` | Put each replicate series on a different plate (needs at least as many plates as replicates). When false, all concentrations of one replicate series stay on one plate. | false |
| `allow_empty_wells` | Allow unused wells inside the usable area. If false, the sample count must fill whole plates exactly. | true |
| `timeout_seconds` | Solver time limit per attempt. | 300 |
| `threads` | Gecode threads (capped to the CPU count). | 8 |
| `seed` | Random seed; same spec + same seed reproduces the layout. | 1 |
| `attempts` | After a timeout, retry with `seed+1`, `seed+2`, ... | 1 |

Names: no commas or double quotes. A name may appear in only one of the three
lists (case-insensitive). Concentrations within one compound must be distinct.

**Different replicate counts per concentration** (`"replicates": [3, 3, 6]`):
PLAID needs one replicate count per compound, so the script splits the compound
into one PLAID entity per replicate count. The row/column spreading then holds
within each group, not across groups. Say so to the user if they rely on it.

**Number of plates** is not an input. PLAID uses the fewest plates that hold all
wells: `ceil(total wells / usable wells per plate)`. Usable wells per plate:

| Format | empty_edge=0 | empty_edge=1 | empty_edge=2 |
|---|---|---|---|
| 96 (8x12) | 96 | 60 (6x10) | 32 (4x8) |
| 384 (16x24) | 384 | 308 (14x22) | 240 (12x20) |
| 1536 (32x48) | 1536 | 1380 (30x46) | 1232 (28x44) |

## PLAID feeder CSV (alternative input)

The iPLAID "Design with PLAID" input. One row per (compound, concentration):

```csv
compound_name,concentration_uM,replicate_number,role
Cisplatin,0.1,7,treatment
Cisplatin,1.0,7,treatment
Staurosporine,1,8,control
DMSO,0,14,solvent
```

`role`: `treatment` (= compound), `control`, or `solvent`. Missing `role` means
treatment. Plate format, edge and solver options come from the command-line flags
(`--plate-format`, `--empty-edge`, `--timeout`, `--attempts`, ...); constraint
flags keep their defaults. For non-default constraints, write a spec JSON.

## Outputs

`<name>_layout.csv`, one row per filled well, sorted by plate then well:

| Column | Example | Meaning |
|---|---|---|
| `plateID` | `plate_1` | Logical plate. Replace with real barcodes before dispensing. |
| `well` | `B02` | Zero-padded well. |
| `cmpdname` | `Etoposide` | Name exactly as in the spec. |
| `CONCuM` | `0.1` | Final concentration in µM; `0` for solvents. |
| `cmpdnum` | `Etoposide_0.1` | Condition label (name_conc). |
| `role` | `compound` | `compound`, `control` or `solvent`. |

Wells not listed are empty (edge wells and any spare inner wells).

`<name>_platemap.csv`: a grid per plate (row letters x column numbers), cell text
`name @ conc`, for people who want to read the layout in a spreadsheet.

`<name>_layout.png`: per plate, an identity panel (codes C1.., K1.., S with legend)
and a concentration panel (log µM, one-hue scale; solvent wells hollow).

`<name>_design.json`: the resolved spec plus `solve` = {seed, attempt, seconds,
plates, wells}. Re-running `design_layout.py` on this spec with that seed reproduces
the layout; `check_layout.py --spec` also reads it.

## What PLAID guarantees

The MiniZinc model (`scripts/plaid_core/templates/plate-design.mzn`, from
pharmbio/plaid, Francisco Rodríguez et al. 2023) enforces:

- exact replicate counts for every compound/concentration and control;
- the outer `empty_edge` ring stays empty;
- each replicate dose series uses distinct rows and/or columns (flags above), and
  its concentrations are split evenly between the top/bottom and left/right halves;
- controls are spread evenly over rows, columns, plate halves and quadrants, and
  across plates when there are several;
- compounds are shared evenly between plates;
- placement is randomised within those rules (seeded).

It does **not** know about dispensing, stock concentrations, solvent limits or
cell seeding. Those belong to the downstream protocol.

## Using the layout in iPLAID

The layout CSV loads directly in the iPLAID workbench (upload layout CSV) or
its pipeline. iPLAID also needs a metadata CSV `cmpdname,highest_stock_mM,solvent`
with one row per compound **and** one row per solvent (`DMSO,0,DMSO`). Names must
match `cmpdname` exactly.
