# public-database-lookup

An agent skill for getting facts out of public scientific databases instead of the agent's memory. You ask for
a compound's identifiers, a gene's annotation, a variant's frequency, every IC50 for a drug–target pair or every
trial matching some filters. The agent queries the authoritative database's public API, checks that it got
everything it should have, and reports how the lookup can be repeated. It covers 46 databases across chemistry,
genomics, structures, pathways and clinical data, and it works in any agent that can run Python or `curl`.

| | |
|---|---|
| Skill folder | [`skills/public-database-lookup/`](../../skills/public-database-lookup/) |
| Test tasks | [`evals/public-database-lookup/`](../../evals/public-database-lookup/) |
| Needs | Python 3 with `requests` (or `curl`); network access. No API keys. |
| Owner | _to be filled in_ |

## What the skill does

1. Writes down what is being asked: entity, identifiers, organism, genome build, filters, fields, and whether
   this is a **targeted lookup** (a few records) or an **exhaustive retrieval** (every matching record).
2. Picks the primary database from a table of 46, and reads that database's reference file (endpoints,
   parameters, pagination, known traps) before the first call.
3. Converts identifiers into the form the database accepts (gene symbol → NCBI Gene ID → Ensembl ID or
   UniProt accession; compound name → PubChem CID → ChEMBL ID by InChIKey; rsID → exact allele and build).
4. Labels each filter as server-side, local or ambiguous. For an exhaustive retrieval it gets the total
   count first and asks before going past 10,000 records or 100 API calls, offering the official bulk
   download instead.
5. Retrieves with a small `fetch` helper that paces requests, retries throttled calls once, and logs every
   request.
6. Reconciles counts (expected / retrieved / after each local filter / returned) and goes back to the plan
   if they disagree.
7. Answers with a fixed template: results plus a provenance section (requests, access date, identifier
   conversions, filters, count reconciliation, warnings).

The skill also keeps scientific distinctions that are easy to blur: salt vs. parent compound, stereoisomers,
ClinVar germline vs. somatic classifications, genome vs. exome allele frequencies, and trial status vs. phase
vs. results availability.

### Databases

| Area | Databases |
|---|---|
| Chemistry and drugs | PubChem, ChEMBL, BindingDB, ChEBI, ZINC, KEGG, OpenFDA, DailyMed |
| Genes, proteins, sequences | UniProt, NCBI Gene, NCBI Protein, NCBI Taxonomy, Ensembl, UCSC Genome Browser, ENA, SRA, GEO, RummaGEO, MouseMine |
| Variants | dbSNP, gnomAD, MyVariant.info, ClinVar, GWAS Catalog, ClinPGx (PharmGKB) |
| Regulation and expression | ENCODE, JASPAR, GTEx, Human Protein Atlas, Human Cell Atlas |
| Structures and domains | PDB, AlphaFold DB, EMDB, InterPro |
| Function, pathways, interactions | QuickGO, Gene Ontology, Reactome, STRING |
| Omics datasets | PRIDE, Metabolomics Workbench |
| Disease and clinical | Open Targets, Monarch, HPO, ClinicalTrials.gov, cBioPortal, GDC (TCGA) |

## Installing

Follow [Installing and using skills](../installing-and-using-skills.md), then:

```bash
pip install -r skills/public-database-lookup/requirements.txt
```

Every database works without an account. Two optional environment variables only raise rate limits for bulk
work: `NCBI_API_KEY` (NCBI E-utilities, 3 → 10 requests/s) and `OPENFDA_API_KEY`. The agent reads them from
the environment if they are set and never prints them.

## Example prompts

- "What's the PubChem CID, InChIKey and ChEMBL ID for imatinib mesylate?"
- "Give me every IC50 for gefitinib against human EGFR from ChEMBL as a CSV, exact values in nM only."
- "What is the clinical significance of rs334 and how common is it?"
- "List the completed phase 3 semaglutide trials on ClinicalTrials.gov that have posted results."
- "Which Reactome pathways is TP53 in?"
- "Get the AlphaFold model and PAE for P00533."

## Trying it out

Each folder in `evals/public-database-lookup/` has a prompt and a list of what a good answer must get right,
with expected values and the date they were checked:

| Task | Tests |
|---|---|
| `task_1` | Identifier conversion for a compound list (`t1_compounds.csv`): salt vs. parent, stereoisomers, a name that does not exist |
| `task_2` | Exhaustive ChEMBL retrieval: total count, pagination, local filters, count reconciliation, CSV output |
| `task_3` | A multi-allelic rsID across dbSNP, ClinVar and gnomAD |
| `task_4` | ClinicalTrials.gov counts with ambiguous server-side filters (Phase 2/3 overlap, loose intervention matching) |
| `task_5` | A bulk request that should be sized and confirmed before downloading |

Run each prompt in a fresh session with and without the skill. Databases change, so later counts will drift
from the ones recorded. Judge the reasoning, the reconciliation and the provenance, not exact numbers.
Without the skill, agents tend to answer from memory, stop after the first page of results, merge salt and
parent compounds, or report one frequency for a multi-allelic rsID.

To check that the code in the skill still runs against the live APIs, use the runner in
`skills/public-database-lookup/references/adding-a-database.md` (section *Testing*). On 2026-11-27 every block
passed except two ENA Browser API examples that timed out at 30 s because the server was slow that day.

## Limitations

- Public endpoints only. Controlled-access data (GDC controlled files, private cBioPortal instances,
  unreleased ENCODE objects) is out of scope; the agent says what access would be needed.
- Not a literature search tool. For papers, use a literature skill or PubMed directly.
- Large pulls (over 10,000 records or 100 calls) stop for confirmation, and the agent suggests the
  database's official bulk download.
- NCBI Virus web-interface filters (host, geography, completeness and so on) are not reproduced exactly; the
  agent enforces them explicitly and says so.
- APIs change. Reference files date their observations (for example "on 2026-10-07 this returned …"). When a
  call starts failing, update the reference file using `references/adding-a-database.md`.
- Some services are slow or rate-limited (ENA Browser API, MouseMine, NCBI without a key). Expect timeouts
  now and then; the agent retries once and then falls back to another database.
