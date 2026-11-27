# dbSNP API Reference

## Contents
- Overview
- Base URLs
- Authentication
- E-utilities Endpoints (db=snp)
  - 1. ESearch -- Search SNPs
  - 2. ESummary -- SNP summaries
  - 3. EFetch -- Fetch SNP details
- Variation Services API
  - 1. Lookup variant by rsID
  - 2. Lookup variant by SPDI notation
  - 3. Lookup variant by HGVS
  - 4. Multiple rsIDs
- Common E-utilities Search Patterns
- Rate Limits

## Overview
SNP and variant data. Accessible via two APIs: NCBI E-utilities (`db=snp`) for search/metadata, and the NCBI Variation Services REST API for detailed variant annotations.

## Base URLs
```
E-utilities:  https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
Variation API: https://api.ncbi.nlm.nih.gov/variation/v0/
```

## Authentication
- **E-utilities**: no key required. Optional: `NCBI_API_KEY` raises the limit from 3 to 10 requests/s. Default to unauthenticated; see SKILL.md, **Optional API keys**, before using one.
- **Variation API**: No auth required. Rate limits apply (undocumented; be respectful, ~1-2 req/sec).

---

## E-utilities Endpoints (db=snp)

### 1. ESearch -- Search SNPs
```
GET esearch.fcgi?db=snp&term=QUERY&retmax=N&retmode=json
```

**Example -- search SNPs in BRCA1 gene:**
```python
import requests

NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
NCBI_VARIATION = "https://api.ncbi.nlm.nih.gov/variation/v0"

r = requests.get(
    f"{NCBI_EUTILS}/esearch.fcgi",
    params={"db": "snp", "term": "BRCA1[Gene Name] AND homo sapiens[Organism]", "retmax": 5, "retmode": "json"},
    timeout=30,
)
r.raise_for_status()
search = r.json()["esearchresult"]
{"count": search["count"], "rsids": ["rs" + uid for uid in search["idlist"]],
 "translation": search["querytranslation"]}
```
Response:
```json
{
  "esearchresult": {
    "count": "12847",
    "idlist": ["80357713", "80357508", ...]
  }
}
```
Note: IDs returned are rs numbers without the "rs" prefix.

### 2. ESummary -- SNP summaries
```
GET esummary.fcgi?db=snp&id=IDS&retmode=json
```

**Example -- get summary for rs334 (sickle cell variant):**
```python
r = requests.get(
    f"{NCBI_EUTILS}/esummary.fcgi",
    params={"db": "snp", "id": "334", "retmode": "json"},
    timeout=30,
)
r.raise_for_status()
doc = r.json()["result"]["334"]
{k: doc.get(k) for k in ("snp_id", "chr", "chrpos", "genes", "clinical_significance")}
```
Response includes: `snp_id`, `chr`, `chrpos`, `genes`, `clinical_significance`, `global_mafs`, `docsum`.

### 3. EFetch -- Fetch SNP details
```
GET efetch.fcgi?db=snp&id=IDS&rettype=json&retmode=text
```
Note: EFetch for dbSNP returns JSON with `rettype=json`. Also supports XML with `retmode=xml`.

---

## Variation Services API

### 1. Lookup variant by rsID
```
GET /variation/v0/refsnp/{rsid}
```

**Example:**
```python
r = requests.get(f"{NCBI_VARIATION}/refsnp/334", timeout=30)
r.raise_for_status()
snp = r.json()
primary = snp["primary_snapshot_data"]  # absent for merged or withdrawn RS records
ptlp = [p for p in primary["placements_with_allele"] if p["is_ptlp"]]  # primary top-level placement
{"refsnp_id": snp["refsnp_id"], "variant_type": primary["variant_type"],
 "alleles": [a["hgvs"] for a in ptlp[0]["alleles"]]}
```
Response (JSON, abbreviated):
```json
{
  "refsnp_id": "334",
  "create_date": "2000/09/19",
  "primary_snapshot_data": {
    "placements_with_allele": [...],
    "allele_annotations": [...],
    "support": [...]
  },
  "present_obs_movements": [
    {
      "component_ids": [{"type": "clinvar", "value": "..."}],
      "observation": {
        "seq_id": "NC_000011.10",
        "position": 5227001,
        "deleted_sequence": "T",
        "inserted_sequence": "A"
      }
    }
  ]
}
```

### 2. Lookup variant by SPDI notation
```
GET /variation/v0/spdi/{spdi}/rsids
```
SPDI format: `SeqID:Position:Deletion:Insertion` (Position is 0-based). Quote the `{spdi}` and
`{hgvs}` path segments with `requests.utils.quote(value, safe="")` (they contain `:` and `>`).

**Example:**
```python
spdi = "NC_000011.10:5227001:T:A"  # rs334 T>A on GRCh38
r = requests.get(f"{NCBI_VARIATION}/spdi/{requests.utils.quote(spdi, safe='')}/rsids", timeout=30)
r.raise_for_status()
r.json()["data"]
```

### 3. Lookup variant by HGVS
```
GET /variation/v0/hgvs/{hgvs}/contextuals
```

**Example:**
```python
hgvs = "NC_000011.10:g.5227002T>A"  # HGVS positions are 1-based
r = requests.get(f"{NCBI_VARIATION}/hgvs/{requests.utils.quote(hgvs, safe='')}/contextuals", timeout=30)
r.raise_for_status()
r.json()["data"]["spdis"]
```

### 4. Multiple rsIDs

The current Variation Services schema has no `/refsnp/batch` route. For a small
set, issue bounded individual `/refsnp/{numeric_id}` requests. For large sets,
use [dbSNP bulk JSON](https://ftp.ncbi.nlm.nih.gov/snp/latest_release/JSON/).
RefSNP records can be merged or withdrawn; inspect status and resolve current IDs
before using `primary_snapshot_data`.

## Common E-utilities Search Patterns
Pass each expression unencoded as `params["term"]`; `requests` encodes spaces, quotes and brackets.
```
# By rs number
term=334[RS ID]

# Clinical significance
term=pathogenic[Clinical Significance] AND BRCA1[Gene Name]

# By chromosome position (GRCh38)
term=11[Chromosome] AND 5227002:5227002[Base Position]

# By variant type
term=missense[Function Class] AND TP53[Gene Name]

# By global minor allele frequency
term=0.01:0.05[Global MAF]
```

## Rate Limits
- E-utilities: 3 req/sec (no key), 10 req/sec (with key)
- Variation Services API: No published limit; recommend 1-2 req/sec
