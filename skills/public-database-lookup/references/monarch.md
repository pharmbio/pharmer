# Monarch Initiative API

## Base URL
```
https://api.monarchinitiative.org/v3/api
```

## Auth
No API key required.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/search?q={query}` | Text search across all entities |
| `/autocomplete?q={prefix}` | Autocomplete entity names |
| `/entity/{id}` | Entity details (gene, disease, phenotype) |
| `/association?entity={id}` | Associations for an entity |
| `/association?entity={id}&category={cat}` | Filtered associations |

## Entity ID Prefixes
- `MONDO:` — diseases (e.g. `MONDO:0007947`)
- `HP:` — phenotypes (e.g. `HP:0001250`)
- `HGNC:` — genes (e.g. `HGNC:3603`)
- `NCBIGene:` — genes (e.g. `NCBIGene:7157`)

## Association Categories
`biolink:GeneToPhenotypicFeatureAssociation`, `biolink:DiseaseToPhenotypicFeatureAssociation`, `biolink:GeneToDiseaseAssociation`

## Example Calls
CURIEs go raw in `params`; in a path (`/entity/{id}`) quote them with `requests.utils.quote(id, safe="")`.
```python
import requests

MONARCH = "https://api.monarchinitiative.org/v3/api"

# Search for Marfan syndrome
r = requests.get(f"{MONARCH}/search", params={"q": "Marfan syndrome", "limit": 5}, timeout=30)
r.raise_for_status()
search = r.json()

# Entity details for a disease
r = requests.get(f"{MONARCH}/entity/{requests.utils.quote('MONDO:0007947', safe='')}", timeout=30)
r.raise_for_status()
entity = r.json()

# Gene-to-phenotype for FBN1
r = requests.get(f"{MONARCH}/association",
                 params={"entity": "HGNC:3603", "category": "biolink:GeneToPhenotypicFeatureAssociation",
                         "limit": 10},
                 timeout=30)
r.raise_for_status()
assoc = r.json()
{"search": [(i["id"], i["name"]) for i in search["items"]],
 "entity": (entity["id"], entity["name"], entity["category"]),
 "fbn1_phenotypes": {"total": assoc["total"],
                     "first": [(a["object"], a.get("object_label")) for a in assoc["items"][:5]]}}
```

## Response Format
Paginate search/associations with `limit` and zero-based `offset`. JSON. Search: `items[]` with `id`, `name`, `category`. Associations: `items[]` with `subject`, `predicate`, `object`, `publications`.

## Rate Limits
No published limits. Be reasonable.
