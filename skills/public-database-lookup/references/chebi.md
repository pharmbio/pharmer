# ChEBI (Chemical Entities of Biological Interest) API Reference

## Contents
- Base URLs
- Authentication
- Rate Limits
- Important Note
- OLS4 API Endpoints (Recommended for REST/JSON)
  - 1. Search ChEBI Terms
  - 2. Lookup by ChEBI ID
  - 3. Get Term by Short Form
  - 4. Term Hierarchy — Parents
  - 5. Term Hierarchy — Children
  - 6. Ontology Metadata
- OLS Search Response Format
- ChEBI 2.0 REST endpoints

## Base URLs
- **OLS (Ontology Lookup Service) API**: `https://www.ebi.ac.uk/ols4/api`
- **ChEBI REST API**: `https://www.ebi.ac.uk/chebi/backend/api/public`

## Authentication
None required. All endpoints are public.

## Rate Limits
No published hard limits. EBI general guidance: reasonable usage.

## Important Note
ChEBI 2.0 replaced the deprecated SOAP service with a public REST API. Use ChEBI REST for chemical records and structure searches; OLS4 remains useful for ontology traversal.

---

## OLS4 API Endpoints (Recommended for REST/JSON)

### 1. Search ChEBI Terms
```
GET https://www.ebi.ac.uk/ols4/api/search?q={query}&ontology=chebi
```
Example:
```python
import requests

OLS4 = "https://www.ebi.ac.uk/ols4/api"
CHEBI = "https://www.ebi.ac.uk/chebi/backend/api/public"

r = requests.get(f"{OLS4}/search", params={"q": "aspirin", "ontology": "chebi"},
                 headers={"Accept": "application/json"}, timeout=30)
r.raise_for_status()
res = r.json()["response"]
{"numFound": res["numFound"], "docs": [(d["obo_id"], d["label"]) for d in res["docs"][:5]]}
```
Returns JSON with matching ChEBI terms, IDs, definitions, synonyms.

### 2. Lookup by ChEBI ID
```
GET https://www.ebi.ac.uk/ols4/api/ontologies/chebi/terms?iri=http://purl.obolibrary.org/obo/CHEBI_{id}
```
Example (`requests` encodes the IRI in `params`):
```python
r = requests.get(f"{OLS4}/ontologies/chebi/terms",
                 params={"iri": "http://purl.obolibrary.org/obo/CHEBI_15365"},
                 headers={"Accept": "application/json"}, timeout=30)
r.raise_for_status()
term = r.json()["_embedded"]["terms"][0]
{"obo_id": term["obo_id"], "label": term["label"], "synonyms": term.get("synonyms", [])[:5]}
```
Returns full term details: name, definition, synonyms, xrefs, relationships.

### 3. Get Term by Short Form
```
GET https://www.ebi.ac.uk/ols4/api/ontologies/chebi/terms/{iri_path}
```
(Double-encoded IRI in path: `iri_path` is `http://purl.obolibrary.org/obo/CHEBI_{id}` passed through
`requests.utils.quote(..., safe="")` twice. A singly encoded IRI returns HTTP 400.)

### 4. Term Hierarchy — Parents
```
GET https://www.ebi.ac.uk/ols4/api/ontologies/chebi/terms/{iri_path}/parents
```

### 5. Term Hierarchy — Children
```
GET https://www.ebi.ac.uk/ols4/api/ontologies/chebi/terms/{iri_path}/children
```

Sections 3-5:
```python
iri = "http://purl.obolibrary.org/obo/CHEBI_15365"
iri_path = requests.utils.quote(requests.utils.quote(iri, safe=""), safe="")
r = requests.get(f"{OLS4}/ontologies/chebi/terms/{iri_path}", headers={"Accept": "application/json"}, timeout=30)
r.raise_for_status()
term = r.json()
r = requests.get(f"{OLS4}/ontologies/chebi/terms/{iri_path}/parents", headers={"Accept": "application/json"}, timeout=30)
r.raise_for_status()
parents = r.json().get("_embedded", {}).get("terms", [])  # same for /children; an empty page has no _embedded
{"term": (term["obo_id"], term["label"]), "parents": [(t["obo_id"], t["label"]) for t in parents]}
```

### 6. Ontology Metadata
```
GET https://www.ebi.ac.uk/ols4/api/ontologies/chebi
```

## OLS Search Response Format
```json
{
  "response": {
    "numFound": 5,
    "docs": [
      {
        "id": "chebi:15365",
        "iri": "http://purl.obolibrary.org/obo/CHEBI_15365",
        "label": "aspirin",
        "description": ["A member of the class of benzoic acids..."],
        "short_form": "CHEBI_15365",
        "obo_id": "CHEBI:15365",
        "ontology_name": "chebi",
        "type": "class"
      }
    ]
  }
}
```

## ChEBI 2.0 REST endpoints

| GET path (relative to the ChEBI REST base) | Parameters / purpose |
|---|---|
| `/compound/{chebi_id}/` | Full entity; numeric ID or `CHEBI:` prefix (quote it: `requests.utils.quote("CHEBI:15365", safe="")`) |
| `/es_search/` | `term` required; `page=1`, `size=15` defaults |
| `/ontology/parents/{chebi_id}/` | Ontology parents |
| `/ontology/children/{chebi_id}/` | Ontology children |
| `/structure_search/` | `smiles`, `search_type=connectivity|similarity|substructure` |
| `/molfile/{id}/` | Structure file |

For similarity search, use `similarity` between 0.4 and 1.0. The default
`three_star_only=true` limits structure results to three-star entries; explicitly
set false when two-star entries are also in scope. Search pagination uses `page`
and `size`. The current schema leaves several response bodies unspecified;
inspect the returned JSON before choosing field paths, and do not assume OLS's
`response.docs` envelope applies to ChEBI REST.

Illustrative request:

```python
r = requests.get(f"{CHEBI}/es_search/", params={"term": "aspirin", "page": 1, "size": 5},
                 headers={"Accept": "application/json"}, timeout=30)
r.raise_for_status()
body = r.json()
{"keys": sorted(body), "total": body.get("total"),
 "hits": [(h["_source"]["chebi_accession"], h["_source"]["name"]) for h in body.get("results", [])]}
```

Reviewed 2026-09-30: [ChEBI OpenAPI](https://www.ebi.ac.uk/chebi/backend/api/schema/),
[ChEBI 2.0 migration](https://www.ebi.ac.uk/about/news/updates-from-data-resources/chebi-2-0-launches/).
