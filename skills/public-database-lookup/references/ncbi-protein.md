# NCBI Protein API Reference

## Contents
- Overview
- Base URL
- Authentication
- Key Endpoints
  - 1. ESearch -- Search protein records
  - 2. EFetch -- Retrieve protein records
  - 3. ESummary -- Brief record summaries
  - 4. ELink -- Find related records
- Common Search Patterns
- Rate Limits

## Overview
Protein sequence records (RefSeq, GenBank, UniProt imports) accessible via NCBI E-utilities with `db=protein`.

## Base URL
```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
```

## Authentication
- No key required. Optional: `NCBI_API_KEY` raises the limit from 3 to 10 requests/s. Default to unauthenticated; see SKILL.md, **Optional API keys**, before using one.
- Optional `tool` and `email` parameters identify the caller: send a generic tool name such as `tool="public-database-lookup"` and leave out `email` unless the user gives one.

## Key Endpoints

### 1. ESearch -- Search protein records
```
GET esearch.fcgi?db=protein&term=QUERY&retmax=N&retmode=json
```
| Param | Description |
|-------|-------------|
| `term` | Search query (Entrez syntax). Fields: `[Protein Name]`, `[Organism]`, `[Accession]`, `[Gene Name]` |
| `retmax` | Max UIDs per response (default 20); use small batches and history for large sets. |
| `idtype` | Set `acc` to return accession.version IDs instead of default numeric UIDs. |
| `retstart` | Offset for pagination |
| `usehistory` | `y` to store results on server (use with large sets) |

**Example -- search human insulin:**
```python
import re
import requests

NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

r = requests.get(
    f"{NCBI_EUTILS}/esearch.fcgi",
    params={"db": "protein", "term": "insulin AND homo sapiens[Organism]", "retmax": 5, "retmode": "json"},
    timeout=30,
)
r.raise_for_status()
search = r.json()["esearchresult"]
{"count": search["count"], "ids": search["idlist"], "translation": search["querytranslation"]}
```
Response (JSON):
```json
{
  "esearchresult": {
    "count": "1523",
    "retmax": "5",
    "idlist": ["116734704", "1240286123", "110591076", ...],
    "querytranslation": "insulin AND \"Homo sapiens\"[Organism]"
  }
}
```

### 2. EFetch -- Retrieve protein records
```
GET efetch.fcgi?db=protein&id=IDS&rettype=TYPE&retmode=MODE
```
| rettype | retmode | Output |
|---------|---------|--------|
| `fasta` | `text` | FASTA sequence |
| `gp` | `text` | GenPept flat file |
| `gp` | `xml` | GenPept XML (GBSeq: `GBSet`/`GBSeq_*` elements) |
| `acc` | `text` | Accession list |
| `seqid` | `text` | SeqID list |
| `ft` | `text` | Feature table |

**Example -- fetch FASTA for NP_000198.1 (human insulin):**
```python
r = requests.get(
    f"{NCBI_EUTILS}/efetch.fcgi",
    params={"db": "protein", "id": "NP_000198.1", "rettype": "fasta", "retmode": "text"},
    timeout=30,
)
r.raise_for_status()
lines = r.text.strip().splitlines()
{"header": lines[0], "length": len("".join(lines[1:]))}
```
Response:
```
>NP_000198.1 insulin preproprotein [Homo sapiens]
MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAED
LQVGQVELGGGPGAGSLQPLALEGSLQKRGIVEQCCTSICSLYQLENYCN
```

**Example -- fetch GenPept XML for multiple IDs:**
```python
r = requests.get(
    f"{NCBI_EUTILS}/efetch.fcgi",
    params={"db": "protein", "id": "NP_000198.1,NP_001278826.1", "rettype": "gp", "retmode": "xml"},
    timeout=30,
)
r.raise_for_status()
# A few flat fields: re is enough. Use xml.etree.ElementTree for nested structure.
{"accessions": re.findall(r"<GBSeq_accession-version>(.*?)</", r.text),
 "lengths": re.findall(r"<GBSeq_length>(\d+)</", r.text)}
```

### 3. ESummary -- Brief record summaries
```
GET esummary.fcgi?db=protein&id=IDS&retmode=json
```
Returns: accession, title, organism, length, taxonomy, create/update dates.

### 4. ELink -- Find related records
```
GET elink.fcgi?dbfrom=protein&db=gene&id=NP_000198.1&retmode=json
```
Links protein to gene, nucleotide, structure, taxonomy, etc.

```python
r = requests.get(
    f"{NCBI_EUTILS}/elink.fcgi",
    params={"dbfrom": "protein", "db": "gene", "id": "NP_000198.1", "retmode": "json"},
    timeout=30,
)
r.raise_for_status()
linkset = r.json()["linksets"][0]
{"protein_uids": linkset["ids"], "links": {ls["linkname"]: ls["links"] for ls in linkset.get("linksetdbs", [])}}
```

## Common Search Patterns
Pass each expression unencoded as `params["term"]`; `requests` encodes spaces, quotes and brackets.
```
# By accession
term=NP_000198.1[Accession]

# By gene name + organism
term=BRCA1[Gene Name] AND human[Organism]

# RefSeq only
term=insulin AND srcdb_refseq[Properties]

# By sequence length range
term=100:500[Sequence Length] AND kinase[Protein Name]
```

ELink resolves protein accessions as well as numeric UIDs: the live `NP_000198.1` probe resolved UID `4557671` and Gene `3630`. Preserve both the accession version and the resolved UID in provenance.

## Rate Limits
- Without API key: 3 requests/second
- With API key: 10 requests/second
- Large batch downloads: use `usehistory=y` with `WebEnv`/`query_key`, then fetch in chunks of 500
