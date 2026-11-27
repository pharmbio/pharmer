# Human Phenotype Ontology (HPO)

Public term API: `https://ontology.jax.org/api/hp` (no key).

| GET path | Use |
|---|---|
| `/search?q=seizure&page=0&limit=5` | Search terms; response `terms`, `totalCount` |
| `/terms/HP:0001250` | Term details |
| `/terms/HP:0001250/parents` | Direct parents |
| `/terms/HP:0001250/children` | Direct children |
| `/terms/HP:0001250/ancestors` | All ancestors |
| `/terms/HP:0001250/descendants` | All descendants |
| `/terms?filter=HP:0001250,HP:0001249` | Selected terms |

Quote term IDs in paths (`requests.utils.quote("HP:0001250", safe="")` sends `HP%3A0001250`).
Search is zero-based and needs `q`, `page`, and `limit`; pass these and `filter` raw in `params`.
Term records include `id`, `name`, `definition`, `synonyms`, and `xrefs`.
Hierarchy endpoints return arrays. An absent term can return null.

Annotations use a separate service:
`GET https://ontology.jax.org/api/network/annotation/HP:0001250`.
Inspect its entity-specific response; there are no documented `/hpo/term/.../genes`
or `/hpo/gene/...` routes in the current term API. For bulk gene/disease analyses,
use the versioned HPO annotation downloads and preserve evidence and negation.

```python
import requests

HPO = "https://ontology.jax.org/api/hp"

r = requests.get(f"{HPO}/terms", params={"filter": "HP:0001250,HP:0001249"}, timeout=30)
r.raise_for_status()
selected = [(t["id"], t["name"]) for t in r.json()]
term_id = requests.utils.quote("HP:0001250", safe="")
r = requests.get(f"https://ontology.jax.org/api/network/annotation/{term_id}", timeout=30)
r.raise_for_status()
{"selected": selected, "annotation_counts": {k: len(v) for k, v in r.json().items() if isinstance(v, list)}}
```

Official schemas: [terms](https://ontology.jax.org/api/hp/docs/),
[annotation network](https://ontology.jax.org/api/network/docs).
