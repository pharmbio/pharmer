# NCBI Gene (E-utilities)

## Base URL
```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
```

## Auth
No key required. Optional: `NCBI_API_KEY` raises the limit from 3 to 10 requests/s. Default to unauthenticated; see SKILL.md, **Optional API keys**, before using one.

## Key Endpoints

### eSearch — Search for gene IDs
```
GET /esearch.fcgi?db=gene&term={query}&retmode=json&retmax={n}
```

Parameters:
- `db=gene` (required)
- `term` — search query (e.g. `BRCA1[gene] AND human[orgn]`; pass it unencoded in `params`)
- `retmode=json`
- `retmax` — max results (default 20)
- `retstart` — pagination offset

Example:
```python
import requests

NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

r = requests.get(
    f"{NCBI_EUTILS}/esearch.fcgi",
    params={"db": "gene", "term": "BRCA1[gene] AND human[orgn]", "retmode": "json", "retmax": 5},
    timeout=30,
)
r.raise_for_status()
search = r.json()["esearchresult"]
{"count": search["count"], "ids": search["idlist"], "translation": search["querytranslation"]}
```

### eSummary — Get gene metadata
```
GET /esummary.fcgi?db=gene&id={gene_ids}&retmode=json
```

Key response fields: `name`, `description`, `chromosome`, `maplocation`, `otheraliases`, `nomenclaturesymbol`, `organism`

Example:
```python
r = requests.get(
    f"{NCBI_EUTILS}/esummary.fcgi",
    params={"db": "gene", "id": "672", "retmode": "json"},  # several IDs: ",".join(gene_ids)
    timeout=30,
)
r.raise_for_status()
doc = r.json()["result"]["672"]
{k: doc[k] for k in ("name", "description", "chromosome", "maplocation", "nomenclaturesymbol")}
```

### eFetch — Full gene records (XML/text only, no JSON)
```
GET /efetch.fcgi?db=gene&id={gene_ids}&rettype=gene_table&retmode=text
```

### eLink — Cross-database links (gene to PubMed, OMIM, sequences)
```
GET /elink.fcgi?dbfrom=gene&db={target_db}&id={gene_id}&retmode=json
```

Target databases include `pubmed`, `omim`, `nuccore`, and `protein`; discover supported links with EInfo. BioSystems is retired; use current KEGG/Reactome resources for pathways.

Example — gene to PubMed:
```python
r = requests.get(
    f"{NCBI_EUTILS}/elink.fcgi",
    params={"dbfrom": "gene", "db": "pubmed", "id": "672", "retmode": "json"},
    timeout=30,
)
r.raise_for_status()
linksetdbs = r.json()["linksets"][0].get("linksetdbs", [])
{ls["linkname"]: len(ls["links"]) for ls in linksetdbs}
```

## Rate Limits
- Without API key: 3 requests/second
- With API key: 10 requests/second
- For bulk: use `usehistory=y` with eSearch, then retrieve via `query_key` and `WebEnv`
