# Human Cell Atlas (HCA)

## Base URL
```
https://service.azul.data.humancellatlas.org/
```

## Auth
No auth required.

## Select the catalogue

GET `/index/catalogs` and choose `default_catalog` or an explicitly required
catalogue from `catalogs`. The live default on 2026-09-30 was `dcp60`; pin the
returned name for the entire retrieval. Do not hard-code the old `dcp2` catalogue.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/index/projects?size={n}&catalog={catalog}` | List/search projects |
| `/index/samples?size={n}&catalog={catalog}` | List/search samples |
| `/index/files?size={n}&catalog={catalog}` | List/search files |
| `/index/summary?catalog={catalog}` | Summary statistics |

## Example Calls
```python
import json
import requests

HCA_AZUL = "https://service.azul.data.humancellatlas.org"

r = requests.get(f"{HCA_AZUL}/index/catalogs", timeout=30)
r.raise_for_status()
catalog = r.json()["default_catalog"]

# List projects (filtered to lung); page 2 is the returned next URL, requested as-is
r = requests.get(f"{HCA_AZUL}/index/projects", params={"size": 5, "catalog": catalog,
                 "filters": json.dumps({"organ": {"is": ["lung"]}})}, timeout=30)
r.raise_for_status()
first = r.json()["pagination"]
page2_count = 0
if first["next"]:
    r = requests.get(first["next"], timeout=30)
    r.raise_for_status()
    page2_count = r.json()["pagination"]["count"]

# Summary stats
r = requests.get(f"{HCA_AZUL}/index/summary", params={"catalog": catalog}, timeout=30)
r.raise_for_status()
{"catalog": catalog, "projectCount": r.json()["projectCount"], "lung_projects": first["total"],
 "page2_count": page2_count}
```

Pass `filters` as a JSON string (`json.dumps`), for example `{"organ":{"is":["lung"]}}`.
Follow `pagination.next` for continuation; the API uses search-after tokens,
not a general numeric offset. Query parameters and filter names are defined in
the [OpenAPI schema](https://service.azul.data.humancellatlas.org/openapi.json).

## Response Format
JSON. `hits` array with project/sample/file metadata + pagination.

## Rate Limits
No published limits. Be reasonable.
