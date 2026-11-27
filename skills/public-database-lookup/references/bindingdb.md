# BindingDB REST API

## Contents
- Base URLs
- Auth
- Response Format
- Key Endpoints
- Endpoint Details
  - Get ligands for a single target
  - Get ligands for multiple targets
  - Get ligands by PDB structure
  - Find targets for a compound (similarity search)
- Rate Limits
- Notes

## Base URLs
```python
import time
import requests

BINDINGDB_REST = "https://bindingdb.org/rest"
# https://bindingdb.org/axis2/services/BDBService/ is the documented getTargetByCompound base,
# but it returned HTTP 404 on 2026-10-07; the official example and live calls use BINDINGDB_REST.
```

## Auth
No API key required. Fully open and free.

## Response Format
Default is XML. Add `"response": "application/json"` to `params` on any endpoint for JSON. The JSON wrapper keys are spelled `getLinds...Response` (sic).

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/rest/getLigandsByUniprot` | Ligands for a single protein target |
| `/rest/getLigandsByUniprots` | Ligands for multiple protein targets |
| `/rest/getLigandsByPDBs` | Ligands by PDB structure IDs |
| `/rest/getTargetByCompound` (documented as `/axis2/services/BDBService/getTargetByCompound`) | Targets for a compound (SMILES similarity) |

## Endpoint Details

### Get ligands for a single target
```
GET https://bindingdb.org/rest/getLigandsByUniprot?uniprot={UNIPROT_ID};{IC50_cutoff_nM}&response=application/json
```
- `uniprot` — UniProt ID followed by `;` and affinity cutoff in nM
- Returns monomerIDs, SMILES, affinity types (IC50, Ki, Kd), and values
- Returns empty string if UniProt ID not found

Example:
```python
# ";" inside the value is sent as %3B, which BindingDB accepts
r = requests.get(f"{BINDINGDB_REST}/getLigandsByUniprot",
                 params={"uniprot": "P35355;100", "response": "application/json"}, timeout=60)
r.raise_for_status()
body = r.json()["getLindsByUniprotResponse"] if r.text.strip() else {}  # empty body: see Notes
{"empty_body": not body, "hits": body.get("bdb.hit", 0), "first": body.get("bdb.affinities", [])[:3]}
```

### Get ligands for multiple targets
```
GET https://bindingdb.org/rest/getLigandsByUniprots?uniprot={IDs}&cutoff={nM}&response=application/json
```
- `uniprot` — Comma-separated UniProt IDs
- `cutoff` — Affinity cutoff in nM
- Returns empty string if no matching IDs

Example:
```python
time.sleep(1)
r = requests.get(f"{BINDINGDB_REST}/getLigandsByUniprots",
                 params={"uniprot": ",".join(["P00176", "P00183"]), "cutoff": 10000,
                         "response": "application/json"}, timeout=60)
r.raise_for_status()
rows = r.json()["getLindsByUniprotsResponse"]["affinities"] if r.text.strip() else []
{"empty_body": not r.text.strip(), "rows": len(rows), "first": rows[:2]}
```

### Get ligands by PDB structure
```
GET https://bindingdb.org/rest/getLigandsByPDBs?pdb={PDBs}&cutoff={nM}&identity={percent}&response=application/json
```
- `pdb` — Comma-separated PDB IDs
- `cutoff` — Affinity cutoff in nM
- `identity` — Sequence identity cutoff (percent, e.g. 92)

Example:
```python
time.sleep(1)
r = requests.get(f"{BINDINGDB_REST}/getLigandsByPDBs",
                 params={"pdb": ",".join(["1Q0L", "3ANM"]), "cutoff": 100, "identity": 92,
                         "response": "application/json"}, timeout=60)
r.raise_for_status()
rows = r.json()["getLindsByPDBsResponse"]["affinities"] if r.text.strip() else []
{"empty_body": not r.text.strip(), "rows": len(rows), "targets": sorted(set(x["query"] for x in rows)), "first": rows[:2]}
```

### Find targets for a compound (similarity search)
```
GET https://bindingdb.org/rest/getTargetByCompound?smiles={SMILES}&cutoff={similarity}&response=application/json
```
- `smiles` — Compound SMILES, raw (`params=` encodes it)
- `cutoff` — Tanimoto similarity cutoff (decimal, e.g. 0.85)
- Returns similar compounds with their protein targets and affinities

Example (this SMILES returned 0 hits on 2026-10-07; celecoxib returned 7):
```python
time.sleep(1)
r = requests.get(f"{BINDINGDB_REST}/getTargetByCompound",
                 params={"smiles": "CCC[N+](C)(C)CCn1nncc1COc1cc(=O)n(C)c2ccccc12", "cutoff": 0.85,
                         "response": "application/json"}, timeout=60)
r.raise_for_status()
body = r.json()["getLindsByUniprotResponse"] if r.text.strip() else {}
{"empty_body": not body, "hits": body.get("bdb.hit", 0),
 "first": [{k: a.get(k) for k in ("bdb.target", "bdb.species", "bdb.affinity_type", "bdb.affinity")}
           for a in body.get("bdb.affinities", [])[:3]]}
```

## Rate Limits
No documented limit. Keep requests to ~1 per second as a courtesy.

## Notes
- An empty 200 body is the documented "not found" answer, but on 2026-10-07 valid queries (P35355, 1Q0L) also intermittently came back empty: retry once after a pause before reporting zero ligands
- The API surface is small (4 endpoints) but focused on binding affinity data
- For compound-name search, resolve to SMILES first via PubChem, then use `getTargetByCompound`
- For bulk data access, use downloadable TSV/SDF files from https://www.bindingdb.org/bind/chemsearch/marvin/Download.jsp

Official endpoint contract: https://www.bindingdb.org/rwd/bind/BindingDBRESTfulAPI.jsp
