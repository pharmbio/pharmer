# Gene Ontology (GO) API Reference

## Contents
- Base URLs
- Authentication
- Rate Limits
- GO API (api.geneontology.org)
  - 1. GO Term Lookup
  - 2. Gene/Protein Annotations (Bioentity)
  - 3. Genes Annotated to a GO Term
  - 4. Search Entities
  - 5. Ontology Ancestors / Descendants
- QuickGO API (EBI — recommended for robust annotation queries)
  - 1. GO Term Details
  - 2. Search Annotations
  - 3. Annotations by GO Term
  - 4. Filter Annotations by Evidence
  - 5. GO Term Children
  - 6. GO Term Ancestors (Chart)
  - 7. Search GO Terms by Name
- QuickGO Annotation Search Parameters
- QuickGO Response Format
- Notes

## Base URLs
- **QuickGO (EBI, recommended)**: `https://www.ebi.ac.uk/QuickGO/services` — most reliable endpoint
- **GO API**: `https://api.geneontology.org/api` — current OpenAPI schema: `https://api.geneontology.org/openapi.json`
- **AmiGO / GOlr (Solr-based)**: `https://golr.geneontology.org/solr`

## Authentication
None required. All endpoints are public.

## Rate Limits
No published hard limits. QuickGO recommends reasonable usage.

---

## GO API (api.geneontology.org)

### 1. GO Term Lookup
```
GET https://api.geneontology.org/api/ontology/term/{go_id}
```
Example (CURIEs in a path go through `requests.utils.quote`, which encodes the colon):
```python
import requests

GO_API = "https://api.geneontology.org/api"

r = requests.get(f"{GO_API}/ontology/term/{requests.utils.quote('GO:0008150', safe='')}", timeout=30)
r.raise_for_status()
term = r.json()
{"goid": term.get("goid"), "label": term.get("label"), "synonyms": len(term.get("synonyms", []))}
```
Returns JSON with term name, definition, namespace (biological_process / molecular_function / cellular_component), synonyms.

### 2. Gene/Protein Annotations (Bioentity)
```
GET https://api.geneontology.org/api/bioentity/gene/{gene_id}/function
```
Example — GO annotations for a UniProt protein:
```python
gene = requests.utils.quote("UniProtKB:P04637", safe="")
r = requests.get(f"{GO_API}/bioentity/gene/{gene}/function", timeout=30)
r.raise_for_status()
assocs = r.json()["associations"]
{"returned": len(assocs), "first": [(a["object"]["id"], a["object"].get("label")) for a in assocs[:5]]}
```
Returns GO annotations with evidence codes, qualifiers, references.

### 3. Genes Annotated to a GO Term
```
GET https://api.geneontology.org/api/bioentity/function/{go_id}/genes
```
Example:
```python
go_id = requests.utils.quote("GO:0006915", safe="")
r = requests.get(f"{GO_API}/bioentity/function/{go_id}/genes", params={"rows": 20}, timeout=30)
r.raise_for_status()
assocs = r.json()["associations"]
{"returned": len(assocs), "first": [(a["subject"]["id"], a["subject"].get("label")) for a in assocs[:5]]}
```
Returns genes/proteins annotated with that GO term.

### 4. Search Entities
```
GET https://api.geneontology.org/api/search/entity/autocomplete/{query}
```
Example:
```python
r = requests.get(f"{GO_API}/search/entity/autocomplete/{requests.utils.quote('apoptosis', safe='')}",
                 timeout=30)
r.raise_for_status()
docs = r.json()["docs"]
{"returned": len(docs), "first": [(d.get("label"), d.get("name"), d.get("taxon_label")) for d in docs[:5]]}
```

### 5. Ontology Ancestors / Descendants
```
GET https://api.geneontology.org/api/ontology/term/{go_id}/graph
```

---

## QuickGO API (EBI — recommended for robust annotation queries)

### 1. GO Term Details
```
GET https://www.ebi.ac.uk/QuickGO/services/ontology/go/terms/{go_ids}
```
Example:
```python
import requests

QUICKGO = "https://www.ebi.ac.uk/QuickGO/services"

r = requests.get(f"{QUICKGO}/ontology/go/terms/{requests.utils.quote('GO:0008150', safe='')}", timeout=30)
r.raise_for_status()
[(t["id"], t["name"], t.get("aspect")) for t in r.json()["results"]]
```
Accepts comma-separated IDs (up to 25): quote the joined string, `requests.utils.quote(",".join(ids), safe="")`.

### 2. Search Annotations
```
GET https://www.ebi.ac.uk/QuickGO/services/annotation/search?geneProductId={uniprot_id}
```
Example — annotations for TP53:
```python
r = requests.get(f"{QUICKGO}/annotation/search", params={"geneProductId": "P04637", "limit": 25}, timeout=30)
r.raise_for_status()
body = r.json()
{"hits": body["numberOfHits"], "pages": body["pageInfo"]["total"],
 "first": [(a["goId"], a["evidenceCode"], a["reference"]) for a in body["results"][:5]]}
```

### 3. Annotations by GO Term
```python
r = requests.get(f"{QUICKGO}/annotation/search",
                 params={"goId": "GO:0006915", "taxonId": 9606, "limit": 25}, timeout=30)
r.raise_for_status()
body = r.json()
{"hits": body["numberOfHits"], "first": [(a["geneProductId"], a["symbol"], a["evidenceCode"]) for a in body["results"][:5]]}
```

### 4. Filter Annotations by Evidence
`goUsage` needs `goId` (live 2026-10-07: HTTP 400 "Annotation goUsage requires 'goId' to be set"), so it is not
sent here. `evidenceCode` already matches descendant ECO codes by default (837 hits vs 17 with `evidenceCodeUsage=exact`).
```python
r = requests.get(f"{QUICKGO}/annotation/search",
                 params={"geneProductId": "P04637", "evidenceCode": "ECO:0000269", "limit": 25}, timeout=30)
r.raise_for_status()
body = r.json()
{"hits": body["numberOfHits"], "evidence_codes": sorted({a["evidenceCode"] for a in body["results"]})}
```

### 5. GO Term Children
```python
r = requests.get(f"{QUICKGO}/ontology/go/terms/{requests.utils.quote('GO:0008150', safe='')}/children", timeout=30)
r.raise_for_status()
children = r.json()["results"][0].get("children", [])
{"count": len(children), "first": [(c["id"], c["relation"]) for c in children[:5]]}
```

### 6. GO Term Ancestors (Chart)
```python
r = requests.get(f"{QUICKGO}/ontology/go/terms/{requests.utils.quote('GO:0006915', safe='')}/ancestors",
                 params={"relations": "is_a,part_of"}, timeout=30)
r.raise_for_status()
r.json()["results"][0].get("ancestors", [])
```

### 7. Search GO Terms by Name
```python
r = requests.get(f"{QUICKGO}/ontology/go/search", params={"query": "apoptosis", "limit": 10}, timeout=30)
r.raise_for_status()
body = r.json()
{"hits": body["numberOfHits"], "first": [(t["id"], t["name"]) for t in body["results"][:5]]}
```

## QuickGO Annotation Search Parameters
| Parameter | Description |
|-----------|-------------|
| `geneProductId` | UniProt accession (e.g., P04637) |
| `goId` | GO term (e.g., GO:0006915) |
| `goUsage` | `exact` or `descendants` (include child terms) |
| `taxonId` | NCBI taxonomy ID (9606 = human) |
| `evidenceCode` | ECO code (e.g., ECO:0000269 = experimental) |
| `aspect` | `biological_process`, `molecular_function`, `cellular_component` |
| `limit` | Results per page (max 200) |
| `page` | Page number (1-based) |

## QuickGO Response Format
```json
{
  "numberOfHits": 1234,
  "results": [
    {
      "geneProductId": "P04637",
      "symbol": "TP53",
      "goId": "GO:0006915",
      "goName": "apoptotic process",
      "evidenceCode": "ECO:0000269",
      "goAspect": "biological_process",
      "taxonId": 9606,
      "reference": "PMID:12345678",
      "assignedBy": "UniProt"
    }
  ]
}
```

## Notes
- QuickGO (EBI) is generally more robust and better documented for annotation queries.
- GO API pagination uses `start`/`rows` on supported bioentity routes. Inspect the current OpenAPI schema for per-route parameters; the autocomplete route replaces the former general entity-search route.
- Quote GO IDs and other CURIEs when building paths: `requests.utils.quote("GO:0008150", safe="")` (sends `GO%3A0008150`). Query values go raw in `params`; never pre-encode them.
- Three GO namespaces: biological_process (BP), molecular_function (MF), cellular_component (CC).
- Evidence codes: IDA (direct assay), IMP (mutant phenotype), IGI (genetic interaction), IEA (electronic annotation), etc.
