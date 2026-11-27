# KEGG REST API

## Base URL
```python
import time
import requests

KEGG = "https://rest.kegg.jp"
```

## Auth
No API key required. Free for academic use. Commercial use requires license.

## Important: KEGG returns tab-delimited text and flat-file format, NOT JSON.

## Key Operations (URL-path-based, no query parameters)

| URL Pattern | Description |
|-------------|-------------|
| `/list/{database}` | List all entries |
| `/list/{database}/{organism}` | List entries for organism |
| `/get/{dbentries}` | Get entry data (flat-file) |
| `/get/{dbentries}/image` | Pathway image (PNG) |
| `/get/{dbentries}/kgml` | Pathway as KGML XML |
| `/find/{database}/{query}` | Search by keyword |
| `/find/{database}/{query}/formula` | Search by molecular formula |
| `/find/{database}/{value}/exact_mass` | Search by exact mass |
| `/link/{target_db}/{source_db}` | Find linked entries between databases |
| `/link/{target_db}/{dbentries}` | Links for specific IDs |
| `/conv/{target_db}/{dbentries}` | Cross-reference ID conversion |
| `/ddi/{dbentries}` | Drug-drug interactions |

Arguments are path segments: pass a user keyword or a colon-bearing ID through `requests.utils.quote(value, safe="")` (`hsa%3A10458` works), and join batch IDs with a literal `+`.

## Database Codes

| Code | Database | Example ID |
|------|----------|------------|
| `pathway` | Pathways | `hsa00010` |
| `compound` | Compounds | `C00001` |
| `drug` | Drugs | `D00001` |
| `enzyme` | Enzymes | `ec:1.1.1.1` |
| `genes`/`hsa` | Genes | `hsa:10458` |
| `disease` | Diseases | `H00001` |
| `reaction` | Reactions | `R00001` |
| `ko` | KO orthologs | `K00001` |

## Example Calls

```python
q = requests.utils.quote
calls = {
    "human_pathways": "list/pathway/hsa",                              # List human pathways
    "pathway_entry": "get/hsa00010",                                   # Get pathway entry (flat file)
    "find_name": f"find/compound/{q('aspirin', safe='')}",             # Search compounds by name
    "find_formula": "find/compound/C9H8O4/formula",                    # Search by molecular formula
    "gene_pathways": f"link/pathway/{q('hsa:10458', safe='')}",        # Find pathways for a gene
    "gene_diseases": f"link/disease/{q('hsa:672', safe='')}",          # Find diseases for a gene
    "to_pubchem": "conv/pubchem/C00001",                               # Convert KEGG to PubChem IDs (SIDs)
    "batch_get": "get/" + "+".join(["C00001", "C00002", "C00003"]),    # Multiple entries (max 10, joined with +)
    "ddi": "ddi/" + "+".join(["D00564", "D00110"]),                    # Drug-drug interactions within the set
}
summary = {}
for label, path in calls.items():
    time.sleep(0.4)  # stay under 3 calls/sec
    r = requests.get(f"{KEGG}/{path}", timeout=30)
    if r.status_code == 404:  # KEGG "not found"; this ddi pair has no CI/P interaction (2026-10-07)
        summary[label] = {"lines": 0, "status": 404}
    else:
        r.raise_for_status()
        lines = r.text.splitlines()
        summary[label] = {"lines": len(lines), "rows": [ln.split("\t") for ln in lines[:2]]}
summary
```
Flat-file `get` output separates entries with `///` lines; tab-delimited outputs split on `"\t"`.

## Response Format
Tab-delimited text for list/find/link/conv. Flat-file text for get. **No JSON support.**

## Rate Limits
KEGG requests at most 3 calls per second; pace below that and honor failures. Batch up to 10 IDs per `/get` with `+`. May return HTTP 403 if too many requests.

KEGG `conv/pubchem/...` maps to PubChem **Substance IDs (SIDs)**, not Compound IDs (CIDs). Resolve SID to CID through PubChem before joining compound properties. Official contract: https://www.kegg.jp/kegg/rest/keggapi.html
