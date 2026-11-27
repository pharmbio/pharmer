# ClinVar API Reference

## Contents
- Base URLs
- Authentication
- Rate Limits
- Key Endpoints
  - 1. Search ClinVar (esearch)
  - 2. Fetch ClinVar Records (esummary)
  - 3. Full Record (efetch)
  - 4. Resolve HGVS/SPDI before searching ClinVar
  - 5. ClinVar VCV/RCV Direct Access
- Useful Search Qualifiers
- Response Format
- esummary Response Key Fields
- Notes

## Base URLs
- **NCBI E-utilities**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`
- **ClinVar web API (VCV)**: `https://www.ncbi.nlm.nih.gov/clinvar`
- **NCBI Variation Services**: `https://api.ncbi.nlm.nih.gov/variation/v0`

## Authentication
- E-utilities: no key required. Optional: `NCBI_API_KEY` raises the limit from 3 to 10 requests/s. Default to unauthenticated; see SKILL.md, **Optional API keys**, before using one.

## Rate Limits
- Without API key: 3 req/sec
- With API key: 10 req/sec

## Key Endpoints

### 1. Search ClinVar (esearch)
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=clinvar&term={query}&retmode=json
```
Example — search for BRCA1 pathogenic variants:
```python
import requests

NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

r = requests.get(
    f"{NCBI_EUTILS}/esearch.fcgi",
    params={"db": "clinvar", "term": 'BRCA1[gene] AND "clinsig pathogenic"[Properties]',
            "retmode": "json", "retmax": 10},
    timeout=30,
)
r.raise_for_status()
search = r.json()["esearchresult"]
# an unknown field tag silently becomes [All Fields]; confirm it in the translation
{"count": search["count"], "ids": search["idlist"], "translation": search["querytranslation"]}
```
Returns JSON with `idlist` of ClinVar Variation IDs.

### 2. Fetch ClinVar Records (esummary)
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=clinvar&id={id_list}&retmode=json
```
Example:
```python
r = requests.get(
    f"{NCBI_EUTILS}/esummary.fcgi",
    params={"db": "clinvar", "id": "37088,37087", "retmode": "json"},
    timeout=30,
)
r.raise_for_status()
result = r.json()["result"]
summary = {}
for uid in result["uids"]:
    doc = result[uid]
    if "error" in doc:  # an unavailable ID comes back as {"uid": ..., "error": ...}
        summary[uid] = {"error": doc["error"]}
    else:
        gc = doc["germline_classification"]
        summary[uid] = {"title": doc["title"], "germline": gc["description"],
                        "review_status": gc["review_status"]}
summary
```
Returns JSON with clinical significance, variant name, gene, conditions, review status.

### 3. Full Record (efetch)
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=clinvar&id={id}&rettype=vcv&is_variationid&retmode=xml
```
Note: ClinVar efetch returns **XML only** (no JSON for efetch). `is_variationid` is a flag without a value; send it as `"is_variationid": ""` in `params`.

### 4. Resolve HGVS/SPDI before searching ClinVar

NCBI Variation Services normalizes variants; it has no `/clinvar` suffix endpoint.
Use `GET https://api.ncbi.nlm.nih.gov/variation/v0/hgvs/{hgvs}/contextuals`,
then `/spdi/{spdi}/rsids`, quoting each path segment with `requests.utils.quote(value, safe="")`.
Search ClinVar with the resolved rsID (or a validated HGVS expression) using ESearch. An rsID can represent multiple alternate alleles:
compare accession, assembly, position and alleles in the ClinVar record.
SPDI positions are zero-based; HGVS genomic positions are one-based.

### 5. ClinVar VCV/RCV Direct Access
```
GET https://www.ncbi.nlm.nih.gov/clinvar/variation/{variation_id}/?redir=vcv
```
This returns HTML. For programmatic access, use E-utilities or the Variation Services API.

## Useful Search Qualifiers
- `[gene]` — gene symbol (e.g., `BRCA1[gene]`)
- `[Properties]` — classification: `"clinsig pathogenic"`, `"clinsig likely pathogenic"`, `"clinsig benign"`, `"clinsig vus"`
- `[molcons]` — molecular consequence, e.g. `"missense variant"[molcons]`, `"frameshift variant"[molcons]`
- `[revstat]` — review status, e.g. `"criteria provided, single submitter"[revstat]`, `"reviewed by expert panel"[revstat]`
- `[dis]` — disease/phenotype name, not an exact match (e.g. `autism[dis]`)

Live check 2026-10-07: `[clinical_significance]`, `[molecular_consequence]`, `[review_status]` and
`[condition]` are not ClinVar search fields; Entrez silently turns them into `[All Fields]` (or finds
nothing). Field tags are listed by `einfo.fcgi?db=clinvar` and the ClinVar help page.

## Response Format
- esearch/esummary: JSON (with `retmode=json`)
- efetch: XML only for ClinVar
- Variation Services: JSON

## esummary Response Key Fields
```json
{
  "result": {
    "37088": {
      "uid": "37088",
      "title": "NM_003238.6(TGFB2):c.687C>A (p.Cys229Ter)",
      "germline_classification": {
        "description": "Pathogenic",
        "last_evaluated": "2025/09/08 00:00",
        "review_status": "criteria provided, single submitter",
        "fda_recognized_database": "",
        "trait_set": [
          {
            "trait_xrefs": [
              {
                "db_source": "MedGen",
                "db_id": "C3553762"
              },
              {
                "db_source": "MONDO",
                "db_id": "MONDO:0013897"
              },
              {
                "db_source": "OMIM",
                "db_id": "614816"
              }
            ],
            "trait_name": "Loeys-Dietz syndrome 4"
          }
        ]
      },
      "genes": [
        {
          "symbol": "TGFB2",
          "geneid": "7042",
          "strand": "+",
          "source": "submitted"
        }
      ]
    }
  }
}
```

Somatic clinical impact and oncogenicity are separate classifications; inspect
`somatic_clinical_impact` and `oncogenicity` when present. Do not conflate these
with germline classification or discard conflicting submissions.

## Notes
- Combine esearch + esummary for search-then-fetch workflows.
- For bulk downloads, use ClinVar FTP: https://ftp.ncbi.nlm.nih.gov/pub/clinvar/
