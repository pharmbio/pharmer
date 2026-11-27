# OpenFDA API

## Base URL
```python
import time
import requests

OPENFDA = "https://api.fda.gov"
```

## Auth
Optional free API key (240 req/min with or without). Register at https://open.fda.gov/apis/authentication/
Default to unauthenticated; see SKILL.md, **Optional API keys**, before using `OPENFDA_API_KEY`.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/drug/event.json` | Drug adverse events (FAERS) |
| `/drug/label.json` | Drug product labeling (SPL) |
| `/drug/ndc.json` | NDC directory |
| `/drug/drugsfda.json` | Drugs@FDA (approvals) |
| `/drug/enforcement.json` | Drug recalls |
| `/device/event.json` | Device adverse events |
| `/device/510k.json` | 510(k) clearances |
| `/food/event.json` | Food adverse events |
| `/food/enforcement.json` | Food enforcement |

## Query Parameters

- `search` — query using OpenFDA syntax
- `count` — count unique values for a field
- `limit` — results per request (max 1000)
- `skip` — pagination offset (max 25000)

### Search Syntax
In `params`, write spaces where openFDA URLs show `+`; `requests` sends them as `+`. A literal `+` is sent as `%2B` and matches nothing (2026-10-07: `"warfarin" AND serious:1` matched 100,731 reports, `"warfarin"+AND+serious:1` gave HTTP 404).
- Field search: `field:"value"`
- AND: `field1:value1 AND field2:value2`
- OR: `field1:value1 OR field2:value2`
- Date range: `field:[20230101 TO 20231231]`
- Wildcards: `field:aspir*`
- OpenFDA harmonized fields use `openfda.` prefix

No matches returns HTTP 404 with `{"error": {"code": "NOT_FOUND"}}`: report zero results, not an error.

## Example Calls

```python
examples = {
    # Adverse events for aspirin
    "aspirin_events": ("/drug/event.json", {"search": 'patient.drug.openfda.brand_name:"aspirin"', "limit": 5}),
    # Top adverse reactions for a drug
    "metformin_top_reactions": ("/drug/event.json", {"search": 'patient.drug.openfda.generic_name:"metformin"',
                                                     "count": "patient.reaction.reactionmeddrapt.exact"}),
    # Drug labels by generic name
    "ibuprofen_labels": ("/drug/label.json", {"search": 'openfda.generic_name:"ibuprofen"', "limit": 3}),
    # Drug recalls in date range
    "recalls_2023": ("/drug/enforcement.json", {"search": "report_date:[20230101 TO 20231231]", "limit": 10}),
    # Serious adverse events only
    "warfarin_serious": ("/drug/event.json", {"search": 'patient.drug.openfda.brand_name:"warfarin" AND serious:1',
                                              "limit": 10}),
}
summary = {}
for label, (path, params) in examples.items():
    r = requests.get(f"{OPENFDA}{path}", params=params, timeout=30)
    if r.status_code == 404 and r.json().get("error", {}).get("code") == "NOT_FOUND":
        summary[label] = {"total": 0}
    else:
        r.raise_for_status()
        body = r.json()
        if "count" in params:
            summary[label] = body["results"][:5]  # [{"term": ..., "count": ...}]
        else:
            summary[label] = {"total": body["meta"]["results"]["total"], "returned": len(body["results"])}
    time.sleep(0.3)
summary
```

## Rate Limits
| Tier | Requests/min | Requests/day |
|------|-------------|-------------|
| No API key | 240 | 1,000 |
| With API key (free) | 240 | 120,000 |

FAERS reports are not incidence estimates or proof that a drug caused an event. Preserve report versions and avoid double-counting follow-ups. OpenFDA harmonization is incomplete; a missing harmonized name is not evidence of absence.
