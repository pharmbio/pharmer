# JASPAR (Transcription Factor Binding Profiles)

## Base URL
```
https://jaspar.elixir.no/api/v1/
```

## Auth
No auth required.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/matrix/` | List all TF binding profiles |
| `/matrix/{matrix_id}/` | Specific profile (e.g. MA0139.1 for CTCF) |
| `/matrix/?tax_id={id}&collection=CORE` | Filter by species + collection |
| `/matrix/{id}/?format=jaspar` | Profile in JASPAR format |
| `/matrix/{id}/?format=meme` | Profile in MEME format |
| `/matrix/{id}/?format=transfac` | Profile in TRANSFAC format |
| `/taxon/` | List taxonomic groups |
| `/collections/` | List collections (CORE, CNE, etc.) |

## Filter Parameters
- `tax_id` — NCBI taxonomy ID (9606 for human)
- `collection` — CORE, CNE, PHYLOFACTS, etc.
- `tf_class` — TF structural class
- `name` — TF name search
- `page`, `page_size` — pagination

## Example Calls
```python
import requests

JASPAR = "https://jaspar.elixir.no/api/v1"

# Get CTCF binding profile
r = requests.get(f"{JASPAR}/matrix/MA0139.1/", timeout=30)
r.raise_for_status()
ctcf = r.json()

# Human CORE TF profiles (paged: count, next, results)
r = requests.get(f"{JASPAR}/matrix/", params={"tax_id": 9606, "collection": "CORE", "page_size": 10}, timeout=30)
r.raise_for_status()
core = r.json()

# Get profile in MEME format (plain text)
r = requests.get(f"{JASPAR}/matrix/MA0139.1/", params={"format": "meme"}, timeout=30)
r.raise_for_status()
{"ctcf": (ctcf["name"], ctcf["class"], len(ctcf["pfm"]["A"])),
 "core": (core["count"], [m["matrix_id"] for m in core["results"]]),
 "meme_head": r.text.splitlines()[:10]}
```

## Response Format
JSON. Profiles include: `matrix_id`, `name`, `pfm` (position frequency matrix as A/C/G/T dict), `sequence_logo` URL, `species`, `class`, `family`.

## API Docs
Swagger at https://jaspar.elixir.no/api/v1/docs/

## Rate Limits
No published limits. Be reasonable.
