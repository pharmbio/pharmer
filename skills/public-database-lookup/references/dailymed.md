# DailyMed (NIH/NLM Drug Labels)

## Base URL
```python
import time
import requests

DAILYMED = "https://dailymed.nlm.nih.gov/dailymed/services"
```

## Auth
No API key required.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `v2/spls.json?drug_name={name}` | Search drug labels by name |
| `v2/spls/{setid}.json` | Get label metadata by SetID |
| `v2/spls/{setid}/ndcs.json` | NDC codes for a label |
| `v2/spls/{setid}/media.json` | Images/media for a label |
| `v2/drugnames.json?drug_name={prefix}` | Drug name autocomplete |
| `v2/drugclasses.json?drug_class_name={name}` | Search by pharmacologic class |
| `v2/rxcuis.json?rxcui={rxcui}` | Query RxNorm CUIs |
| `v2/spls.json?ndc={ndc_code}` | Find labels by NDC code |

## Additional filters for `/v2/spls.json`
- `drug_class_code` and `drug_class_coding_system` — pharmacologic class code and terminology; discover codes via `/drugclasses.json` and pass its `codingSystem` too (on 2026-10-07 it was `2.16.840.1.113883.6.345`; `drug_class_code` alone matched 0 labels)
- `labeler` — manufacturer name
- `page` / `pagesize` — pagination (max 100)

## Example Calls

```python
# Search metformin labels
r = requests.get(f"{DAILYMED}/v2/spls.json", params={"drug_name": "metformin"}, timeout=30)
r.raise_for_status()
labels = r.json()
time.sleep(0.5)
# Drug name autocomplete (substring match: "ator" also hits "LABORATORY")
r = requests.get(f"{DAILYMED}/v2/drugnames.json", params={"drug_name": "ator"}, timeout=30)
r.raise_for_status()
names = r.json()
{"metformin_labels": labels["metadata"]["total_elements"],
 "first": [(d["setid"], d["title"][:60]) for d in labels["data"][:3]],
 "ator_names": names["metadata"]["total_elements"], "names_first": [d["drug_name"] for d in names["data"][:5]]}
```

```python
# Search by pharmacologic class (drugclasses name filters gave HTTP 500 on 2026-10-07: match locally)
r = requests.get(f"{DAILYMED}/v2/drugclasses.json", params={"pagesize": 100, "page": 1}, timeout=30)
r.raise_for_status()
cls = [c for c in r.json()["data"] if c["name"] == "5-alpha Reductase Inhibitor"][0]
time.sleep(0.5)
r = requests.get(f"{DAILYMED}/v2/spls.json", params={"drug_class_code": cls["code"],
                 "drug_class_coding_system": cls["codingSystem"], "pagesize": 5}, timeout=30)
r.raise_for_status()
by_class = r.json()
time.sleep(0.5)
# Full label XML (SPL content with sections): save it to a file, don't print it
setid = by_class["data"][0]["setid"]
r = requests.get(f"{DAILYMED}/v2/spls/{setid}.xml", timeout=30)
r.raise_for_status()
out = Path("database_lookup") / f"dailymed_{setid}.xml"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(r.content)
{"class": cls, "labels_in_class": by_class["metadata"]["total_elements"],
 "xml": {"path": str(out), "bytes": len(r.content), "content_type": r.headers.get("Content-Type")}}
```

## Response Format
```json
{
  "metadata": {
    "total_elements": 12,
    "elements_per_page": 10,
    "current_page": 1,
    "total_pages": 2
  },
  "data": [
    {
      "published_date": "2024-01-15",
      "title": "METFORMIN HYDROCHLORIDE tablet",
      "setid": "b03f295f-..."
    }
  ]
}
```

## Rate Limits
No published limits. Be reasonable.
