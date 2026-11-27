## Prompt

A colleague made this 96-well layout by hand (t3_layout.csv). The design was 4 drugs (etoposide, cisplatin, olaparib, niraparib) at 0.1, 1, 10 µM in triplicate, staurosporine 1 µM x4, DMSO x8, outer ring empty. Is it OK to use?

## A good answer

- Runs `check_layout.py` with a spec written from the description (or `--plate-format 96 --empty-edge 1`).
- Finds all three planted problems: a sample in edge well A05, two samples in the same well (B10), and DMSO in 7 wells instead of 8; also that Olaparib's wells can no longer be split into replicate series on distinct rows and columns (a side effect of the moved well).
- Says the layout should not be used as is and offers to generate a PLAID layout instead; does not silently "fix" wells by hand.
