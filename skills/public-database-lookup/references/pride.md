# PRIDE Archive API

Public base: `https://www.ebi.ac.uk/pride/ws/archive/v3` (no key).
Use the current [OpenAPI schema](https://www.ebi.ac.uk/pride/ws/archive/v3/v3/api-docs).

| GET path | Purpose |
|---|---|
| `/projects?page=0&pageSize=5` | List projects |
| `/search/projects?keyword=alzheimer&page=0&pageSize=5` | Search projects |
| `/projects/PXD010000` | Retrieve project metadata |
| `/projects/PXD010000/files?page=0&pageSize=10` | List project files |
| `/projects/PXD010000/files/count` | File count |
| `/files/{fileAccession}` | File details |
| `/projects/count` | Project count |

`/projects` does not implement keyword search. Use `/search/projects`; its
`filter` syntax is `field==value`, with fields from the current search/facet
schema. Search supports `sortFields`, `sortDirection`, and `dateGap`.
Pagination uses zero-based `page` and `pageSize` (documented default 100).
List/search/file-list responses are JSON arrays, not a universal `results`
envelope. A single project is an object; inspect actual keys before parsing.

```python
import requests

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"

r = requests.get(f"{PRIDE}/search/projects", params={"keyword": "alzheimer", "page": 0, "pageSize": 5},
                 headers={"Accept": "application/json"}, timeout=30)
r.raise_for_status()
hits = r.json()  # JSON array of project records
r = requests.get(f"{PRIDE}/projects/PXD010000/files/count", timeout=30)
r.raise_for_status()
{"hits": [(p["accession"], p["title"][:60]) for p in hits], "PXD010000_files": r.json()}
```

The Archive API does not expose the previously suggested `/spectra`,
`/peptideevidences`, or `/proteinevidences` routes. For identified molecules and
spectra, use the linked PRIDE analysis resources or download the project files.
Retain PXD accession, assay provenance, organism and submission/publication dates;
submitted data alone do not establish peptide/protein identification confidence.
