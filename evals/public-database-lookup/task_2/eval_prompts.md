## Prompt

For a meta-analysis I need every IC50 that ChEMBL has for gefitinib against human EGFR. Keep only exact values
in nM and save them as a CSV with the assay and source document for each row.

## A good answer

Counts checked on 2026-11-27. ChEMBL releases add records, so later runs may find more; the reconciliation
steps matter more than the exact numbers.

- Resolves gefitinib → `CHEMBL939` and human EGFR → `CHEMBL203` (single protein, *Homo sapiens*), and says so.
- Treats this as an **exhaustive retrieval**: gets the server total before paging (`page_meta.total_count`,
  268 on 2026-11-27), paginates until the count is reached, and keeps a batch log.
- Uses server-side filters for molecule, target and `standard_type=IC50`, and labels the units and relation
  checks as local filters.
- Gives a count reconciliation like:
  `expected 268 / retrieved 268 / after local filters 244 (standard_units == nM: -0; standard_relation == '=': -24) / returned 244`.
- Saves the CSV to a file and reports its path. Columns include at least activity ID, value, units, relation,
  assay ChEMBL ID and document ChEMBL ID. The rows are not pasted into the chat.
- States that the 24 censored values (`<`, `>`) were dropped, not converted.
- Optional but good: checks salt forms with `parent_molecule_chembl_id` (on 2026-11-27 this gave the same 268
  records, all under CHEMBL939).
- Provenance: request URLs (pages summarised), access date, filters, warnings.
- Without the skill, agents tend to stop after the first page (default 20 records), skip the total, or report
  a summary statistic without saying how many records went into it.
