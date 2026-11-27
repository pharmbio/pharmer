# Human Protein Atlas (HPA)

## Base URL
```
https://www.proteinatlas.org
```

## Auth
No API key required.

## Key Endpoints

| Purpose | URL Pattern |
|---|---|
| Gene data by Ensembl ID | `/{ENSEMBL_ID}.json` |
| Search | `/search/{QUERY}`; use the result page Download control for XML/TSV/JSON |

## Example Calls

```python
import requests

HPA = "https://www.proteinatlas.org"

# Gene data by Ensembl ID
r = requests.get(f"{HPA}/ENSG00000141510.json", timeout=30)
r.raise_for_status()
gene = r.json()

# Search: returns an HTML results page; quote free-text queries as a path segment
s = requests.get(f"{HPA}/search/{requests.utils.quote('TP53', safe='')}", timeout=30)
s.raise_for_status()
{"gene": gene["Gene"], "uniprot": gene["Uniprot"], "rna_tissue": gene["RNA tissue specificity"],
 "search": (s.headers.get("Content-Type"), len(s.content))}
```

## Response Format (JSON, gene endpoint)
```json
{
  "Gene": "TP53",
  "Gene synonym": ["p53", "LFS1"],
  "Ensembl": "ENSG00000141510",
  "Gene description": "tumor protein p53",
  "Uniprot": ["P04637"],
  "Chromosome": "17",
  "Protein class": ["Transcription factors"],
  "RNA tissue specificity": "Low tissue specificity",
  "Subcellular location": ["Nucleoplasm"],
  "Pathology prognostics": [...]
}
```

## Bulk Downloads
For large-scale work, use TSV files from https://www.proteinatlas.org/about/download:
- `normal_tissue.tsv` — IHC tissue expression
- `rna_tissue_consensus.tsv` — RNA consensus
- `subcellular_location.tsv`
- `pathology.tsv` — cancer prognostics

## Rate Limits
No published limits. Be reasonable. Prefer bulk downloads for large queries.
