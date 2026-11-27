# InterPro API Reference

## Contents
- Base URL
- Authentication
- Rate Limits
- Response Format
- Key Endpoints
  - 1. Entry Lookup (by accession)
  - 2. Entry Lookup by Member Database
  - 3. Search / List Entries
  - 4. Protein Annotations — Get InterPro Entries for a Protein
  - 5. Proteins with a Given Entry
  - 6. Structure Mappings
  - 7. Entry by Type Filter
  - 8. Taxonomy Cross-Reference
- Pagination
- Entry Response Key Fields
- Notes

## Base URL
```
https://www.ebi.ac.uk/interpro/api
```

## Authentication
None required. Fully public API.

## Rate Limits
No published hard limits. EBI general guidance: be reasonable, use bulk downloads for large datasets.

## Response Format
JSON by default. Some endpoints support `?format=json` explicitly.

## Key Endpoints

### 1. Entry Lookup (by accession)
```
GET https://www.ebi.ac.uk/interpro/api/entry/interpro/{accession}
```
Example:
```python
import requests

INTERPRO = "https://www.ebi.ac.uk/interpro/api"

r = requests.get(f"{INTERPRO}/entry/interpro/IPR000504", timeout=30)
r.raise_for_status()
meta = r.json()["metadata"]
go_terms = meta["go_terms"] if meta["go_terms"] else []  # null for some entries
{"name": meta["name"]["name"], "type": meta["type"], "members": meta["member_databases"],
 "go": [g["identifier"] for g in go_terms]}
```
Returns JSON with entry name, type (family/domain/site/etc.), description, GO terms, literature references.

### 2. Entry Lookup by Member Database
```
GET https://www.ebi.ac.uk/interpro/api/entry/pfam/{pfam_accession}
GET https://www.ebi.ac.uk/interpro/api/entry/smart/{smart_accession}
GET https://www.ebi.ac.uk/interpro/api/entry/prosite/{prosite_accession}
```
Example:
```python
r = requests.get(f"{INTERPRO}/entry/pfam/PF00076", timeout=30)
r.raise_for_status()
meta = r.json()["metadata"]
{"name": meta["name"]["name"], "type": meta["type"], "integrated": meta["integrated"]}
```

### 3. Search / List Entries
```
GET https://www.ebi.ac.uk/interpro/api/entry/interpro?search={query}
```
Example:
```python
r = requests.get(f"{INTERPRO}/entry/interpro", params={"search": "kinase"}, timeout=30)
r.raise_for_status()
page = r.json()
{"count": page["count"], "next": page["next"], "first": [e["metadata"]["accession"] for e in page["results"][:5]]}
```
Returns paginated list of matching InterPro entries.

### 4. Protein Annotations — Get InterPro Entries for a Protein
```
GET https://www.ebi.ac.uk/interpro/api/entry/interpro/protein/uniprot/{uniprot_accession}
```
Example:
```python
r = requests.get(f"{INTERPRO}/entry/interpro/protein/uniprot/P12345", timeout=30)
r.raise_for_status()
[(e["metadata"]["accession"], e["metadata"]["type"]) for e in r.json()["results"]]
```
Returns all InterPro entries annotating that protein.

### 5. Proteins with a Given Entry
```
GET https://www.ebi.ac.uk/interpro/api/protein/uniprot/entry/interpro/{accession}
```
Example:
```python
r = requests.get(f"{INTERPRO}/protein/uniprot/entry/interpro/IPR000504", params={"page_size": 5}, timeout=30)
r.raise_for_status()
page = r.json()
{"count": page["count"], "first": [p["metadata"]["accession"] for p in page["results"]]}
```
Returns paginated list of UniProt proteins annotated with that entry.

### 6. Structure Mappings
```
GET https://www.ebi.ac.uk/interpro/api/structure/pdb/entry/interpro/{accession}
```
Example:
```python
r = requests.get(f"{INTERPRO}/structure/pdb/entry/interpro/IPR000504", params={"page_size": 5}, timeout=30)
r.raise_for_status()
page = r.json()
{"count": page["count"], "first": [p["metadata"]["accession"] for p in page["results"]]}
```

### 7. Entry by Type Filter
```
GET https://www.ebi.ac.uk/interpro/api/entry/interpro?type=domain
GET https://www.ebi.ac.uk/interpro/api/entry/interpro?type=family
GET https://www.ebi.ac.uk/interpro/api/entry/interpro?type=homologous_superfamily
```

### 8. Taxonomy Cross-Reference
```
GET https://www.ebi.ac.uk/interpro/api/taxonomy/uniprot/entry/interpro/{accession}
```

## Pagination
Responses include `next` and `previous` URLs:
```json
{
  "count": 1234,
  "next": "https://www.ebi.ac.uk/interpro/api/entry/interpro?cursor=...&page_size=20",
  "previous": null,
  "results": [...]
}
```
Set `params={"page_size": N}` to control page size (default 20). Request the `next` URL as returned, without `params`: it already carries the cursor and filters.

## Entry Response Key Fields
```json
{
  "metadata": {
    "accession": "IPR000504",
    "name": {"name": "RNA recognition motif domain", "short": "RRM_dom"},
    "type": "domain",
    "source_database": "interpro",
    "member_databases": {"pfam": {"PF00076": "RRM_1"}},
    "go_terms": [{"identifier": "GO:0003723", "name": "RNA binding", "category": {...}}],
    "description": [{"text": "<p>The RNA recognition motif...</p>", ...}]
  }
}
```

## Notes
- The API follows a composable URL pattern: combine entity types (entry, protein, structure, taxonomy) to create cross-reference queries.
- Member databases include `pfam`, `smart`, `prosite` (patterns), `profile` (PROSITE profiles), `prints`, `panther`, `cdd`, `hamap`, `pirsf`, `sfld`, `cathgene3d`, `ssf`, and `ncbifam`. `tigrfams` was replaced by `ncbifam`; discover current sources from the API root.
