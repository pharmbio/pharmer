## Prompt

I'm running a viability assay in a 96-well plate. Four drugs (etoposide, cisplatin, olaparib, niraparib), each at 0.1, 1 and 10 µM in triplicate. Staurosporine 1 µM as positive control (4 wells) and DMSO vehicle (8 wells). Keep the outer wells empty. Can you design the plate layout?

## A good answer

- Loads the skill and uses PLAID (`scripts/design_layout.py`), not a hand-made or `random.shuffle` layout.
- 96-well, `empty_edge: 1`; 48 filled wells out of 60 usable, 12 inner wells empty.
- Each drug x concentration appears exactly 3 times; Staurosporine 4, DMSO 8 (`CONCuM = 0`).
- `check_layout.py` report has no FAIL; the agent looked at the PNG.
- Delivers layout CSV, plate-map CSV, figure and design JSON with the seed; says plateID must be mapped to a barcode.
