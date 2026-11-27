# Exhaustive Retrieval

Read this when the scope is every matching record: "all trials for X", "all variants in gene Y",
an accession list, or a dataset for downstream analysis. A targeted lookup does not need it.
The code uses `fetch` and `REQUEST_LOG` from SKILL.md, **The fetch helper**.

## Contents
- Count and budget
- Pagination styles
- Worked example: link pagination (UniProt)
- Worked example: offset pagination (ChEMBL)
- Local filters
- Reconcile and report
- Dataset hazards

## Count and budget

1. **Get the total first**: a count endpoint, or the `total`/`count` metadata of a one-record
   page. Each reference file names the field (ChEMBL `page_meta.total_count`, UniProt
   `x-total-results` header, ClinicalTrials.gov `countTotal=true`, GDC `pagination.total`, ENA `/count`).
2. **Estimate the cost**: calls = total ÷ page size, rounded up; time = calls ÷ the API's rate limit.
3. **Ask before going past 10,000 records or 100 calls**, or past the API's own bulk-use guidance.
   When the user really needs everything, propose the official bulk route instead (PubChem FTP,
   ChEMBL dumps, ClinicalTrials.gov bulk download, GDC Data Transfer Tool, HPA TSV downloads).
4. **Fix the order** with `sort`, accession order or a stable cursor where the API allows it, so a
   rerun returns the same records.

If the API exposes no count, say that completeness cannot be verified independently and report
the stopping condition you used.

## Pagination styles

The reference file has the exact parameter names; these are the patterns.

| Style | Databases | Advance by | Stop when |
|---|---|---|---|
| Offset | ChEMBL `offset`, NCBI E-utilities `retstart`, GDC `from`, OpenFDA `skip` (max 25,000), Monarch `offset` | the number of records returned | a page is empty, or the cumulative count reaches the total |
| Page number | ZINC `page` (1-based), QuickGO `page` (1-based), cBioPortal `pageNumber` (0-based), GTEx `page` (0-based), HPO `page` (0-based) | 1 | a page is short or empty, or the total is reached |
| Token or link | ClinicalTrials.gov `nextPageToken`, UniProt `Link` header, HCA `pagination.next`, InterPro `next`, GWAS Catalog `_links.next.href`, ChEMBL `page_meta.next` | the token or URL the response returns | no token or link comes back |
| Count-then-fetch | ENA Portal `/search` (no offset) | — | check `/count`, then fetch one bounded query or partition by an indexed field |

Never invent a token or increment it numerically. A `next` link usually carries the query
already, so drop your own `params` when following it.

## Worked example: link pagination (UniProt)

```python
url = "https://rest.uniprot.org/uniprotkb/search"
params = {"query": "gene_exact:TP53 AND organism_id:9606",
          "fields": "accession,reviewed", "size": 50, "format": "json"}
records, batches, expected = [], [], None
while url and len(batches) < 100:  # the 100-call budget
    r = fetch("GET", url, params=params)
    if expected is None:
        expected = int(r.headers["x-total-results"])
    page = r.json()["results"]
    records.extend(page)
    batches.append({"batch": len(batches) + 1, "returned": len(page), "cumulative": len(records)})
    url = r.links.get("next", {}).get("url")  # the next URL already carries the query
    params = None
    time.sleep(0.2)  # UniProt publishes no limit; 5 requests/s stays polite
{"expected": expected, "retrieved": len(records), "complete": url is None, "batches": batches}
```

## Worked example: offset pagination (ChEMBL)

```python
url = "https://www.ebi.ac.uk/chembl/api/data/activity.json"
params = {"molecule_chembl_id": "CHEMBL941", "target_chembl_id": "CHEMBL1862",
          "standard_type": "IC50", "order_by": "activity_id", "limit": 1000, "offset": 0}
records, batches, expected = [], [], None
while len(batches) < 100:
    page = fetch("GET", url, params=params).json()
    if expected is None:
        expected = page["page_meta"]["total_count"]
    rows = page["activities"]
    records.extend(rows)
    batches.append({"offset": params["offset"], "returned": len(rows), "cumulative": len(records)})
    if len(rows) == 0 or len(records) >= expected:
        break
    params["offset"] += len(rows)
{"expected": expected, "retrieved": len(records), "batches": batches}
```

## Local filters

Apply each local filter as its own step and log how many records it removed, so the count
reconciliation can name every drop:

```python
filter_log = []
kept = records
step = [a for a in kept if a.get("standard_units") == "nM"]
filter_log.append({"filter": "standard_units == nM", "removed": len(kept) - len(step)})
kept = step
step = [a for a in kept if a.get("standard_relation") == "="]
filter_log.append({"filter": "standard_relation == '='", "removed": len(kept) - len(step)})
kept = step
{"before": len(records), "after": len(kept), "filter_log": filter_log}
```

## Reconcile and report

Report four numbers and the steps between them. For the ChEMBL example above:

```text
Count reconciliation: expected 94 (server total) / retrieved 94 in 1 batch /
  after local filters 72 (standard_units == nM: -3; standard_relation == '=': -19) / returned 72
```

- **retrieved < expected**: pagination stopped early (budget, error, or a page-size cap). Resume
  from the last logged batch, or report the dataset as incomplete. Never present it as complete.
- **retrieved > expected**: duplicates across pages or a moving total. Deduplicate by accession,
  report how many duplicates there were, and note that the source changed during retrieval.
- Save the full dataset to a file (CSV, TSV or JSON) rather than printing it, and report the
  path, the batch log and `REQUEST_LOG` (pages of one query can be summarised as "pages 1–9 of <URL>").

## Dataset hazards

- **Accession versions**: keep them (`NM_000546.6`, `ENSG00000139618.14`) when sequence or
  coordinates depend on them; RefSeq, GenBank, ENA, DDBJ and UniProt records are not interchangeable.
- **Dates**: collection, release, submission and publication dates are different fields. Say which
  one a date filter used.
- **Viral sequence sets**: track completeness, segment, host, geography, collection date,
  ambiguous-base threshold, lab passage, source database and protein-annotation filters, and
  report which were enforced server-side and which locally.
- **Moving targets**: databases update between calls. Record the access date, and the release when
  the API reports one (Open Targets API version, Ensembl release, gnomAD dataset, HCA catalogue).
