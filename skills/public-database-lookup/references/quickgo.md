# QuickGO (EBI GO Annotation Browser)

## Base URL
```
https://www.ebi.ac.uk/QuickGO/services/
```

## Auth
No auth required.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ontology/go/terms/{goId}` | GO term details |
| `/ontology/go/terms/{goId}/children` | Child terms |
| `/ontology/go/terms/{goId}/ancestors` | Ancestor terms |
| `/ontology/go/search?query={term}` | Search GO terms by keyword |
| `/annotation/search` | Search annotations by gene/taxon/GO term |

`{goId}` in a path is a CURIE: quote it with `requests.utils.quote(go_id, safe="")`.

## Annotation Search Parameters
- `goId` — GO term (e.g. GO:0003723)
- `taxonId` — NCBI taxonomy (e.g. 9606 for human)
- `geneProductId` — UniProt accession
- `evidenceCode` — ECO evidence code (e.g. ECO:0000269)
- `aspect` — biological_process, molecular_function, cellular_component
- `limit`, `page` — pagination; page is one-based, and annotation search limits each page to 200
- Send `headers={"Accept": "application/json"}`; preserve evidence, qualifiers/negation and annotation provenance.

## Example Calls
```python
import requests

QUICKGO = "https://www.ebi.ac.uk/QuickGO/services"
accept_json = {"Accept": "application/json"}

go_id = "GO:0003723"
r = requests.get(f"{QUICKGO}/ontology/go/terms/{requests.utils.quote(go_id, safe='')}",
                 headers=accept_json, timeout=30)
r.raise_for_status()
term = r.json()["results"][0]
# Human annotations for RNA binding
r = requests.get(f"{QUICKGO}/annotation/search", params={"goId": go_id, "taxonId": 9606, "limit": 10},
                 headers=accept_json, timeout=30)
r.raise_for_status()
ann = r.json()
# Search terms by keyword
r = requests.get(f"{QUICKGO}/ontology/go/search", params={"query": "apoptosis", "limit": 5},
                 headers=accept_json, timeout=30)
r.raise_for_status()
{"term": (term["id"], term["name"], term["aspect"]),
 "annotations": {"hits": ann["numberOfHits"], "pages": ann["pageInfo"]["total"],
                 "first": [(a["geneProductId"], a["qualifier"], a["goEvidence"], a["reference"]) for a in ann["results"][:3]]},
 "search": [(t["id"], t["name"]) for t in r.json()["results"]]}
```

## Response Format
JSON. Annotations: paginated results with gene product, GO term, evidence, qualifier.

## Rate Limits
EBI fair-use policy. Use download endpoint for large result sets.
