# NCBI GEO (Gene Expression Omnibus) via E-utilities

## Contents
- Base URLs
- Important: The database name is `gds`
- Key Endpoints
  - eSearch — Search GEO
  - eSummary — Get metadata for UIDs
  - GEO Direct Query — Full records by accession
  - eLink — Cross-reference with other NCBI databases
- Practical Workflow
- Important Notes
- Rate Limits

## Base URLs

| Purpose | URL |
|---|---|
| E-utilities | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` |
| GEO direct query | `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi` |

## Important: The database name is `gds`

The Entrez database for GEO is `gds` (not `geo`). It contains all GEO record types: GDS datasets, GSE series, GPL platforms, GSM samples. Filter by type using `[ETYP]` in the search term.

## Key Endpoints

### eSearch — Search GEO

```
GET /esearch.fcgi?db=gds&term={query}&retmode=json&retmax={n}
```

Parameters:
- `db=gds` (required)
- `term` — search query with field tags
- `retmax` — max results (default 20)
- `retstart` — offset for pagination
- `retmode=json` — get JSON response
- `usehistory=y` — store results server-side for large queries
- `api_key` — NCBI API key (optional, raises rate limit)

#### Entry type filters (`[ETYP]`)
- `gds[ETYP]` — curated GEO DataSets
- `gse[ETYP]` — GEO Series (most common, use this by default)
- `gpl[ETYP]` — platforms
- `gsm[ETYP]` — samples

#### Other field tags
- `[Organism]` — e.g. `"Homo sapiens"[Organism]`
- `[PDAT]` — publication date
- `[Title]` — title search
- Boolean: `AND`, `OR`, `NOT` (uppercase)

Example — cancer GSE series in human:
```python
import time
import requests

NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
GEO_ACC = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"

r = requests.get(
    f"{NCBI_EUTILS}/esearch.fcgi",
    params={"db": "gds", "term": 'cancer AND gse[ETYP] AND "Homo sapiens"[Organism]',
            "retmax": 10, "retmode": "json"},
    timeout=30,
)
r.raise_for_status()
search = r.json()["esearchresult"]
{"count": search["count"], "uids": search["idlist"], "translation": search["querytranslation"]}
```

Response:
```json
{
  "esearchresult": {
    "count": "15432",
    "retmax": "10",
    "idlist": ["200012345", "200067890"],
    "querytranslation": "cancer AND gse[ETYP]"
  }
}
```

The IDs returned are numeric Entrez UIDs, not accessions. Resolve them with ESummary and read `accession`; do not depend on an arithmetic UID conversion.

### eSummary — Get metadata for UIDs

```
GET /esummary.fcgi?db=gds&id={uid_list}&retmode=json
```

Key response fields per record:
- `accession` — e.g. "GSE12345"
- `title`, `summary`
- `taxon` — organism
- `entrytype` — "GDS", "GSE", "GPL", "GSM"
- `gdstype` — e.g. "Expression profiling by array"
- `n_samples` — sample count
- `pubmedids` — linked PubMed IDs
- `pdat` — publication date
- `samples` — array of sample objects
- `ftplink` — data download path

Example:
```python
r = requests.get(
    f"{NCBI_EUTILS}/esummary.fcgi",
    params={"db": "gds", "id": "200012345", "retmode": "json"},
    timeout=30,
)
r.raise_for_status()
doc = r.json()["result"]["200012345"]
{k: doc[k] for k in ("accession", "entrytype", "gdstype", "taxon", "n_samples", "pdat", "ftplink")}
```

### GEO Direct Query — Full records by accession

```
GET https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}&form={format}&view={detail}
```

Parameters:
- `acc` — GEO accession (GSE12345, GDS1234, GPL570, GSM12345)
- `targ` — `self`, `gsm` (samples), `gpl` (platform), `gse` (series)
- `form` — `text` (SOFT format), `xml` (MINiML), `html`
- `view` — `quick`, `brief`, `full`, `data`

Example — series metadata in SOFT:
```python
r = requests.get(
    GEO_ACC,
    params={"acc": "GSE53757", "targ": "self", "form": "text", "view": "brief"},
    timeout=30,
)
r.raise_for_status()
soft = r.text.splitlines()
{"content_type": r.headers.get("Content-Type"), "lines": len(soft), "head": soft[:2]}
```

Note: acc.cgi does not return JSON. Use eSearch + eSummary for JSON results. Use acc.cgi when you need full SOFT/MINiML records.

### eLink — Cross-reference with other NCBI databases

```
GET /elink.fcgi?dbfrom=gds&db=pubmed&id={uid}&retmode=json
```

## Practical Workflow

For most queries, use this two-step approach:

1. **eSearch** to find UIDs matching the query
2. **eSummary** to get metadata for those UIDs

This gives you JSON throughout. With the History server, eSummary reads the search result
through `WebEnv`/`query_key` from the eSearch response instead of a pasted ID list:

```python
r = requests.get(
    f"{NCBI_EUTILS}/esearch.fcgi",
    params={"db": "gds", "term": 'cancer AND gse[ETYP] AND "Homo sapiens"[Organism]',
            "usehistory": "y", "retmax": 0, "retmode": "json"},
    timeout=30,
)
r.raise_for_status()
search = r.json()["esearchresult"]
time.sleep(0.34)
r = requests.get(
    f"{NCBI_EUTILS}/esummary.fcgi",
    params={"db": "gds", "WebEnv": search["webenv"], "query_key": search["querykey"],
            "retstart": 0, "retmax": 20, "retmode": "json"},  # next page: retstart += 20
    timeout=30,
)
r.raise_for_status()
result = r.json()["result"]
{"count": search["count"], "page": [result[uid]["accession"] for uid in result["uids"]]}
```

## Important Notes

- GDS records are mostly frozen — NCBI stopped curating new GDS. Use `gse[ETYP]` for comprehensive results.
- eFetch has limited support for the `gds` database. Use eSummary for metadata or acc.cgi for full records.
- Pass the raw term (spaces, quotes, brackets) in `params` and let `requests` encode it; a pre-encoded `+` or `%22` would be encoded again.

## Rate Limits

- **Without API key**: 3 requests/second
- **With API key**: 10 requests/second (free registration at ncbi.nlm.nih.gov/account/settings)
- Optional `tool` and `email` parameters identify the caller: send a generic tool name such as `tool="public-database-lookup"` and leave out `email` unless the user gives one
- For large result sets, use the History server (`usehistory=y` then pass `WebEnv` and `query_key` to eSummary)
