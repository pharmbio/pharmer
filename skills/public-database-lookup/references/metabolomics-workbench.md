# Metabolomics Workbench REST API

## Contents
- Base URL
- Auth
- URL Structure
- Key Endpoints
  - Study Context
  - Compound Context
  - RefMet (Standardized Nomenclature)
  - Gene / Protein Context
  - Mass search
- Example Calls
- Response Format
- Rate Limits

## Base URL
```python
import time
import requests

METABOLOMICS_WORKBENCH = "https://www.metabolomicsworkbench.org/rest"
```

## Auth
No API key required. Fully public.

## URL Structure
```
/rest/{context}/{input_item}/{input_value}/{output_item}
```

Contexts: `study`, `compound`, `refmet`, `gene`, `protein`, `moverz` (`exactmass` is an input item, not a context)

Every input value is a path segment: pass names, adducts and lipid abbreviations through `requests.utils.quote(value, safe="")`.

## Key Endpoints

### Study Context
| URL Pattern | Description |
|---|---|
| `/rest/study/study_id/{ST_ID}/summary` | Study summary metadata |
| `/rest/study/study_id/{ST_ID}/metabolites` | Metabolites in a study |
| `/rest/study/study_id/{ST_ID}/analysis` | Analysis details |
| `/rest/study/study_id/{ST_ID}/factors` | Experimental factors |
| `/rest/study/study_id/{ST_ID}/data` | Named metabolite data matrix |
| `/rest/study/study_title/{keyword}/summary` | Search studies by title keyword |
| `/rest/study/analysis_id/{AN_ID}/summary` | Summary by analysis ID |

Study IDs: `ST######` (e.g., `ST000001`). Analysis IDs: `AN######`.

### Compound Context
| URL Pattern | Description |
|---|---|
| `/rest/compound/formula/{FORMULA}/all` | Search compound by molecular formula |
| `/rest/compound/pubchem_cid/{CID}/all` | Search by PubChem CID |
| `/rest/compound/hmdb_id/{HMDB_ID}/all` | Search by HMDB ID |
| `/rest/compound/kegg_id/{KEGG_ID}/all` | Search by KEGG ID |
| `/rest/compound/inchi_key/{KEY}/all` | Search by InChI key |
| `/rest/compound/regno/{REGNO}/classification` | Compound classification |
| `/rest/compound/regno/{REGNO}/molfile` | MOL file (structure) |

### RefMet (Standardized Nomenclature)
| URL Pattern | Description |
|---|---|
| `/rest/refmet/name/{NAME}/all` | Full RefMet record |
| `/rest/refmet/match/{NAME}/name` | Match name to standardized RefMet name |

### Gene / Protein Context
| URL Pattern | Description |
|---|---|
| `/rest/gene/gene_symbol/{SYMBOL}/all` | Gene info by symbol |
| `/rest/gene/gene_id/{ID}/all` | Gene info by Entrez ID |
| `/rest/protein/uniprot_id/{ID}/all` | Protein by UniProt ID |

### Mass search

The moverz input encodes library, m/z, adduct and tolerance in Daltons:
```text
/rest/moverz/MB/635.52/M+H/0.5
```
`MB` selects the Metabolomics Workbench library. Quote the adduct
(`requests.utils.quote("M+H", safe="")` sends `M%2BH`; a raw `+` also worked on 2026-10-07).
Specify the ion/adduct; a positive/negative mode label alone is not sufficient. Exact mass for a lipid abbreviation is:
```text
/rest/moverz/exactmass/PC(34:1)/M+H
```

## Example Calls

```python
q = requests.utils.quote
calls = {
    "study_summary": "study/study_id/ST000001/summary",          # Study summary
    "study_metabolites": "study/study_id/ST000001/metabolites",  # Metabolites in a study
    "title_search": f"study/study_title/{q('diabetes', safe='')}/summary",  # Search studies by title
    "formula": "compound/formula/C6H12O6/all",                   # Compounds with a formula (not unique chemical identity)
    "pubchem_cid": "compound/pubchem_cid/5793/all",              # Compound by PubChem CID
    "refmet_match": f"refmet/match/{q('alpha-D-Glucose', safe='')}/name",  # RefMet standardized name match
}
summary = {}
for label, path in calls.items():
    r = requests.get(f"{METABOLOMICS_WORKBENCH}/{path}", timeout=30)
    r.raise_for_status()
    if "json" not in r.headers.get("Content-Type", ""):
        summary[label] = {"content_type": r.headers.get("Content-Type"), "text": r.text[:200]}
    else:
        body = r.json()
        # one record is a flat dict; several are a dict of records keyed "1", "2", ... (or "Row1", ...)
        vals = list(body.values()) if isinstance(body, dict) else []
        rows = vals if vals and isinstance(vals[0], dict) else [body]
        summary[label] = {"records": len(rows), "first": dict(list(rows[0].items())[:5]) if isinstance(rows[0], dict) else rows[0]}
    time.sleep(0.5)
summary
```

The `moverz` routes 302-redirect to `/data/*.php`. On 2026-10-07, following that redirect over the
reused connection intermittently failed with `ConnectionError` (RemoteDisconnected) for quoted
paths; `headers={"Connection": "close"}` avoided it.

```python
adduct = requests.utils.quote("M+H", safe="")
# m/z search in positive mode: tab-separated text (served as text/html), header row first
r = requests.get(f"{METABOLOMICS_WORKBENCH}/moverz/MB/635.52/{adduct}/0.5",
                 headers={"Connection": "close"}, timeout=30)
r.raise_for_status()
mz_rows = [ln.split("\t") for ln in r.text.strip().splitlines()]
time.sleep(0.5)
# Exact mass search
lipid = requests.utils.quote("PC(34:1)", safe="")
r = requests.get(f"{METABOLOMICS_WORKBENCH}/moverz/exactmass/{lipid}/{adduct}",
                 headers={"Connection": "close"}, timeout=30)
r.raise_for_status()
{"mz_matches": len(mz_rows) - 1, "columns": mz_rows[0], "first": mz_rows[1:3],
 "exactmass": [ln.replace("</br>", "").strip() for ln in r.text.strip().splitlines()]}
```

## Response Format
Most record queries default to JSON. `mwtab` returns MWTab text and `molfile` returns MOL text. `/moverz/exactmass/` returns a short HTML/text result: the live PC(34:1), M+H example returned 760.585077 and C42H83NO8P. No general pagination contract is exposed; keep queries narrow and inspect the actual content type and body. An HTTP 200 can contain an unsupported-input error. Resolve names through RefMet; `compound/name` is not a supported input item.

## Rate Limits
No published limits. Be reasonable. Add 0.5-1s delay for batch calls.

Official query builder and contract: https://www.metabolomicsworkbench.org/tools/mw_rest.php
