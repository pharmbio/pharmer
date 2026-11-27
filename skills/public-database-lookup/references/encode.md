# ENCODE (Encyclopedia of DNA Elements)

## Base URL
```
https://www.encodeproject.org
```

## Auth
No auth required. Pass `params={"format": "json"}` or `headers={"Accept": "application/json"}`.

## Portal data objects and search support JSON; file download URLs return file content.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/search/?type=Experiment&format=json` | Search experiments |
| `/experiments/{accession}/?format=json` | Specific experiment |
| `/files/{accession}/?format=json` | File metadata |
| `/biosamples/{accession}/?format=json` | Biosample info |
| `/annotations/?format=json` | Search annotations |

## Search Parameters
- `type` — Experiment, File, Biosample, Annotation, etc.
- `assay_title` — TF ChIP-seq, Histone ChIP-seq, total RNA-seq, ATAC-seq, etc. (bare `ChIP-seq` matches nothing; use `assay_term_name=ChIP-seq`)
- `target.label` — target protein (e.g. CTCF, H3K27ac)
- `biosample_ontology.term_name` — cell type
- `limit` — results per page
- `field` — specific fields to return (a list in `params` repeats the key)

## Example Calls
```python
import requests

ENCODE = "https://www.encodeproject.org"
HEADERS = {"Accept": "application/json"}

# ChIP-seq experiments for CTCF (no hits = HTTP 404 with "total": 0)
r = requests.get(f"{ENCODE}/search/", params={"type": "Experiment", "assay_title": "TF ChIP-seq",
                 "target.label": "CTCF", "limit": 5}, headers=HEADERS, timeout=30)
if r.status_code != 404:
    r.raise_for_status()
ctcf = r.json()

# Specific experiment
r = requests.get(f"{ENCODE}/experiments/ENCSR000AAA/", headers=HEADERS, timeout=30)
r.raise_for_status()
experiment = r.json()

# Files for an experiment
r = requests.get(f"{ENCODE}/search/", params={"type": "File", "dataset": "/experiments/ENCSR000AAA/",
                 "limit": 5}, headers=HEADERS, timeout=30)
r.raise_for_status()
files = r.json()
{"ctcf": (ctcf["total"], [e["accession"] for e in ctcf["@graph"]]),
 "experiment": (experiment["accession"], experiment["assay_title"]),
 "files": (files["total"], [(f["accession"], f["output_type"]) for f in files["@graph"]])}
```

## Response Format
JSON-LD. Search: `@graph` array + `total` + `facets`. Use `frame=object` or `frame=embedded` to control depth.

## Rate Limits
No published limits. Use `limit=` and `field=` to reduce payload.

Search pagination uses `limit` and `from`; verify `@graph` length against `total`. Preserve file assembly, output_type, status and audit flags before selecting a download. Public reads need no key, while restricted/unreleased objects require authorized access.
