# ClinicalTrials.gov (v2 API)

## Contents
- Base URL
- Auth
- Key Endpoints
  - API version and data freshness
  - Search studies
  - Single study by NCT ID
  - Study count
  - Field metadata
- Pagination
- Rate Limits
- Bulk download

## Base URL
```
https://clinicaltrials.gov/api/v2/
```

## Auth
No API key required. Fully public.

## Key Endpoints

### API version and data freshness
```
GET /version
```

Check `dataTimestamp` before time-sensitive retrievals to confirm the daily refresh has completed. ClinicalTrials.gov notes that data is generally refreshed Monday through Friday by 9 a.m. ET / 14:00 UTC.

ClinicalTrials.gov modernized its data ingest on August 26, 2025. For reproducible comparisons against older exports, note that some rich text markup fields and location/geopoint data may differ from the legacy pipeline.

### Search studies
```
GET /studies
```

Key parameters:
- `query.cond` — condition/disease (e.g. `breast cancer`)
- `query.intr` — intervention/treatment (e.g. `pembrolizumab`)
- `query.term` — general search terms
- `query.spons` — sponsor
- `query.id` — NCT ID
- `filter.overallStatus` — pipe-delimited: `RECRUITING|COMPLETED|ACTIVE_NOT_RECRUITING|...`
- `filter.advanced` — Essie expression, e.g. `AREA[Phase]PHASE3`; there is no `filter.phase` parameter
- `filter.geo` — `distance(lat,lon,dist)` e.g. `distance(38.89,-77.03,50mi)`
- `fields` — comma-separated field list to reduce payload
- `sort` — e.g. `LastUpdatePostDate:desc`
- `pageSize` — results per page (default 10, max 1000)
- `pageToken` — cursor for next page (from `nextPageToken` in response)
- `countTotal=true` — include total count

Example — recruiting Phase 3 breast cancer trials:
```python
import requests

CTGOV = "https://clinicaltrials.gov/api/v2"

params = {
    "query.cond": "breast cancer",
    "filter.overallStatus": "RECRUITING",  # several: "RECRUITING|ACTIVE_NOT_RECRUITING"
    "filter.advanced": "AREA[Phase]PHASE3",
    "pageSize": 5,
    "countTotal": "true",
}
r = requests.get(f"{CTGOV}/studies", params=params, timeout=30)
r.raise_for_status()
page = r.json()
nct_ids = [s["protocolSection"]["identificationModule"]["nctId"] for s in page["studies"]]

# Next page: send back the returned token unchanged
if page.get("nextPageToken"):
    params["pageToken"] = page["nextPageToken"]
    r = requests.get(f"{CTGOV}/studies", params=params, timeout=30)
    r.raise_for_status()
    nct_ids += [s["protocolSection"]["identificationModule"]["nctId"] for s in r.json()["studies"]]
{"totalCount": page["totalCount"], "retrieved": len(nct_ids), "nct_ids": nct_ids}
```

Response structure:
```json
{
  "totalCount": 1234,
  "studies": [
    {
      "protocolSection": {
        "identificationModule": {"nctId": "NCT05123456", "briefTitle": "..."},
        "statusModule": {"overallStatus": "RECRUITING"},
        "designModule": {"phases": ["PHASE3"], "enrollmentInfo": {"count": 500}},
        "conditionsModule": {"conditions": ["Breast Cancer"]},
        "eligibilityModule": {"minimumAge": "18 Years", "sex": "ALL"}
      }
    }
  ],
  "nextPageToken": "CAYQAg"
}
```

### Single study by NCT ID
```
GET /studies/{nctId}
```
Example:
```python
r = requests.get(f"{CTGOV}/studies/NCT05123456", timeout=30)
r.raise_for_status()
study = r.json()["protocolSection"]
{"nctId": study["identificationModule"]["nctId"], "status": study["statusModule"]["overallStatus"]}
```

### Study count
```
GET /studies?query.cond={condition}&filter.overallStatus=RECRUITING&pageSize=1&countTotal=true
```

Read `totalCount` from the first response. `/stats/size` accepts no search parameters and reports registry-wide statistics, not a filtered count.

### Field metadata
```
GET /studies/metadata
```

## Pagination
Uses cursor-based pagination via `pageToken` (NOT numeric offsets). Include `countTotal=true` on first request to get total.

## Rate Limits
No API key. Be reasonable — a few requests per second.

## Bulk download

Prefer the v2 `/studies` API with `pageToken` pagination for programmatic
retrieval. The former bulk URL `https://clinicaltrials.gov/AllAPIJSON.zip`
returns **404** and must not be used.

For a full-registry **XML** dump, use (a HEAD request checks it without downloading):

```python
r = requests.head("https://clinicaltrials.gov/AllPublicXML.zip", allow_redirects=True, timeout=30)
r.raise_for_status()
{"url": r.url, "content_type": r.headers.get("Content-Type"), "disposition": r.headers.get("Content-Disposition")}
```

That path redirects to `https://clinicaltrials.gov/api/legacy/public-xml?format=zip`
and returns `Content-Type: application/zip` (`ctg-public-xml.zip`). Confirm the
redirect still yields a zip before large downloads; CSV / pipe-delimited export
options are documented under ClinicalTrials.gov Data API “Download” pages when
XML is not appropriate.
