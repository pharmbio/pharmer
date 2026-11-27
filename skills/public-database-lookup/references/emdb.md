# EMDB (Electron Microscopy Data Bank)

## Base URL
```
https://www.ebi.ac.uk/emdb/api/
```

## Auth
No auth required.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/entry/{emdb_id}` | Full entry metadata (e.g. EMD-1234) |
| `/entry/map/{emdb_id}` | Map/volume metadata |
| `/entry/experiment/{emdb_id}` | Experimental details |
| `/entry/fitted/{emdb_id}` | Fitted PDB models |
| `/search/{query}?rows={n}` | Search entries by keyword (quote `{query}`) |

## Example Calls
```python
import requests

EMDB = "https://www.ebi.ac.uk/emdb/api"

# Entry metadata; /entry/experiment/, /entry/map/ and /entry/fitted/ take the same ID
r = requests.get(f"{EMDB}/entry/EMD-1234", headers={"Accept": "application/json"}, timeout=30)
r.raise_for_status()
entry = r.json()
# Search for ribosome entries. The query is a path segment, so quote it
# (Solr syntax such as 'ribosome AND resolution:[* TO 3]' works once quoted)
query_path = requests.utils.quote("ribosome", safe="")
r = requests.get(f"{EMDB}/search/{query_path}", params={"rows": 5},
                 headers={"Accept": "application/json"}, timeout=30)
r.raise_for_status()
{"entry": (entry["emdb_id"], entry["admin"]["title"]), "search_ids": [h["emdb_id"] for h in r.json()]}
```

## Response Format
JSON. Search accepts `rows` (default 10), `page` (1-based), and `fl` (field selection). `fl` applies only to CSV output (`headers={"Accept": "text/csv"}`); JSON search returns an array of full entry objects with no total count, so inspect it before iterating. Entry metadata is an object with `emdb_id`, `map`, and experimental/sample sections, not the map density file itself.

## Rate Limits
EBI fair-use policy. Map files (MRC/CCP4) available via FTP for bulk access.
