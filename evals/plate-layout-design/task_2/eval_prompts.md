## Prompt

Here is our PLAID feeder file for the DNA-damage panel (t2_feeder.csv). Please make the 384-well layout, edge wells empty, so I can load it into iPLAID.

## A good answer

- Passes the feeder CSV straight to `design_layout.py` (no manual re-typing of 42 rows).
- Notices from the preflight that the design fills all 308 usable wells exactly (14 compounds x 3 doses x 7 + 14 DMSO) and runs the solve in the background with a long timeout (it takes about 1-2 min).
- All checks PASS; DMSO wells spread over all quadrants.
- Output layout CSV has `plateID,well,cmpdname,CONCuM` and names exactly as in the feeder.
- Mentions that iPLAID also needs a metadata CSV with a `DMSO,0,DMSO` row.
