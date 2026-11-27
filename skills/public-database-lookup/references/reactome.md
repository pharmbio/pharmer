# Reactome Content Service REST API

## Contents
- Base URL
- Key Endpoints
  - Search (full-text across pathways, reactions, proteins)
  - Autocomplete
  - Top-level pathways for a species
  - Pathway details
  - Events contained in a pathway
  - Participants of a reaction
  - Ancestors of an event
  - Map external ID to pathways (e.g. UniProt to Reactome pathways)
  - Map external ID to reactions
  - Generic entity lookup
  - Reference entities for an event
  - All species
  - Event hierarchy for a species (large response)
- Stable ID Format
- External Resource Names for Mapping
- Rate Limits

## Base URL

```
https://reactome.org/ContentService
```

No authentication required. JSON by default.

## Key Endpoints

### Search (full-text across pathways, reactions, proteins)

```
GET /search/query?query={term}
```

Parameters:
- `query` (required) — search term (e.g. "apoptosis", "TP53", "R-HSA-109581")
- `species` — filter by species (e.g. "Homo sapiens")
- `types` — filter by type: `Pathway`, `Reaction`, `Protein`, `Complex`, `SmallMolecule`
- `cluster` — boolean, cluster results (default true)
- `rows` — page size
- `Start row` — zero-based offset. The name contains a space; use it literally in `params` (`{"Start row": 0}`) and let requests encode it.
- `Force filters=true` — keep requested filters even when no records match; the default can relax filters to obtain results. In `params`: `{"Force filters": "true"}` (literal space, no hand-encoding).

Example:
```python
import requests

REACTOME = "https://reactome.org/ContentService"

r = requests.get(f"{REACTOME}/search/query",
                 params={"query": "apoptosis", "species": "Homo sapiens", "types": "Pathway",
                         "rows": 10, "Start row": 0, "Force filters": "true"},
                 timeout=30)
r.raise_for_status()
body = r.json()
{"matches": body["numberOfMatches"],
 "groups": [(g["typeName"], g["entriesCount"], [e["stId"] for e in g["entries"][:5]]) for g in body["results"]]}
```

With `Force filters` and no match the service answers HTTP 404 (`No entries found for query`), not an empty result.

Response (live 2026-10-07: groups hold `entries` and the total is `numberOfMatches`; `name` and `summation` carry `<span class="highlighting">` markup):
```json
{
  "results": [
    {
      "typeName": "Pathway",
      "entriesCount": 192,
      "entries": [
        {
          "dbId": "109581",
          "stId": "R-HSA-109581",
          "name": "<span class=\"highlighting\" >Apoptosis</span>",
          "species": ["Homo sapiens"],
          "summation": "..."
        }
      ]
    }
  ],
  "numberOfMatches": 192
}
```

### Autocomplete
```
GET /search/suggest?query={partial_term}
```

### Top-level pathways for a species
```
GET /data/pathways/top/{species}
```
Example (the species name is a path segment, so quote it; the space becomes `%20`):
```python
species = requests.utils.quote("Homo sapiens", safe="")
r = requests.get(f"{REACTOME}/data/pathways/top/{species}", timeout=30)
r.raise_for_status()
top = r.json()
{"count": len(top), "first": [(p["stId"], p["displayName"]) for p in top[:5]]}
```

### Pathway details
```
GET /data/query/{id}
```
Where `{id}` is a stable ID like `R-HSA-109581` or a numeric dbId.

### Events contained in a pathway
```
GET /data/pathway/{id}/containedEvents
```

### Participants of a reaction
```
GET /data/participants/{id}
```

### Ancestors of an event
```
GET /data/event/{id}/ancestors
```

### Map external ID to pathways (e.g. UniProt to Reactome pathways)
```
GET /data/mapping/{resource}/{id}/pathways
```
Example — find pathways for TP53 (UniProt P04637):
```python
r = requests.get(f"{REACTOME}/data/mapping/UniProt/P04637/pathways", timeout=30)
r.raise_for_status()
pathways = r.json()
{"count": len(pathways), "first": [(p["stId"], p["displayName"]) for p in pathways[:5]]}
```

### Map external ID to reactions
```
GET /data/mapping/{resource}/{id}/reactions
```

### Generic entity lookup
```
GET /data/query/{id}
```

### Reference entities for an event
```
GET /data/participants/{id}/referenceEntities
```

### All species
```
GET /data/species/all
```

### Event hierarchy for a species (large response)
```
GET /data/eventsHierarchy/{species}
```

## Stable ID Format

`R-{species_code}-{number}`

| Code | Species |
|---|---|
| HSA | Homo sapiens |
| MMU | Mus musculus |
| RNO | Rattus norvegicus |
| DME | Drosophila melanogaster |
| CEL | C. elegans |
| SCE | S. cerevisiae |

## External Resource Names for Mapping

`UniProt`, `ChEBI`, `ENSEMBL`, `miRBase`, `GeneCards`, `NCBI`

Multiple values for same parameter: repeat the parameter (e.g. `types=Pathway&types=Reaction`); with requests, pass a list: `params={"types": ["Pathway", "Reaction"]}`.

## Rate Limits

No API key required. No formal rate limit published, but be reasonable — avoid hundreds of concurrent requests. For bulk data, use Reactome's downloadable dumps (MySQL, Neo4j, BioPAX, SBML).
