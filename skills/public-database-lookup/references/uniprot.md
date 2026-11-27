# UniProt REST API

## Contents
- Base URL
- Identifier handling
- Authentication
- Key Endpoints
  - 1. Search proteins
  - 2. Fetch single entry by accession
  - 3. FASTA sequence retrieval
  - 4. ID Mapping (convert between ID types)
  - 5. UniRef (clustered sequences)
  - 6. UniParc (sequence archive)
  - 7. Proteomes
  - 8. Taxonomy
- Query Syntax
- Rate Limits
- Error Format

## Base URL

```
https://rest.uniprot.org
```

## Identifier handling

UniProtKB accessions contain 6 or 10 alphanumeric characters under the official accession patterns; do not restrict them to `P`/`Q` plus five digits. Preserve the submitted accession and record the resolved primary accession when a secondary accession redirects. Isoform identifiers such as `P04637-2` add a suffix and require an endpoint that supports isoforms; do not silently strip it and return the canonical sequence.

## Authentication

No API key required. All endpoints are public.

## Key Endpoints

### 1. Search proteins

```
GET /uniprotkb/search
```

**Parameters:**

| Parameter | Type   | Description |
|-----------|--------|-------------|
| `query`   | string | **Required.** Search query using UniProt query syntax (field:value pairs, boolean operators). |
| `format`  | string | `json` (default), `tsv`, `fasta`, `xml`, `list`, `xlsx`, `obo` |
| `fields`  | string | Comma-separated list of columns to return. Key fields: `accession`, `id`, `protein_name`, `gene_names`, `organism_name`, `organism_id`, `length`, `sequence`, `cc_function`, `go_id`, `go`, `xref_pdb`, `reviewed`, `ec`, `cc_subcellular_location`, `ft_domain`, `lineage` |
| `size`    | int    | Results per page (max 500, default 25) |
| `cursor`  | string | Pagination cursor (returned in `Link` response header) |
| `sort`    | string | Sort field and direction, e.g. `gene asc`, `length desc`, `annotation_score desc` |

**Example calls** (pass the query unencoded in `params`):

```python
import time
import requests

UNIPROT = "https://rest.uniprot.org"

# Reviewed human TP53. Other example queries for the same call:
#   "(protein_name:insulin) AND (reviewed:true)"                  protein name keyword
#   "(ec:2.7.11.1) AND (organism_id:9606)"                         EC number
#   "(go:0006915) AND (organism_id:9606) AND (reviewed:true)"      Gene Ontology
r = requests.get(f"{UNIPROT}/uniprotkb/search", timeout=30, params={
    "query": "(gene:TP53) AND (organism_id:9606) AND (reviewed:true)", "format": "json",
    "fields": "accession,protein_name,gene_names,organism_name,length,cc_function", "size": 10})
r.raise_for_status()
{"total": int(r.headers["x-total-results"]), "next_page": r.links.get("next", {}).get("url"),
 "hits": [(e["primaryAccession"], e["sequence"]["length"]) for e in r.json()["results"]]}
```

**Response (JSON):**
```json
{
  "results": [
    {
      "entryType": "UniProtKB reviewed (Swiss-Prot)",
      "primaryAccession": "P04637",
      "uniProtkbId": "P53_HUMAN",
      "organism": {
        "scientificName": "Homo sapiens",
        "taxonId": 9606
      },
      "proteinDescription": {
        "recommendedName": {
          "fullName": { "value": "Cellular tumor antigen p53" }
        }
      },
      "genes": [
        {
          "geneName": { "value": "TP53" },
          "synonyms": [{ "value": "P53" }]
        }
      ],
      "sequence": {
        "value": "MEEPQSDP...",
        "length": 393,
        "molWeight": 43653,
        "crc64": "..."
      },
      "comments": [...],
      "features": [...],
      "references": [...]
    }
  ]
}
```

**Pagination:** The `Link` response header contains the next page URL with the cursor parameter. Follow it to get subsequent pages (`r.links["next"]["url"]` already carries the query); `x-total-results` holds the total count.

```python
next_url = f"{UNIPROT}/uniprotkb/search"
params = {"query": "(protein_name:insulin) AND (reviewed:true)", "fields": "accession", "format": "json", "size": 5}
accessions, pages = [], 0
while next_url and pages < 2:  # bounded for the example; size goes up to 500
    r = requests.get(next_url, params=params, timeout=30)
    r.raise_for_status()
    accessions.extend([e["primaryAccession"] for e in r.json()["results"]])
    next_url = r.links.get("next", {}).get("url")
    params = None
    pages += 1
    time.sleep(0.2)
{"total": int(r.headers["x-total-results"]), "retrieved": len(accessions), "more": next_url is not None}
```

---

### 2. Fetch single entry by accession

```
GET /uniprotkb/{accession}
```

**Parameters:**

| Parameter | Type   | Description |
|-----------|--------|-------------|
| `format`  | string | `json`, `tsv`, `fasta`, `xml`, `gff` |

**Example calls** (`/uniprotkb/P04637.fasta` returns FASTA; see section 3):

```python
r = requests.get(f"{UNIPROT}/uniprotkb/P04637", params={"format": "json"}, timeout=30)
r.raise_for_status()
entry = r.json()
{"accession": entry["primaryAccession"], "id": entry["uniProtkbId"], "length": entry["sequence"]["length"]}
```

---

### 3. FASTA sequence retrieval

Append `.fasta` to the accession or use `format=fasta`:

```python
r = requests.get(f"{UNIPROT}/uniprotkb/P04637.fasta", timeout=30)
r.raise_for_status()
single = r.text
# Batch FASTA from search (paginated like JSON search)
r = requests.get(f"{UNIPROT}/uniprotkb/search", timeout=30, params={
    "query": "(gene:BRCA1) AND (organism_id:9606) AND (reviewed:true)", "format": "fasta"})
r.raise_for_status()
{"single": single.splitlines()[0], "batch_records": r.text.count(">"), "total": r.headers.get("x-total-results")}
```

---

### 4. ID Mapping (convert between ID types)

ID mapping is a two-step async process.

**Step 1: Submit job** (form-encoded body: send it with `data={...}`)
```
POST /idmapping/run
form fields: from={dbFrom}, to={dbTo}, ids={comma-separated-ids}
```

Common `from`/`to` database names:
- `UniProtKB_AC-ID` (UniProt accession)
- `Gene_Name`
- `GeneID` (NCBI Gene / Entrez Gene)
- `Ensembl`, `Ensembl_Genomes`
- `RefSeq_Protein`
- `PDB`
- `ChEMBL`
- `EMBL-GenBank-DDBJ`
- `STRING`

Returns:
```json
{ "jobId": "abc123def456" }
```

**Step 2: Poll and retrieve results**
```
GET /idmapping/status/{jobId}
```
Poll the status response until no longer running. A finished job answers with a 303 redirect to
the results, which `requests` follows by default, so poll with `allow_redirects=False` and read
`jobStatus`. Then request
`GET /idmapping/details/{jobId}` and follow its `redirectURL` for the correct
result resource. A typical result path is:
```
GET /idmapping/results/{jobId}?format=json&size=500
```

**Example:**

Map Ensembl gene IDs to UniProt accessions (UniProt to PDB is `"from": "UniProtKB_AC-ID", "to": "PDB", "ids": "P04637,P38398"`; its `to` values are plain strings):
```python
r = requests.post(f"{UNIPROT}/idmapping/run", timeout=30, data={
    "from": "Ensembl", "to": "UniProtKB", "ids": ",".join(["ENSG00000141510", "ENSG00000012048"])})
r.raise_for_status()
job_id = r.json()["jobId"]
for attempt in range(10):  # bounded polling
    status = requests.get(f"{UNIPROT}/idmapping/status/{job_id}", allow_redirects=False, timeout=30)
    status.raise_for_status()
    job_status = status.json().get("jobStatus")
    if job_status != "NEW" and job_status != "RUNNING":
        break
    time.sleep(2)
if job_status != "FINISHED":
    raise RuntimeError(status.text[:300])
r = requests.get(f"{UNIPROT}/idmapping/details/{job_id}", timeout=30)
r.raise_for_status()
r = requests.get(r.json()["redirectURL"], timeout=30,
                 params={"format": "json", "size": 500, "fields": "accession,reviewed,gene_primary"})
r.raise_for_status()
body = r.json()
{"total": int(r.headers["x-total-results"]), "more_pages": "next" in r.links, "failedIds": body.get("failedIds", []),
 "first": [(x["from"], x["to"]["primaryAccession"]) for x in body["results"][:5]]}
```

**Response (results):**
```json
{
  "results": [
    {
      "from": "ENSG00000141510",
      "to": {
        "primaryAccession": "P04637",
        "uniProtkbId": "P53_HUMAN",
        ...
      }
    }
  ]
}
```

---

### 5. UniRef (clustered sequences)

```
GET /uniref/search?query={query}&format=json
GET /uniref/{id}
```

Cluster IDs: `UniRef100_P04637`, `UniRef90_P04637`, `UniRef50_P04637`

---

### 6. UniParc (sequence archive)

```
GET /uniparc/search?query={query}&format=json
GET /uniparc/{upi}
```

---

### 7. Proteomes

```
GET /proteomes/search?query=(organism_id:9606)&format=json
GET /proteomes/{upid}
```

Example — human reference proteome:
```python
r = requests.get(f"{UNIPROT}/proteomes/UP000005640", params={"format": "json"}, timeout=30)
r.raise_for_status()
proteome = r.json()
{"id": proteome["id"], "type": proteome["proteomeType"], "taxon": proteome["taxonomy"]["scientificName"],
 "proteins": proteome.get("proteinCount")}
```

---

### 8. Taxonomy

```
GET /taxonomy/search?query={query}&format=json
GET /taxonomy/{taxonId}
```

---

## Query Syntax

UniProt search queries support field:value syntax with boolean operators:

- `(gene:TP53)` -- gene name
- `(organism_id:9606)` -- NCBI taxonomy ID (9606 = human, 10090 = mouse)
- `(organism_name:"Homo sapiens")` -- organism name
- `(reviewed:true)` -- Swiss-Prot only (manually reviewed)
- `(protein_name:kinase)` -- protein name contains keyword
- `(ec:2.7.11.1)` -- enzyme classification
- `(go:0006915)` -- Gene Ontology term ID
- `(xref:pdb-4HHB)` -- cross-reference
- `(length:[100 TO 300])` -- sequence length range
- `(cc_disease:cancer)` -- disease involvement
- `(ft_domain:SH2)` -- domain annotation
- `(cc_subcellular_location:nucleus)` -- subcellular location
- `(date_modified:[2024-01-01 TO *])` -- modification date

Combine with `AND`, `OR`, `NOT`:
```
(gene:BRCA1) AND (organism_id:9606) AND (reviewed:true)
```

## Rate Limits

- No hard published rate limit, but excessive requests will be throttled.
- Use pagination (`size` + `cursor`) to batch results.
- Batch ID mapping jobs instead of one-at-a-time lookups.
- For large downloads, use the streaming endpoints or FTP site.
- Respect `Retry-After` headers if you receive HTTP 429.

## Error Format

```json
{
  "url": "https://rest.uniprot.org/...",
  "messages": ["Error message here"]
}
```

HTTP 400 for bad queries, 404 for not found, 429 for rate limiting, 500 for server errors.

Mapping namespaces are directional: check `https://rest.uniprot.org/configure/idmapping/fields`
for allowed `from`/`to` values. Preserve unmapped IDs and one-to-many mappings.
