# NCBI Taxonomy API Reference

## Contents
- Overview
- Base URL
- Authentication
- Key Endpoints
  - 1. ESearch -- Search taxonomy by name
  - 2. EFetch -- Retrieve full taxonomy records
  - 3. ESummary -- Brief taxonomy summaries
  - 4. ELink -- Cross-link taxonomy to other databases
- Common Search Patterns
- Useful Cross-references
- Rate Limits

## Overview
Taxonomic classification data (names, lineages, ranks) for all organisms in NCBI databases. Accessible via E-utilities with `db=taxonomy`.

## Base URL
```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
```

## Authentication
- No key required. Optional: `NCBI_API_KEY` raises the limit from 3 to 10 requests/s. Default to unauthenticated; see SKILL.md, **Optional API keys**, before using one.
- Optional `tool` and `email` parameters identify the caller: send a generic tool name such as `tool="public-database-lookup"` and leave out `email` unless the user gives one.

## Key Endpoints

### 1. ESearch -- Search taxonomy by name
```
GET esearch.fcgi?db=taxonomy&term=QUERY&retmode=json
```
| Param | Description |
|-------|-------------|
| `term` | Organism name, common name, or taxid. Fields: `[Scientific Name]`, `[Common Name]`, `[All Names]`, `[Rank]` |
| `retmax` | Max IDs returned (default 20) |

**Example -- search by scientific name:**
```python
import re
import requests

NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

r = requests.get(
    f"{NCBI_EUTILS}/esearch.fcgi",
    params={"db": "taxonomy", "term": "Homo sapiens[Scientific Name]", "retmode": "json"},
    timeout=30,
)
r.raise_for_status()
search = r.json()["esearchresult"]
{"count": search["count"], "ids": search["idlist"]}
```
Response:
```json
{
  "esearchresult": {
    "count": "1",
    "idlist": ["9606"]
  }
}
```

**Example -- search by common name:**
```python
r = requests.get(
    f"{NCBI_EUTILS}/esearch.fcgi",
    params={"db": "taxonomy", "term": "dog[Common Name]", "retmode": "json"},
    timeout=30,
)
r.raise_for_status()
r.json()["esearchresult"]["idlist"]
```

### 2. EFetch -- Retrieve full taxonomy records
```
GET efetch.fcgi?db=taxonomy&id=TAXIDS&retmode=xml
```
Note: Taxonomy EFetch only supports XML output.

**Example -- fetch human taxonomy (taxid 9606):**
```python
r = requests.get(
    f"{NCBI_EUTILS}/efetch.fcgi",
    params={"db": "taxonomy", "id": "9606", "retmode": "xml"},
    timeout=30,
)
r.raise_for_status()
# re is enough for these flat fields. The first <ScientificName>/<Rank> are the taxon's own;
# later ones belong to the ancestor <Taxon> nodes inside <LineageEx>.
{"name": re.search(r"<ScientificName>(.*?)</", r.text).group(1),
 "rank": re.search(r"<Rank>(.*?)</", r.text).group(1),
 "lineage": re.search(r"<Lineage>(.*?)</", r.text).group(1)}
```
Response (abbreviated XML):
```xml
<TaxaSet>
  <Taxon>
    <TaxId>9606</TaxId>
    <ScientificName>Homo sapiens</ScientificName>
    <OtherNames>
      <CommonName>human</CommonName>
    </OtherNames>
    <Rank>species</Rank>
    <Division>Primates</Division>
    <GeneticCode><GCId>1</GCId><GCName>Standard</GCName></GeneticCode>
    <MitoGeneticCode><MGCId>2</MGCId><MGCName>Vertebrate Mitochondrial</MGCName></MitoGeneticCode>
    <Lineage>cellular organisms; Eukaryota; Opisthokonta; Metazoa; ... ; Hominidae; Homo</Lineage>
    <LineageEx>
      <Taxon><TaxId>131567</TaxId><ScientificName>cellular organisms</ScientificName><Rank>no rank</Rank></Taxon>
      <Taxon><TaxId>2759</TaxId><ScientificName>Eukaryota</ScientificName><Rank>superkingdom</Rank></Taxon>
      <!-- ... each ancestor node ... -->
    </LineageEx>
  </Taxon>
</TaxaSet>
```

### 3. ESummary -- Brief taxonomy summaries
```
GET esummary.fcgi?db=taxonomy&id=TAXIDS&retmode=json
```
**Example -- multiple taxa:**
```python
r = requests.get(
    f"{NCBI_EUTILS}/esummary.fcgi",
    params={"db": "taxonomy", "id": "9606,10090,7227", "retmode": "json"},
    timeout=30,
)
r.raise_for_status()
result = r.json()["result"]
{uid: [result[uid]["scientificname"], result[uid]["rank"]] for uid in result["uids"]}
```
Response includes: lowercase JSON keys `scientificname`, `commonname`, `rank`, `division`, `taxid`, `genus`, `species` (XML uses different capitalization).

### 4. ELink -- Cross-link taxonomy to other databases
```
GET elink.fcgi?dbfrom=taxonomy&db=protein&id=9606&term=insulin
```
Find all protein records for a given taxid, optionally filtered by keyword.

## Common Search Patterns
Pass each expression unencoded as `params["term"]`; `requests` encodes spaces, quotes and brackets.
```
# All species under a genus
term=Drosophila[Next Level] AND species[Rank]

# Search Taxonomy by taxid directly
term=9606[Taxonomy ID]

# By rank
term=Mammalia[Scientific Name] AND class[Rank]

# Taxonomy subtree search
term=9605[Subtree]
```

`txid9606[Organism:exp]` is a sequence-database search expression, not a Taxonomy field. Discover Taxonomy search fields with `einfo.fcgi?db=taxonomy&retmode=json`; resolve scientific names to taxids before subtree searches.

## Useful Cross-references
| Link | Description |
|------|-------------|
| `taxonomy_protein` | All proteins for a taxon |
| `taxonomy_gene` | All genes for a taxon |
| `taxonomy_nuccore` | All nucleotide records for a taxon |
| `taxonomy_genome` | Genome assemblies for a taxon |

## Rate Limits
- Without API key: 3 requests/second
- With API key: 10 requests/second
- EFetch supports multiple taxids in a single call (comma-separated)
