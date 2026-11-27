# European Nucleotide Archive (ENA) API Reference

## Contents
- Overview
- 1. ENA Portal API (Advanced Search)
  - Base URL
  - Key Endpoints
  - Result Types
- 2. ENA Browser API (Record Retrieval)
  - Base URL
  - Key Endpoints
  - Response Formats
  - Accession Types
- 3. ENA Taxonomy REST API
  - Base URL
  - Key Endpoints
- 4. ENA Cross Reference Service
  - Base URL
  - Key Endpoints
- 5. CRAM Reference Registry
  - Base URL
  - Key Endpoints
- Common Search Patterns
- Rate Limits
- Tips

## Overview
The ENA is Europe's primary nucleotide sequence repository, part of the International Nucleotide Sequence Database Collaboration (INSDC) alongside NCBI GenBank and DDBJ. It stores raw sequencing reads, assembled sequences, genome assemblies, and associated metadata. ENA provides five complementary APIs for different access patterns.

## 1. ENA Portal API (Advanced Search)

### Base URL
```python
import re
import requests

ENA_PORTAL = "https://www.ebi.ac.uk/ena/portal/api"
```

No authentication required. All endpoints are public.

### Key Endpoints

#### Search records
```
GET /search?result={result_type}&query={query}&fields={fields}&limit={N}&format={format}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `result` | string | **Required.** Data type to search. See Result Types below. |
| `query` | string | Search query using ENA query syntax. |
| `fields` | string | Comma-separated list of fields to return. Use `/returnFields` to see available fields per result type. |
| `limit` | int | Bound results explicitly; 0 or omission can request the entire result set. |
| `format` | string | `json`, `tsv` (default). |

**Query syntax:**
```
tax_id=9606 AND description="*hemoglobin*"
tax_id=9606 AND library_strategy="RNA-Seq"
accession="PRJEB40665"
scientific_name="Escherichia coli" AND dataclass="STD"
country="United Kingdom" AND first_public>2024-01-01
```

Operators: `=`, `!=`, `>`, `<`, `>=`, `<=`. Use `AND`, `OR`, `NOT`. Wildcards: `*`. Enclose values with spaces in double quotes. Pass the query exactly as written above in `params`; `requests` encodes the `=`, spaces and quotes.

**Example -- search human RNA-Seq runs:**
```python
r = requests.get(
    f"{ENA_PORTAL}/search",
    params={
        "result": "read_run",
        "query": 'tax_id=9606 AND library_strategy="RNA-Seq"',
        "fields": "run_accession,experiment_accession,sample_accession,study_accession,"
                  "instrument_platform,library_strategy,read_count,base_count",
        "limit": 5,
        "format": "json",
    },
    timeout=30,
)
r.raise_for_status()
runs = r.json()
{"returned": len(runs), "runs": [(x["run_accession"], x["study_accession"], x["read_count"]) for x in runs]}
```

**Example -- search nucleotide sequences by organism:**
```python
r = requests.get(
    f"{ENA_PORTAL}/search",
    params={
        "result": "sequence",
        "query": 'tax_id=9606 AND description="*hemoglobin*"',
        "fields": "accession,description,tax_id,scientific_name,base_count",
        "limit": 5,
        "format": "json",
    },
    timeout=90,  # wildcard description searches sometimes took over 30 s (2026-10-07)
)
r.raise_for_status()
[(x["accession"], x["base_count"], x["description"][:60]) for x in r.json()]
```

**Response:**
```json
[
  {
    "accession": "AA126503",
    "description": "zk94h05.s1 Soares_pregnant_uterus_NbHPU Homo sapiens cDNA clone ...",
    "tax_id": "9606"
  }
]
```

#### Count records
```
GET /count?result={result_type}&query={query}
```

Returns a one-column TSV: a `count` header line, then the number. With `format=json` it returns `{"count": "<n>"}`, the number as a string.

**Example:**
```python
r = requests.get(
    f"{ENA_PORTAL}/count",
    params={"result": "read_run", "query": 'tax_id=9606 AND library_strategy="RNA-Seq"', "format": "json"},
    timeout=30,
)
r.raise_for_status()
{"count": int(r.json()["count"]), "request": r.url}
```

#### List available result types
```
GET /results?format=json
```

#### List searchable fields for a result type
```
GET /searchFields?result={result_type}
```

#### List returnable fields for a result type
```
GET /returnFields?result={result_type}
```

### Result Types

| Result Type | Description |
|-------------|-------------|
| `sequence` | Nucleotide sequences |
| `coding` | Coding sequences (CDS) |
| `noncoding` | Non-coding sequences |
| `read_run` | Raw sequencing reads (runs) |
| `read_experiment` | Sequencing experiments |
| `read_study` | Studies for raw reads |
| `analysis` | Analyses |
| `analysis_study` | Studies for analyses |
| `assembly` | Genome assemblies |
| `sample` | Samples |
| `study` | Studies |
| `taxon` | Taxonomic classification |
| `wgs_set` | Genome assembly contig sets (WGS) |
| `tsa_set` | Transcriptome assembly contig sets (TSA) |
| `tls_set` | Targeted locus study contig sets (TLS) |

---

## 2. ENA Browser API (Record Retrieval)

### Base URL
```python
ENA_BROWSER = "https://www.ebi.ac.uk/ena/browser/api"
```

Use this for direct retrieval of records by accession number. Responses are XML, EMBL or FASTA text: summarize them (record type, first line, length) instead of printing the whole body.

### Key Endpoints

#### Retrieve record in XML format
```
GET /xml/{accession}
```

**Example:**
```python
# Same call for a run (SRR12345678) or a sample (ERS1234567, which comes back under
# its BioSample primary ID with the ERS accession as SECONDARY_ID).
r = requests.get(f"{ENA_BROWSER}/xml/PRJEB40665", timeout=30)
r.raise_for_status()
xml = r.text
root = re.search(r'<(\w+) accession="([^"]+)"', xml)
{"content_type": r.headers.get("Content-Type"), "chars": len(xml),
 "record": root.groups() if root else None}
```

#### Retrieve record in EMBL flat file format
```
GET /embl/{accession}
```

**Example:**
```python
r = requests.get(f"{ENA_BROWSER}/embl/AY585947", params={"lineLimit": 20}, timeout=30)
r.raise_for_status()
lines = r.text.splitlines()
{"lines": len(lines), "id_line": lines[0], "description": [ln[5:] for ln in lines if ln.startswith("DE ")]}
```

Supports `?lineLimit=N` to truncate long records.

#### Retrieve sequence in FASTA format
```
GET /fasta/{accession}
```

**Example:**
```python
r = requests.get(f"{ENA_BROWSER}/fasta/AY585947", timeout=30)
r.raise_for_status()
lines = r.text.splitlines()
{"header": lines[0], "length": len("".join(lines[1:]))}
```

### Response Formats

| Endpoint | Format | Use case |
|----------|--------|----------|
| `/xml/{accession}` | XML | Full structured metadata for studies, samples, experiments, runs |
| `/embl/{accession}` | EMBL flat file | Annotated sequences with features |
| `/fasta/{accession}` | FASTA | Raw nucleotide/protein sequences |

### Accession Types

| Prefix | Entity | Example |
|--------|--------|---------|
| `PRJEB` / `PRJNA` / `PRJDB` | Study/Project | `PRJEB40665` |
| `ERX` / `SRX` / `DRX` | Experiment | `ERX1234567` |
| `ERS` / `SRS` / `DRS` | Sample | `ERS1234567` |
| `ERR` / `SRR` / `DRR` | Run | `ERR1234567` |
| `GCA` | Genome assembly | `GCA_000001405.29` |
| Standard INSDC | Sequence | `AY585947`, `M10051` |

---

## 3. ENA Taxonomy REST API

### Base URL
```python
ENA_TAXONOMY = "https://www.ebi.ac.uk/ena/taxonomy/rest"
```

Names are path segments: quote them with `requests.utils.quote(name, safe="")` (a space becomes `%20`).

### Key Endpoints

#### Lookup by taxonomy ID
```
GET /tax-id/{taxId}
```

**Example:**
```python
r = requests.get(f"{ENA_TAXONOMY}/tax-id/9606", timeout=30)
r.raise_for_status()
taxon = r.json()
{k: taxon[k] for k in ("taxId", "scientificName", "rank", "division", "geneticCode")}
```

**Response** (every value is a string, including `taxId` and the true/false flags):
```json
{
  "taxId": "9606",
  "scientificName": "Homo sapiens",
  "commonName": "human",
  "formalName": "true",
  "rank": "species",
  "division": "HUM",
  "lineage": "Eukaryota; Metazoa; Chordata; Craniata; Vertebrata; ...; Homo; ",
  "geneticCode": "1",
  "mitochondrialGeneticCode": "2",
  "submittable": "true",
  "binomial": "true",
  "metagenome": "false",
  "otherNames": [
    "Homo sapiens Linnaeus, 1758:authority",
    "human:genbank common name"
  ]
}
```

#### Search by scientific name
```
GET /scientific-name/{name}
```

**Example:**
```python
name = requests.utils.quote("Homo sapiens", safe="")
r = requests.get(f"{ENA_TAXONOMY}/scientific-name/{name}", timeout=30)
r.raise_for_status()
[(t["taxId"], t["scientificName"], t["rank"]) for t in r.json()]
```

Returns an array of matching taxonomy records.

#### Search by common name
```
GET /any-name/{name}
```

**Example:**
```python
r = requests.get(f"{ENA_TAXONOMY}/any-name/human", timeout=30)
r.raise_for_status()
[(t["taxId"], t["scientificName"], t.get("commonName")) for t in r.json()]
```

#### Suggest names (autocomplete)
```
GET /suggest-for-submission/{partialName}
```

**Example:**
```python
partial = requests.utils.quote("Homo sap", safe="")
r = requests.get(f"{ENA_TAXONOMY}/suggest-for-submission/{partial}", timeout=30)
r.raise_for_status()
suggestions = r.json()
{"returned": len(suggestions), "first": [(t["taxId"], t["scientificName"]) for t in suggestions[:5]]}
```

---

## 4. ENA Cross Reference Service

### Base URL
```python
ENA_XREF = "https://www.ebi.ac.uk/ena/xref/rest"
```

Retrieves links between ENA records and external databases (UniProt, PDB, PubMed, etc.).

### Key Endpoints

#### Search cross-references by accession
```
GET /json/search?accession={accession}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `accession` | string | ENA accession to look up cross-references for. |
| `source` | string | Filter by source database (e.g., `UniProtKB`). |
| `target` | string | Filter by target type. |
| `limit` | int | Max results. |
| `offset` | int | Pagination offset. |

**Example:**
```python
r = requests.get(f"{ENA_XREF}/json/search", params={"accession": "A00145"}, timeout=30)
r.raise_for_status()
xrefs = r.json()
{"returned": len(xrefs), "links": [(x["Source"], x["Source Primary Accession"]) for x in xrefs[:10]]}
```

**Response:**
```json
[
  {
    "Source": "EuropePMC",
    "Source Primary Accession": "PMC12345",
    "Source Secondary Accession": "",
    "Source URL": "https://europepmc.org/...",
    "Source Secondary URL": "",
    "Target": "sequence",
    "Target Primary Accession": "A00145",
    "Target Secondary Accession": "",
    "Target URL": "https://www.ebi.ac.uk/ena/...",
    "Has Inferred": "N",
    "Inferred From": ""
  }
]
```

---

## 5. CRAM Reference Registry

### Base URL
```python
ENA_CRAM = "https://www.ebi.ac.uk/ena/cram"
```

Retrieves reference sequences used in CRAM file compression.

### Key Endpoints

#### Lookup by MD5 checksum
```
GET /md5/{md5}
```

**Example:**
```python
# rCRS mitochondrial genome (16,569 bp). A whole chromosome is far larger (GRCh38 chr1,
# 6aef897c3d6ff0c78aff06ac189178dd, is ~249 MB), so check Content-Length before reading.
r = requests.get(f"{ENA_CRAM}/md5/c68f52674c9fb33aef52dcf399755519", stream=True, timeout=30)
r.raise_for_status()
size = int(r.headers.get("Content-Length", "0"))
seq = r.text if 0 < size <= 5_000_000 else None
r.close()
{"content_type": r.headers.get("Content-Type"), "bytes": size, "head": seq[:40] if seq else None}
```

#### Lookup by SHA1 checksum
```
GET /sha1/{sha1}
```

Inspect the CRAM registry response: checksum retrieval can return raw sequence rather than FASTA. Do not pass an unverified body to a FASTA parser. Verify the checksum of the normalized sequence against the requested registry identifier.

---

## Common Search Patterns

Each pattern is the `result` and `query` for `/search` or `/count`. Pass them in `params` as written, as in the examples above.

```
# All RNA-Seq runs for a species
result=read_run&query=tax_id=9606 AND library_strategy="RNA-Seq"

# WGS assemblies for an organism
result=assembly&query=tax_id=562 AND assembly_type="primary metagenome"

# Sequences by study accession
result=sequence&query=study_accession="PRJEB40665"

# Samples from a country with collection date
result=sample&query=country="Germany" AND collection_date>=2024-01-01

# Coding sequences for a gene keyword
result=coding&query=description="*BRCA1*" AND tax_id=9606

# Count available datasets
/count?result=read_run&query=tax_id=9606

# Get metadata fields available for a result type
/returnFields?result=read_run
/searchFields?result=read_run
```

## Rate Limits

- No authentication required
- No formal published rate limit, but be courteous: avoid more than ~5 concurrent requests
- Portal `/search` has no documented `offset`. A limit can truncate results; use `/count` to check size and retrieve a complete bounded query or partition by supported indexed fields. Do not repeatedly request an ignored offset.
- For bulk downloads of sequence data (FASTQ, etc.), use ENA's FTP/Aspera services rather than the REST API

## Tips

- **ENA vs SRA**: ENA and NCBI SRA mirror each other's data (both are INSDC members). ENA accessions (ERR/ERX/ERS/PRJEB) and NCBI accessions (SRR/SRX/SRS/PRJNA) are cross-referenced. Use whichever API has the query features you need.
- **Portal API for search, Browser API for retrieval**: Use the Portal API when you need to search across many records with filters. Use the Browser API when you have a specific accession and want the full record.
- **JSON vs XML**: The Portal API returns JSON or TSV. The Browser API primarily returns XML, EMBL, or FASTA.
- **Field discovery**: Always check `/returnFields?result={type}` and `/searchFields?result={type}` to see what's available for each result type -- fields differ between result types.
- **Cross-references**: Use the xref service to find links from ENA records to UniProt, PDB, PubMed, and other databases.
