# PubChem PUG REST API

## Contents
- Base URL
- URL Pattern
- Key Endpoints
  - Search by name
  - Search by CID
  - Search by SMILES
  - Search by InChIKey
  - Search by InChI (POST only — InChI strings are too long for URLs)
  - Search by molecular formula
  - Property retrieval
  - Synonym lookup
  - Compound description
  - Get just CIDs from a name
  - Cross-references (patents, registry IDs)
  - Fast similarity search (synchronous CID result)
  - 2D structure image
- Rate Limits
- Error Format

## Base URL

```python
import requests

PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
```

## URL Pattern

```
/{domain}/{namespace}/{identifiers}/{operation}/{output}
```

- **domain**: `compound`, `substance`, `assay`
- **namespace**: `cid`, `name`, `smiles`, `inchi`, `inchikey`, `fastformula`
- **operation**: `record`, `property`, `synonyms`, `description`, `cids`, `xrefs`
- **output**: `JSON`, `XML`, `CSV`, `TXT`, `SDF`, `PNG`

`{identifiers}` is a path segment: quote names with `requests.utils.quote(name, safe="")`, and send SMILES and InChI as form data (`data=`) to the POST forms below instead of putting them in the path.

## Key Endpoints

### Search by name
```
GET /compound/name/{name}/JSON
```
```python
name = "aspirin"
r = requests.get(f"{PUBCHEM}/compound/name/{requests.utils.quote(name, safe='')}/JSON", timeout=30)
r.raise_for_status()
records = r.json()["PC_Compounds"]
{"records": len(records), "cid": records[0]["id"]["id"]["cid"], "request": r.url}
```

### Search by CID
```
GET /compound/cid/{cid}/JSON
```
```python
cids = [2244, 5988, 3672]  # multiple CIDs are comma-joined; a single CID is just /compound/cid/2244/JSON
r = requests.get(f"{PUBCHEM}/compound/cid/{','.join(map(str, cids))}/JSON", timeout=30)
r.raise_for_status()
[c["id"]["id"]["cid"] for c in r.json()["PC_Compounds"]]
```

### Search by SMILES
```
GET /compound/smiles/{smiles}/JSON
```
For SMILES with special characters, use POST:
```python
r = requests.post(f"{PUBCHEM}/compound/smiles/JSON",
                  data={"smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"}, timeout=30)
r.raise_for_status()
r.json()["PC_Compounds"][0]["id"]["id"]
```

### Search by InChIKey
```
GET /compound/inchikey/{inchikey}/JSON
```

### Search by InChI (POST only — InChI strings are too long for URLs)
```python
inchi = "InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)"
r = requests.post(f"{PUBCHEM}/compound/inchi/JSON", data={"inchi": inchi}, timeout=30)
r.raise_for_status()
r.json()["PC_Compounds"][0]["id"]["id"]
```

### Search by molecular formula
```
GET /compound/fastformula/{formula}/JSON
```
```python
# Without MaxRecords, C9H8O4 returned ~1,250 full records (16 MB) on 2026-10-07; use /cids/JSON for IDs only
r = requests.get(f"{PUBCHEM}/compound/fastformula/C9H8O4/JSON", params={"MaxRecords": 5}, timeout=30)
r.raise_for_status()
[c["id"]["id"]["cid"] for c in r.json()["PC_Compounds"]]
```

### Property retrieval
```
GET /compound/{namespace}/{id}/property/{property_list}/JSON
```
Properties are comma-separated. Available properties:

`MolecularFormula`, `MolecularWeight`, `ConnectivitySMILES`, `SMILES`, `InChI`, `InChIKey`, `IUPACName`, `XLogP`, `ExactMass`, `MonoisotopicMass`, `TPSA`, `Complexity`, `Charge`, `HBondDonorCount`, `HBondAcceptorCount`, `RotatableBondCount`, `HeavyAtomCount`, `CID`

Example:
```python
props = ["MolecularFormula", "MolecularWeight", "ConnectivitySMILES", "IUPACName"]
r = requests.get(f"{PUBCHEM}/compound/cid/2244/property/{','.join(props)}/JSON", timeout=30)
r.raise_for_status()
r.json()["PropertyTable"]["Properties"][0]
```

Response:
```json
{
  "PropertyTable": {
    "Properties": [
      {
        "CID": 2244,
        "MolecularFormula": "C9H8O4",
        "MolecularWeight": "180.16",
        "IUPACName": "2-acetyloxybenzoic acid",
        "ConnectivitySMILES": "CC(=O)OC1=CC=CC=C1C(O)=O"
      }
    ]
  }
}
```

### Synonym lookup
```
GET /compound/{namespace}/{id}/synonyms/JSON
```

### Compound description
```
GET /compound/cid/{cid}/description/JSON
```

### Get just CIDs from a name
```
GET /compound/name/{name}/cids/JSON
```

### Cross-references (patents, registry IDs)
```
GET /compound/cid/{cid}/xrefs/PatentID/JSON
GET /compound/cid/{cid}/xrefs/RegistryID/JSON
```

### Fast similarity search (synchronous CID result)
```
POST /compound/fastsimilarity_2d/smiles/cids/JSON
```
```python
r = requests.post(f"{PUBCHEM}/compound/fastsimilarity_2d/smiles/cids/JSON",
                  data={"smiles": "CC(=O)OC1=CC=CC=C1C(=O)O", "Threshold": 90}, timeout=30)
r.raise_for_status()
hits = r.json()["IdentifierList"]["CID"]
{"hits": len(hits), "first": hits[:10]}
```

### 2D structure image
```
GET /compound/cid/{cid}/PNG
GET /compound/cid/{cid}/PNG?image_size=300x300
```
Save binary output to a file instead of printing it:
```python
r = requests.get(f"{PUBCHEM}/compound/cid/2244/PNG", params={"image_size": "300x300"}, timeout=30)
r.raise_for_status()
out = Path("database_lookup") / "cid2244.png"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(r.content)
{"path": str(out), "bytes": len(r.content), "content_type": r.headers.get("Content-Type")}
```

## Rate Limits

- Max **5 requests per second**
- Max **400 requests per minute**
- Batch CIDs with commas; use POST (`/compound/cid/{operation}/JSON` with `data={"cid": ",".join(map(str, cids))}`) when the URL becomes long and keep batches small enough to meet time/payload limits. Endpoint-specific limits differ.
- Throttle error returns `PUGREST.ServerBusy` fault code

## Error Format

```json
{
  "Fault": {
    "Code": "PUGREST.NotFound",
    "Message": "No CID found",
    "Details": ["..."]
  }
}
```

`fastsimilarity_2d` returns `IdentifierList.CID` synchronously; do not look for an
asynchronous ListKey in a successful fast-search response. Older SMILES property
aliases may still be accepted but returned JSON keys use the current names above.
Official contract: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
