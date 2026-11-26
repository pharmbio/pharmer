# When the solver does not return a layout

`design_layout.py` exits with code 2 and prints one of three causes. Find yours,
then work down its list. Changes marked **ask** alter the experiment: propose them
to the user with the numbers, do not apply them silently.

## How PLAID behaves (measured)

Search is randomised and solve time is heavy-tailed: the same design can finish in
seconds with one seed and run for minutes with another. Seed racing (several
single-thread runs with different seeds, first one wins) is on by default
(`parallel: 4`, `attempts: 3`).

Single 384-well plate, 10 compounds x 6 doses x 3 replicates (180 wells) plus the
controls below; one Gecode thread per run, 90–180 s limit:

| Solved in seconds | Slow or timed out |
|---|---|
| 48 DMSO alone (3 s) | 56 DMSO alone, 72 DMSO alone |
| 32 DMSO + 32 positive (3 s) | 40 DMSO + 40 positive |
| 28 + 28 (4 s), 36 + 20 (4 s) | 40 + 16 (12 seeds x 120 s, none solved) |
| 16 + 16 (13 s) | 42 + 14, 44 + 12, 40 + 8 |
| 24 + 16 (17–48 s, seed-dependent) | 32 + 16 (seed 1 > 180 s; seeds 2, 3: 50 s, 85 s) |

Other designs:

| Design | Result |
|---|---|
| Full 384 plate: 14 compounds x 3 doses x 7 reps + 14 DMSO (308/308) | 81 s |
| 96-well, 2 plates at 75% fill | 13 s |
| 96-well, 2 plates at 95% fill | timed out (3 rounds); same wells on one 384 plate: 6 s |
| 1536-well, 10 compounds x 4 doses x 2 + 32 controls (144 wells) | 5 s |
| 1536-well, 20 compounds x 8 doses x 2 + 56 controls (432 wells) | timed out (2 seeds x 240 s) |

Lessons: difficulty depends on the exact control counts more than on their total;
moving a control count by a few wells (40 + 16 → 36 + 20) can turn a timeout into
a 4 s solve. Single plates tolerate high fill; multi-plate designs do not.

## "TIMEOUT: no layout within N round(s)"

The solver did not prove anything; another try may work.

1. Rerun with fresh seeds: `--seed 101 --attempts 5`; with spare cores add
   `--parallel 8`. Raising `--timeout` helps less than more seeds.
2. **ask** — Shift control counts by a few wells. Probe candidates quickly
   (`--timeout 60 --attempts 1 --out <scratch dir>` on a copy of the spec, one
   variant per run) and
   offer the user the closest one that solves, e.g. "36 DMSO + 20 positive solves
   in 4 s; 40 + 16 does not".
3. **ask** — Multi-plate and > 85% full: use the next plate format up (two 96s →
   one 384), or split the compounds into separate designs.
4. **ask** — Fewer control wells of one kind (keep a single control ≤ ~36 per
   384 plate).
5. **ask** — `concentrations_on_different_columns: false` (keeps the rows rule).
   It did not rescue 60 DMSO + 16 positive in testing, so try it last, and tell
   the user the design is weaker.

Never drop the dose-spread or control-balance requirements without the user's
OK; that is the reason to use PLAID instead of a random shuffle.

## "UNSATISFIABLE: no layout exists"

Proven impossible; more time or seeds will not help. Usual causes:

- Replicates or concentrations do not fit the rows/columns spread, e.g. more
  concentrations than usable rows with `concentrations_on_different_rows`.
- `allow_empty_wells: false` with a count that cannot be balanced.
- `replicates_on_different_plates` with replicate counts not matching plates.
- Multi-plate designs whose replicate series cannot be shared evenly between the
  plates (seen: 7 compounds x 3 replicates on two 96-well plates; 6 or 8
  compounds solve).

Fix the input (**ask**), rerun `--dry-run`, then solve.

## "MiniZinc failed: ... assertion failed: ..."

The model rejected the data before searching. The message names the problem:

| Message contains | Meaning | Fix |
|---|---|---|
| `even number of rows` / `columns` | Usable area has odd rows/cols | Change `empty_edge` or plate format |
| `(E01)` / `(E02)` | Compounds/controls cannot be split evenly across plates | Change replicate counts so wells fill plates more evenly (**ask**) |
| `too many controls of only one kind` | One control type with > usable/4 wells | Add a second control type or reduce it (**ask**) |
| `empty wells` | `allow_empty_wells: false` but wells would stay empty | Allow empty wells or add wells (**ask**) |

The preflight already catches most of these; if one gets through, the spec
changed after `--dry-run`. Run it again.

## "MiniZinc not found"

Install it (SKILL.md, Setup) or set `MINIZINC_PATH`. Check with
`minizinc --solvers | grep -i gecode`; PLAID needs Gecode.
