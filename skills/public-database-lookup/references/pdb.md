# RCSB Protein Data Bank (PDB) API Reference

## Contents
- Base URLs
- Authentication
- Rate Limits
- Key Endpoints
  - 1. Entry Lookup (Data API)
  - 2. Polymer Entity (unique molecular entity)
  - 3. Assembly Info
  - 4. Full-Text and Attribute Search (Search API)
  - 5. Sequence Search (Search API)
  - 6. Structure Similarity Search
  - 7. Download Structure Files
  - 8. GraphQL Query
- Response Format
- Useful `return_type` Values for Search
- Notes

## Base URLs
- **Data API**: `https://data.rcsb.org/rest/v1`
- **Search API**: `https://search.rcsb.org/rcsbsearch/v2/query`
- **GraphQL**: `https://data.rcsb.org/graphql`
- **Files**: `https://files.rcsb.org`

## Authentication
None required. Fully public API.

## Rate Limits
No published hard limits; be courteous (a few requests/second). Bulk downloads available via FTP.

## Key Endpoints

### 1. Entry Lookup (Data API)
```
GET https://data.rcsb.org/rest/v1/core/entry/{entry_id}
```
Example:
```python
import requests

RCSB_DATA = "https://data.rcsb.org/rest/v1"
RCSB_SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_GRAPHQL = "https://data.rcsb.org/graphql"

r = requests.get(f"{RCSB_DATA}/core/entry/4HHB", timeout=30)
r.raise_for_status()
entry = r.json()
{"title": entry["struct"]["title"], "method": [e["method"] for e in entry["exptl"]],
 "resolution": entry["rcsb_entry_info"].get("resolution_combined")}
```
Returns JSON with resolution, method, deposition date, title, authors, etc.

### 2. Polymer Entity (unique molecular entity)
```
GET https://data.rcsb.org/rest/v1/core/polymer_entity/{entry_id}/{entity_id}
```
Example:
```python
r = requests.get(f"{RCSB_DATA}/core/polymer_entity/4HHB/1", timeout=30)
r.raise_for_status()
ids = r.json()["rcsb_polymer_entity_container_identifiers"]
{"label_asym_ids": ids["asym_ids"], "auth_asym_ids": ids["auth_asym_ids"], "uniprot": ids.get("uniprot_ids")}
```

An entity may have multiple chain instances. For chain-specific coordinates/annotations use `/core/polymer_entity_instance/{entry_id}/{label_asym_id}`; `label_asym_id` is the mmCIF identifier, not necessarily the author chain ID.

### 3. Assembly Info
```
GET https://data.rcsb.org/rest/v1/core/assembly/{entry_id}/{assembly_id}
```

### 4. Full-Text and Attribute Search (Search API)
```
POST https://search.rcsb.org/rcsbsearch/v2/query
```
Example — search by UniProt accession:
```json
{
  "query": {
    "type": "terminal",
    "service": "text",
    "parameters": {
      "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
      "operator": "exact_match",
      "value": "P69905"
    }
  },
  "return_type": "entry"
}
```
```python
query = {
    "query": {"type": "terminal", "service": "text", "parameters": {
        "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
        "operator": "exact_match", "value": "P69905"}},
    "return_type": "entry",
    "request_options": {"paginate": {"start": 0, "rows": 25}},
}
r = requests.post(RCSB_SEARCH, json=query, timeout=30)
r.raise_for_status()
hits = r.json() if r.status_code == 200 else {"total_count": 0, "result_set": []}  # 204: no matches
{"total": hits["total_count"], "returned": len(hits["result_set"]),
 "ids": [h["identifier"] for h in hits["result_set"][:10]]}
```
Send the section 5 and 6 bodies the same way. GET with the document in a `json` query parameter
(`params={"json": json.dumps(query)}`) also works.

### 5. Sequence Search (Search API)
```json
{
  "query": {
    "type": "terminal",
    "service": "sequence",
    "parameters": {
      "evalue_cutoff": 0.1,
      "identity_cutoff": 0.9,
      "sequence_type": "protein",
      "value": "MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH"
    }
  },
  "return_type": "polymer_entity"
}
```

### 6. Structure Similarity Search
```json
{
  "query": {
    "type": "terminal",
    "service": "structure",
    "parameters": {
      "value": {"entry_id": "4HHB", "assembly_id": "1"},
      "operator": "strict_shape_match"
    }
  },
  "return_type": "assembly"
}
```

### 7. Download Structure Files
```
GET https://files.rcsb.org/download/{entry_id}.cif
GET https://files.rcsb.org/download/{entry_id}.pdb
```

### 8. GraphQL Query
```
POST https://data.rcsb.org/graphql
```
Body example, with the entry ID passed as a variable:
```python
gql = """
query Entry($id: String!) {
  entry(entry_id: $id) { rcsb_entry_info { resolution_combined } struct { title } }
}
"""
r = requests.post(RCSB_GRAPHQL, json={"query": gql, "variables": {"id": "4HHB"}}, timeout=30)
r.raise_for_status()
body = r.json()
if body.get("errors"):
    raise RuntimeError(body["errors"])
body["data"]["entry"]  # None for an unknown ID (HTTP 200, no errors)
```

## Response Format
REST/Data and successful Search results return JSON. Search can return HTTP 204 for no matches; do not attempt to JSON-decode an empty body. File downloads return PDB/mmCIF text.

## Useful `return_type` Values for Search
- `entry` — PDB IDs
- `polymer_entity` — entity-level results (e.g., 4HHB_1)
- `assembly` — biological assembly results

## Notes
- Search API uses POST with a JSON query DSL. Combine queries with `"type": "group"` and `"logical_operator": "and"/"or"`.
- Pagination via `"request_options": {"paginate": {"start": 0, "rows": 25}}`.
