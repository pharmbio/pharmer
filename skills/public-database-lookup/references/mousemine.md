# MouseMine (Mouse Genome Informatics, InterMine-based)

## Base URL
```
https://mousemine.alliancegenome.org/mousemine/service
```
On 2026-10-07 `https://www.mousemine.org/mousemine/service` answered HTTP 302 to this host. Use it
directly: on a 302, `requests` re-sends a POST as a GET without its body.

## Auth
No auth for most queries. Free account token needed for saved lists.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/search?q={query}&format=json` | Keyword search across all objects |
| `/template/results?name={template}&op1=LOOKUP&value1={value}&format=json` | Run pre-built template query |
| `/query/results` (POST) | Run custom PathQuery (XML) |
| `/model` | Retrieve data model |
| `/templates?format=json` | Discover currently available templates and editable constraints |

## Example Calls
```python
import requests

MOUSEMINE = "https://mousemine.alliancegenome.org/mousemine/service"

# Keyword search for Brca1
r = requests.get(f"{MOUSEMINE}/search", params={"q": "Brca1", "format": "json"}, timeout=30)
r.raise_for_status()
found = r.json()

# Discover templates before constructing template/results parameters
r = requests.get(f"{MOUSEMINE}/templates", params={"format": "json"}, timeout=60)
r.raise_for_status()
templates = r.json()["templates"]

{"search_total": found.get("totalHits"),
 "first_hits": [(h["type"], h["fields"].get("symbol")) for h in found["results"][:3]],
 "n_templates": len(templates), "MFeature_GO": "MFeature_GO" in templates, "Gene_GO": "Gene_GO" in templates}
```

## Custom Query (POST)
`POST /query/results` with an `application/x-www-form-urlencoded` body: pass the PathQuery XML as
a `data=` field and `requests` encodes it. `start`/`size` page the rows; this query matches every mouse gene.
Constrain organism by `taxonId` as the templates do: on 2026-10-07 `Gene.organism.name = "Mus musculus"`
returned 0 rows with HTTP 200, and `Gene.organism.taxonId = 10090` returned mouse genes.
```python
pathquery = ('<query model="genomic" view="Gene.symbol Gene.name" sortOrder="Gene.symbol asc">'
             '<constraint path="Gene.organism.taxonId" op="=" value="10090"/></query>')
r = requests.post(f"{MOUSEMINE}/query/results", data={"query": pathquery, "format": "json", "size": 5}, timeout=60)
if r.status_code == 429:  # see Rate Limits: wait Retry-After seconds before one retry
    result = {"rate_limited": True, "retry_after_s": r.headers.get("Retry-After")}
else:
    r.raise_for_status()
    rows = r.json()["results"]
    result = {"n_rows": len(rows), "rows": rows}
result
```

## Response Format
JSON: `{"results": [...], "statusCode": 200}`. Also supports XML, TSV, CSV via `format` param.

## Rate Limits
No published limits. Be reasonable. On 2026-10-07 `/query/results` answered bursts with HTTP 429
(`"MouseMine request rate temporarily limited"`, `Retry-After: 60`) for several minutes, while the
GET search/template catalogue calls were unaffected. Space query POSTs out; do not retry in a loop.

The live template catalogue includes `MFeature_GO` (editable `SequenceFeature` lookup); `Gene_GO` is not present. Supply the template's actual constraint paths/operators and preserve the fixed organism/data-source constraints.
