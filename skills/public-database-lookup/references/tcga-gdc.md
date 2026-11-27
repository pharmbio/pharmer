# TCGA / GDC Data Portal API

## Base URL
```
https://api.gdc.cancer.gov
```

## Auth
No auth for public data. Token needed only for controlled-access downloads.

## Key Endpoints

All search endpoints accept GET or POST (POST preferred for complex filters).

| Endpoint | Description |
|----------|-------------|
| `/projects` | List/filter cancer projects (e.g. TCGA-BRCA) |
| `/cases` | Search cases (patients/samples) |
| `/files` | Search/filter files (BAM, VCF, expression) |
| `/genes` | Search gene-level data |
| `/ssms` | Search simple somatic mutations |
| `/ssm_occurrences` | Mutation occurrences across cases |
| `/files/{uuid}` | File metadata by UUID |
| `/data/{uuid}` | Download file by UUID |

## Filter Syntax (POST body)
```json
{
  "filters": {
    "op": "in",
    "content": {"field": "cases.project.project_id", "value": ["TCGA-BRCA"]}
  },
  "fields": "file_id,file_name,data_type",
  "format": "JSON",
  "size": 10
}
```
Operators: `in`, `=`, `!=`, `>`, `<`, `>=`, `<=`, `is`, `not`, `and`, `or`

## Example Calls
```python
import json
import requests

GDC = "https://api.gdc.cancer.gov"

# List projects
r = requests.get(f"{GDC}/projects", params={"size": 5, "fields": "project_id,name,primary_site"}, timeout=30)
r.raise_for_status()
projects = r.json()["data"]["hits"]

# BRCA1 mutations (POST with the filter syntax above)
query_body = {
    "filters": {"op": "in", "content": {"field": "consequence.transcript.gene.symbol", "value": ["BRCA1"]}},
    "fields": "ssm_id,genomic_dna_change",
    "size": 5,
}
r = requests.post(f"{GDC}/ssms", json=query_body, timeout=30)
r.raise_for_status()
ssms = r.json()["data"]

# Cases in TCGA-LUAD (GET: `filters` is a JSON string; requests URL-encodes it)
filters = {"op": "in", "content": {"field": "project.project_id", "value": ["TCGA-LUAD"]}}
params = {"filters": json.dumps(filters), "size": 3, "fields": "submitter_id,disease_type"}
r = requests.get(f"{GDC}/cases", params=params, timeout=30)
r.raise_for_status()
cases = r.json()["data"]

{"projects": [p["project_id"] for p in projects],
 "brca1_ssms": {"total": ssms["pagination"]["total"], "first": [h["genomic_dna_change"] for h in ssms["hits"][:3]]},
 "luad_cases": {"total": cases["pagination"]["total"], "first": [h["submitter_id"] for h in cases["hits"]]}}
```

## Pagination
`from` (offset) and `size` (limit, max 10000). Default size is 10.

## Rate Limits
No fixed metadata rate guarantee is assumed. Honor throttling, inspect `data.pagination`, and use the GDC Data Transfer Tool for large downloads. Controlled-access authorization is file-specific; a successful public metadata search does not authorize its files.
