## Prompt

I'm tidying up our screening library sheet (t1_compounds.csv). For each compound, add the PubChem CID, InChIKey,
molecular formula, ChEMBL ID and highest clinical phase. Give me the table back as a CSV.

## A good answer

Values checked on 2026-11-27. IDs are stable; re-check `max_phase` if the test is run much later.

| compound_name | PubChem CID | InChIKey | Formula | ChEMBL ID | max_phase |
|---|---|---|---|---|---|
| aspirin | 2244 | BSYNRYMUTXBXSQ-UHFFFAOYSA-N | C9H8O4 | CHEMBL25 | 4 |
| Imatinib mesylate | 123596 | YLMAHDNUQAMNNX-UHFFFAOYSA-N | C30H35N7O4S | CHEMBL1642 (parent CHEMBL941) | 4 |
| esomeprazole | 9568614 | SUBDBMMJDZJVOS-DEOSSOPVSA-N | C17H19N3O3S | CHEMBL1201320 | 4 |
| omeprazole | 4594 | SUBDBMMJDZJVOS-UHFFFAOYSA-N | C17H19N3O3S | CHEMBL1503 | 4 |
| dexamethasone | 5743 | UREBDLICKHMUKA-CXSFZGCWSA-N | C22H29FO5 | CHEMBL384467 | 4 |
| zorbanatinib | not found | — | — | — | — |

- Loads the skill and uses PubChem for identity and ChEMBL for the ChEMBL ID and phase, mapping between
  them by InChIKey rather than by name.
- **Salt form kept**: imatinib mesylate stays the mesylate salt (CID 123596, CHEMBL1642). It is not silently
  replaced by the free base (CID 5291, CHEMBL941); the parent is named alongside.
- **Stereochemistry kept**: esomeprazole and omeprazole get different CIDs and ChEMBL IDs. The answer notes that
  they share a formula and the first InChIKey block and differ only in the stereo layer.
- **Not found is a result**: zorbanatinib is reported as not found in PubChem, with what was tried (name lookup,
  then a search or synonym check). No ID is invented for it.
- Provenance section: databases, request URLs, access date, identifier conversions.
- Without the skill, agents often fill in IDs from memory, merge the salt with its parent, or give the
  zorbanatinib row a plausible-looking CID.
