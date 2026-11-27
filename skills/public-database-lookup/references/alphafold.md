# AlphaFold DB (Predicted Protein Structures)

## Base URL
```
https://alphafold.ebi.ac.uk/api/
```

## Auth
No auth required.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/prediction/{uniprot_accession}` | Prediction metadata and current file URLs by UniProt accession |

## Structure File URLs (direct download)

Prefer the URLs returned by `/prediction/{uniprot_accession}` (`pdbUrl`, `cifUrl`, `bcifUrl`, `paeDocUrl`, `msaUrl`, `plddtDocUrl`, and AlphaMissense annotation URLs) instead of hardcoding a version. AlphaFold DB file names are versioned; as of the checked API response for `P00533`, `latestVersion` is `6`.

Current direct-download patterns:
```
https://alphafold.ebi.ac.uk/files/AF-{UNIPROT}-F1-model_v6.pdb
https://alphafold.ebi.ac.uk/files/AF-{UNIPROT}-F1-model_v6.cif
https://alphafold.ebi.ac.uk/files/AF-{UNIPROT}-F1-model_v6.bcif
https://alphafold.ebi.ac.uk/files/AF-{UNIPROT}-F1-predicted_aligned_error_v6.json
https://alphafold.ebi.ac.uk/files/AF-{UNIPROT}-F1-confidence_v6.json
https://alphafold.ebi.ac.uk/files/msa/AF-{UNIPROT}-F1-msa_v6.a3m
```

## Example Calls
```python
import requests

ALPHAFOLD = "https://alphafold.ebi.ac.uk/api"

# Get prediction metadata for EGFR: an array of model entities (canonical, isoforms, fragments)
acc = "P00533"
r = requests.get(f"{ALPHAFOLD}/prediction/{acc}", headers={"Accept": "application/json"}, timeout=30)
r.raise_for_status()
models = r.json()
selected = [m for m in models if m["uniprotAccession"] == acc]  # drops isoforms such as P00533-2
if len(selected) != 1:
    raise ValueError(f"{len(selected)} entities for {acc}: pick one by sequenceStart/sequenceEnd")
model = selected[0]

# Download mmCIF/PDB and PAE (predicted aligned error) from the URLs in that metadata
out_dir = Path("database_lookup")
out_dir.mkdir(parents=True, exist_ok=True)
saved = {}
for key in ("cifUrl", "pdbUrl", "paeDocUrl"):
    r = requests.get(model[key], timeout=30)
    r.raise_for_status()
    name = model[key].rsplit("/", 1)[-1]
    (out_dir / name).write_bytes(r.content)
    saved[name] = {"bytes": len(r.content), "content_type": r.headers.get("Content-Type")}
{"entities": [(m["modelEntityId"], m["sequenceStart"], m["sequenceEnd"], m["globalMetricValue"]) for m in models],
 "saved": saved}
```

## Response Format
`/prediction/{accession}` returns a JSON array. Key fields include `modelEntityId`, `latestVersion`, `allVersions`, `globalMetricValue` (mean pLDDT), `sequenceStart`, `sequenceEnd`, `taxId`, `organismScientificName`, `pdbUrl`, `cifUrl`, `bcifUrl`, `paeDocUrl`, `paeImageUrl`, `plddtDocUrl`, `msaUrl`, and AlphaMissense annotation URLs when available.

Coordinate files are available as PDB, mmCIF, and binary CIF. Prefer mmCIF/BCIF for large structures. Per-residue confidence is stored in the coordinate file B-factor column and is also available as confidence JSON. PAE is JSON.

A single accession can return multiple isoforms as well as fragments: the 2026-09-30 `P04637` response returned nine model entities. Select the intended isoform and residue interval, and retain `modelEntityId`; do not silently take the first array element.

Proteins longer than the model size limit may be represented as overlapping fragments (`F1`, `F2`, ...). Preserve fragment identifiers and residue ranges when reporting results.

## Rate Limits
No strict per-request limit is published. For many proteins, use the metadata endpoint to retrieve current URLs and pace requests conservatively. For proteome-scale or all-database retrievals, use AlphaFold DB's FTP/download pages or Google Cloud public dataset instead of looping over individual file URLs. The database contains over 200M monomer predictions, and current downloads also include selected AlphaFold complex predictions.
