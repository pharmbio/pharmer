# plate-layout-design

An agent skill that designs microplate layouts with PLAID, the constraint-programming layout engine behind iPLAID's
*Design with PLAID*. You describe the compounds, concentrations, replicates and controls; the agent returns a
well-by-well layout where dose series are spread over different rows and columns, controls are balanced across the
plate, and the edge wells stay empty. It can also check a layout someone made by hand.

| | |
|---|---|
| Skill folder | [`skills/plate-layout-design/`](../../skills/plate-layout-design/) |
| Test tasks | [`evals/plate-layout-design/`](../../evals/plate-layout-design/) |
| Needs | Python 3 with pandas and matplotlib; MiniZinc with the Gecode solver |
| Owner | _to be filled in_ |

## What the skill does

1. Turns the request (free text, a compound table, or an iPLAID feeder CSV) into a design spec.
2. Runs a preflight that mirrors the solver's own feasibility rules, so impossible designs fail fast with a fix
   (for example "usable area must have an even number of rows", "too many wells of a single control type").
3. Solves the layout with the bundled PLAID MiniZinc model (unchanged from upstream).
4. Checks the result independently: wells exist and are unique, edge ring empty, exact replicate counts,
   no dose series stacked in one row/column, controls balanced over halves and quadrants.
5. Delivers an iPLAID-compatible layout CSV, a spreadsheet plate map, a plate-map figure, and a design JSON
   that reproduces the layout (spec + seed).

Only the design engine was kept from iPLAID (`src/plaid_core/`). The web UI, backend, and the dispense-protocol pipeline
(iDOT/Echo files, source-plate prep) are not part of this skill. The layout CSV can still be loaded into iPLAID for that.

## Installing

Follow [Installing and using skills](../installing-and-using-skills.md), then:

```bash
pip install -r skills/plate-layout-design/requirements.txt
brew install minizinc                     # macOS; on Linux use the bundle from minizinc.org (includes Gecode)
minizinc --solvers | grep -i gecode       # should print a Gecode line
```

## Example prompts

- "Design a 96-well layout: 4 drugs at 0.1, 1, 10 µM in triplicate, staurosporine 1 µM x4, DMSO x8, outer wells empty."
- "Here's our PLAID feeder CSV, make the 384-well layout for iPLAID."
- "8-point dose response for 6 compounds in duplicate on 384, with 16 DMSO and 8 positive control wells."
- "Can you check whether this hand-made plate layout is OK?"

## Trying it out

Each folder in `evals/plate-layout-design/` holds a prompt and what a good answer must get right. Run each prompt in
a fresh session with and without the skill. Without it, agents tend to shuffle wells at random or fill row by row,
with no guarantee that a dose series isn't stacked in one row or that controls aren't clustered.

## Limitations

- Solve time grows quickly with the number of control/vehicle wells; designs with many controls may need several
  minutes or a reduced control count. See `references/solver_troubleshooting.md` in the skill.
- At most 3 plates per solve; larger screens are split into batches.
- No combination wells and no multi-cell-line plates.
- `plateID` is logical (`plate_1`); map to physical barcodes before dispensing.

PLAID: Francisco Rodríguez, Carreras Puigvert & Spjuth, *Designing microplate layouts using artificial intelligence*,
AI in the Life Sciences 3, 100073 (2023). Apache-2.0.
