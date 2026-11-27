# Ensembl REST API

## Contents
- Base URL
- Authentication
- Common Headers
- Key Endpoints
  - 1. Gene lookup by symbol
  - 2. Gene/feature lookup by Ensembl ID
  - 3. Batch lookup (POST, up to 1000 IDs)
  - 4. Sequence retrieval
  - 5. Sequence by region
  - 6. Variant annotation (VEP -- Variant Effect Predictor)
  - 7. Variant (known variants by rsID)
  - 8. Overlap / features in a region
  - 9. Cross-references (Xrefs)
  - 10. Comparative genomics -- Homology
  - 11. Regulatory features
  - 12. Species information
  - 13. Assembly information
  - 14. Phenotype by gene
  - 15. LD (Linkage Disequilibrium)
- Common Species Names
- Rate Limits
- Error Format
- Tips

## Base URL

```python
import requests

ENSEMBL = "https://rest.ensembl.org"
ENSEMBL_GRCH37 = "https://grch37.rest.ensembl.org"  # GRCh37 (hg19) archive
ENSEMBL_HEADERS = {"Accept": "application/json"}    # see Common Headers
```

The Ensembl Genomes (plants, fungi, bacteria, protists, metazoa) use the same base:
Ensembl Genomes was merged into the main REST API.

## Authentication

No API key required. All endpoints are public.

## Common Headers

The API uses content negotiation. Every GET sends `headers={"Accept": "application/json"}`
(`ENSEMBL_HEADERS`), or `params={"content-type": "application/json"}`; a GET has no body, so it
needs no `Content-Type`. Other options such as `expand=1` are ordinary `params` entries, not
`;expand=1` appended to the URL. Batch POSTs pass the body with `json=`, which sets
`Content-Type: application/json`, and keep the `Accept` header.

Path values with characters outside `A-Za-z0-9._-` (regions such as `17:7661779..7662000:1`,
HGVS such as `17:g.7675088C>G`) go through `requests.utils.quote(value, safe="")`.

## Key Endpoints

### 1. Gene lookup by symbol

```
GET /lookup/symbol/{species}/{symbol}
```

| Parameter   | Type   | Description |
|------------|--------|-------------|
| `species`   | string | **Required.** Species name (e.g., `homo_sapiens`, `mus_musculus`). |
| `symbol`    | string | **Required.** Gene symbol (e.g., `TP53`, `BRCA1`). |
| `expand`    | int    | Set to `1` to include transcripts, translations, exons. |

**Example:**
```python
r = requests.get(f"{ENSEMBL}/lookup/symbol/homo_sapiens/TP53", headers=ENSEMBL_HEADERS, timeout=30)
r.raise_for_status()
tp53 = r.json()

r = requests.get(f"{ENSEMBL}/lookup/symbol/homo_sapiens/BRCA1", params={"expand": 1},
                 headers=ENSEMBL_HEADERS, timeout=30)
r.raise_for_status()
brca1 = r.json()
{"TP53": [tp53["id"], tp53["assembly_name"], tp53["seq_region_name"], tp53["start"], tp53["end"]],
 "BRCA1": [brca1["id"], len(brca1["Transcript"])]}
```

**Response:**
```json
{
  "id": "ENSG00000141510",
  "display_name": "TP53",
  "description": "tumor protein p53 [Source:HGNC Symbol;Acc:HGNC:11998]",
  "species": "homo_sapiens",
  "object_type": "Gene",
  "biotype": "protein_coding",
  "assembly_name": "GRCh38",
  "seq_region_name": "17",
  "start": 7661779,
  "end": 7687538,
  "strand": -1,
  "source": "ensembl_havana",
  "logic_name": "ensembl_havana_gene_homo_sapiens",
  "version": 16,
  "Transcript": [...]
}
```

---

### 2. Gene/feature lookup by Ensembl ID

```
GET /lookup/id/{id}
```

| Parameter | Type   | Description |
|-----------|--------|-------------|
| `id`      | string | **Required.** Ensembl stable ID (gene, transcript, protein, exon). |
| `expand`  | int    | Set to `1` to include child objects (transcripts for genes, etc.). |
| `db_type` | string | Database type: `core`, `otherfeatures`, `cdna`, `rnaseq`. |

**Example:**
```python
# A transcript (ENST00000269305) or protein (ENSP00000269305) ID uses the same call;
# object_type ("Transcript", "Translation") and Parent tell them apart.
r = requests.get(f"{ENSEMBL}/lookup/id/ENSG00000141510", params={"expand": 1},
                 headers=ENSEMBL_HEADERS, timeout=30)
r.raise_for_status()
gene = r.json()
{"id": gene["id"], "object_type": gene["object_type"], "transcripts": len(gene["Transcript"]),
 "canonical": [t["id"] for t in gene["Transcript"] if t.get("is_canonical")]}
```

---

### 3. Batch lookup (POST, up to 1000 IDs)

```python
r = requests.post(
    f"{ENSEMBL}/lookup/id",
    json={"ids": ["ENSG00000141510", "ENSG00000012048", "ENSG00000157764"]},
    headers=ENSEMBL_HEADERS,
    timeout=30,
)
r.raise_for_status()
{stable_id: (rec["display_name"] if rec else None) for stable_id, rec in r.json().items()}
```

**Example response:** Returns a map keyed by ID:
```json
{
  "ENSG00000141510": {
    "id": "ENSG00000141510",
    "display_name": "TP53",
    ...
  },
  "ENSG00000012048": { ... }
}
```

---

### 4. Sequence retrieval

```
GET /sequence/id/{id}
```

| Parameter     | Type   | Description |
|--------------|--------|-------------|
| `id`          | string | Ensembl stable ID (gene, transcript, or protein). |
| `type`        | string | `genomic`, `cdna`, `cds`, `protein`. Default varies by object type. |
| `format`      | string | `fasta`; select JSON with the content-type/Accept header. |
| `expand_3prime` | int  | Expand 3' end by N bases. |
| `expand_5prime` | int  | Expand 5' end by N bases. |
| `mask`        | string | `soft` (lowercase repeats) or `hard` (N-mask repeats). |

**Examples:** protein, CDS, and genomic sequence with flanks as JSON, then FASTA.
```python
seqs = {}
for label, seq_id, opts in [
    ("protein", "ENSP00000269305", {}),
    ("cds", "ENST00000269305", {"type": "cds"}),
    ("genomic+flanks", "ENSG00000141510", {"type": "genomic", "expand_5prime": 1000, "expand_3prime": 500}),
]:
    r = requests.get(f"{ENSEMBL}/sequence/id/{seq_id}", params=opts, headers=ENSEMBL_HEADERS, timeout=30)
    r.raise_for_status()
    seqs[label] = [r.json()["molecule"], len(r.json()["seq"])]

# FASTA: ask for it in the Accept header
r = requests.get(f"{ENSEMBL}/sequence/id/ENSP00000269305", headers={"Accept": "text/x-fasta"}, timeout=30)
r.raise_for_status()
seqs["fasta_header"] = r.text.splitlines()[0]
seqs
```

**Response (JSON):**
```json
{
  "id": "ENSP00000269305",
  "seq": "MEEPQSDPSVEPPLSQETFSDL...",
  "molecule": "protein",
  "desc": "chromosome:GRCh38:17:7661779:7687538:-1"
}
```

---

### 5. Sequence by region

```
GET /sequence/region/{species}/{region}
```

Region format: `chromosome:start..end` or `chromosome:start..end:strand`

**Example:**
```python
region = requests.utils.quote("17:7661779..7662000:1", safe="")
r = requests.get(f"{ENSEMBL}/sequence/region/homo_sapiens/{region}", headers=ENSEMBL_HEADERS, timeout=30)
r.raise_for_status()
{"id": r.json()["id"], "length": len(r.json()["seq"])}
```

---

### 6. Variant annotation (VEP -- Variant Effect Predictor)

**By HGVS notation:**
```
GET /vep/{species}/hgvs/{hgvs_notation}
```

**Example:**
```python
# Transcript HGVS (ENST00000269305.9:c.817C>T) works the same way; quote either form.
hgvs = requests.utils.quote("17:g.7675088C>G", safe="")
r = requests.get(f"{ENSEMBL}/vep/homo_sapiens/hgvs/{hgvs}", params={"CADD": 1},
                 headers=ENSEMBL_HEADERS, timeout=30)
r.raise_for_status()
v = r.json()[0]
canon = [t for t in v["transcript_consequences"] if t["transcript_id"] == "ENST00000269305"]
{"allele_string": v["allele_string"], "most_severe": v["most_severe_consequence"],
 "ENST00000269305": {k: canon[0].get(k) for k in ("gene_symbol", "amino_acids", "protein_start", "cadd_phred")} if canon else None}
```

`CADD=1` is how you get `cadd_phred`. Without it the field is absent.
Verified 2026-09-11: `17:g.7675088C>G` is `missense_variant` / TP53 /
`cadd_phred` **29.4**. The older worked example `17:g.7674220G>A` is
HTTP 400 — the reference at 7674220 is `C`, not `G`.

**By genomic region:**
```
GET /vep/{species}/region/{region}/{allele}
```

**Example:**
```python
region = requests.utils.quote("17:7675088-7675088:1", safe="")
r = requests.get(f"{ENSEMBL}/vep/homo_sapiens/region/{region}/G", params={"CADD": 1},
                 headers=ENSEMBL_HEADERS, timeout=30)
r.raise_for_status()
v = r.json()[0]
{"allele_string": v["allele_string"], "most_severe": v["most_severe_consequence"],
 "transcripts": len(v["transcript_consequences"])}
```

The path carries the **alt** only. VEP reads the reference from the
assembly. `17:7675088-7675088:1/G` returns `allele_string: C/G` even if
you thought the ref was `A`. Compare `allele_string` to the alleles you
meant, or use `/hgvs/` (which 400s on a wrong ref).

**By rsID:**
```
GET /vep/{species}/id/{rsid}
```

**Example:**
```python
# rs699 works the same way (drop CADD when you only need consequences).
r = requests.get(f"{ENSEMBL}/vep/homo_sapiens/id/rs28934578", params={"CADD": 1},
                 headers=ENSEMBL_HEADERS, timeout=30)
r.raise_for_status()
v = r.json()[0]
{"allele_string": v["allele_string"], "most_severe": v["most_severe_consequence"],
 "transcripts": len(v["transcript_consequences"]),
 "alt_alleles": sorted({t["variant_allele"] for t in v["transcript_consequences"]})}
```

`rs28934578` is multi-allelic (`C/A/G/T`). `most_severe_consequence` is
one label across **every** transcript (117 here, vs 39 on the single-alt
region call). Do not quote it as the consequence of one allele.

**VEP Response:**
```json
[
  {
    "input": "17:g.7675088C>G",
    "assembly_name": "GRCh38",
    "seq_region_name": "17",
    "start": 7675088,
    "end": 7675088,
    "strand": 1,
    "allele_string": "C/G",
    "most_severe_consequence": "missense_variant",
    "transcript_consequences": [
      {
        "gene_id": "ENSG00000141510",
        "gene_symbol": "TP53",
        "transcript_id": "ENST00000269305",
        "biotype": "protein_coding",
        "consequence_terms": ["missense_variant"],
        "impact": "MODERATE",
        "amino_acids": "R/P",
        "codons": "cGc/cCc",
        "protein_start": 175,
        "sift_prediction": "deleterious",
        "sift_score": 0.0,
        "cadd_phred": 29.4
      }
    ],
    "colocated_variants": [
      {
        "id": "rs28934578",
        "frequencies": { ... },
        "clin_sig": ["pathogenic"]
      }
    ]
  }
]
```

**Batch VEP (POST, up to 200 variants):**
```python
r = requests.post(
    f"{ENSEMBL}/vep/homo_sapiens/region",
    json={"variants": ["17 7675088 7675088 C/G 1", "7 140753336 140753336 A/T 1"], "CADD": 1},
    headers=ENSEMBL_HEADERS,
    timeout=30,
)
r.raise_for_status()
[{"input": v["input"], "most_severe": v["most_severe_consequence"],
  "cadd_phred": sorted({t["cadd_phred"] for t in v["transcript_consequences"] if "cadd_phred" in t})}
 for v in r.json()]
```

Add `CADD=1` as a query parameter on GET or in the POST body when you
need CADD annotations. Record the available CADD model/release and assembly.
Scores from other aggregators can differ by model, release or build; compare
like-for-like values (`myvariant.md`).

---

### 7. Variant (known variants by rsID)

```
GET /variation/{species}/{rsid}
```

**Example:**
```python
r = requests.get(f"{ENSEMBL}/variation/homo_sapiens/rs699", headers=ENSEMBL_HEADERS, timeout=30)
r.raise_for_status()
var = r.json()
{"name": var["name"], "MAF": var.get("MAF"), "clinical_significance": var.get("clinical_significance"),
 "mappings": [[m["location"], m["allele_string"], m.get("ancestral_allele")] for m in var["mappings"]]}
```

**Response:**
```json
{
  "name": "rs699",
  "source": "Variants (including SNPs and indels) imported from dbSNP",
  "mappings": [
    {
      "seq_region_name": "1",
      "start": 230710048,
      "end": 230710048,
      "strand": 1,
      "allele_string": "A/G",
      "assembly_name": "GRCh38",
      "location": "1:230710048-230710048"
    }
  ],
  "MAF": 0.35,
  "minor_allele": "G",
  "clinical_significance": [],
  "synonyms": [],
  "ancestral_allele": "A"
}
```

2026-10-07: rs699 returned `MAF` and `minor_allele` as `null`, and `ancestral_allele` (`G`) sat
inside each `mappings` entry rather than at the top level. Read these fields with `.get()` and
take allele frequencies from a population source.

---

### 8. Overlap / features in a region

```
GET /overlap/region/{species}/{region}?feature={type}
```

| Parameter | Type   | Description |
|-----------|--------|-------------|
| `region`  | string | Format: `chr:start-end`. |
| `feature` | string | One or more of: `gene`, `transcript`, `cds`, `exon`, `repeat`, `simple`, `misc`, `variation`, `somatic_variation`, `structural_variation`, `regulatory`, `motif`, `chipseq`, `constrained`. Can repeat parameter for multiple. |

**Example -- get all genes and regulatory features in a region:**
```python
# A list repeats the parameter (feature=gene&feature=regulatory); one type is just "gene".
region = requests.utils.quote("17:7660000-7690000", safe="")
r = requests.get(f"{ENSEMBL}/overlap/region/homo_sapiens/{region}",
                 params={"feature": ["gene", "regulatory"]}, headers=ENSEMBL_HEADERS, timeout=30)
r.raise_for_status()
features = r.json()
regulatory = [(x["id"], x.get("description")) for x in features if x["feature_type"] == "regulatory"]
{"genes": [(g["id"], g.get("external_name"), g["biotype"]) for g in features if g["feature_type"] == "gene"],
 "regulatory_count": len(regulatory), "regulatory_first": regulatory[:5]}
```

---

### 9. Cross-references (Xrefs)

```
GET /xrefs/id/{id}
```

**Example:**
```python
r = requests.get(f"{ENSEMBL}/xrefs/id/ENSG00000141510", headers=ENSEMBL_HEADERS, timeout=30)
r.raise_for_status()
gene_xrefs = r.json()

# Swiss-Prot accessions hang off the translation, not the gene (see the note below)
r = requests.get(f"{ENSEMBL}/xrefs/id/ENSP00000269305", headers=ENSEMBL_HEADERS, timeout=30)
r.raise_for_status()
protein_xrefs = r.json()
{"gene": {db: [x["primary_id"] for x in gene_xrefs if x["dbname"] == db][:5]
          for db in ("HGNC", "EntrezGene", "Uniprot_gn")},
 "protein": [x["primary_id"] for x in protein_xrefs if x["dbname"] == "Uniprot/SWISSPROT"]}
```

Returns links to external databases (HGNC, UniProt, NCBI Gene, RefSeq, etc.).

**Response:**
```json
[
  {
    "primary_id": "11998",
    "display_id": "TP53",
    "dbname": "HGNC",
    "db_display_name": "HGNC Symbol"
  },
  {
    "primary_id": "P04637",
    "display_id": "P53_HUMAN",
    "dbname": "Uniprot/SWISSPROT"
  },
  {
    "primary_id": "7157",
    "display_id": "TP53",
    "dbname": "EntrezGene"
  }
]
```

2026-10-07: for the gene ID, HGNC's `primary_id` is `HGNC:11998`, and UniProt appears only as
`Uniprot_gn` (16 accessions, reviewed and unreviewed mixed). `Uniprot/SWISSPROT` (`P04637`) is
attached to the translation, so query `/xrefs/id/ENSP00000269305` for it.

**Xrefs by symbol:**
```
GET /xrefs/symbol/{species}/{symbol}
```

**Example:**
```python
# This took 4 s to over 60 s on 2026-10-07 (54 s on a rerun), hence the longer timeout
r = requests.get(f"{ENSEMBL}/xrefs/symbol/homo_sapiens/TP53", headers=ENSEMBL_HEADERS, timeout=120)
r.raise_for_status()
[(x["id"], x["type"]) for x in r.json()]
```

---

### 10. Comparative genomics -- Homology

```
GET /homology/id/{species}/{id}
```

| Parameter     | Type   | Description |
|--------------|--------|-------------|
| `id`          | string | Ensembl gene ID. |
| `type`        | string | `orthologues`, `paralogues`, `projections`, `all`. |
| `target_species` | string | Filter to specific species (e.g., `mus_musculus`). |
| `target_taxon`   | int    | Filter to NCBI taxon ID. |
| `sequence`    | string | `none`, `cdna`, `protein`. Include aligned sequences. |

**Example -- get mouse orthologs of human TP53:**
```python
r = requests.get(f"{ENSEMBL}/homology/id/homo_sapiens/ENSG00000141510",
                 params={"type": "orthologues", "target_species": "mus_musculus"},
                 headers=ENSEMBL_HEADERS, timeout=30)
r.raise_for_status()
homologies = r.json()["data"][0]["homologies"]
[(h["type"], h["target"]["id"], h["target"]["species"], h["target"]["perc_id"]) for h in homologies]
```

**Response:**
```json
{
  "data": [
    {
      "id": "ENSG00000141510",
      "homologies": [
        {
          "type": "ortholog_one2one",
          "target": {
            "id": "ENSMUSG00000059552",
            "species": "mus_musculus",
            "protein_id": "ENSMUSP00000073359",
            "perc_id": 77.8,
            "perc_pos": 86.0
          },
          "source": {
            "id": "ENSG00000141510",
            "species": "homo_sapiens",
            "protein_id": "ENSP00000269305"
          },
          "method_link_type": "ENSEMBL_ORTHOLOGUES",
          "dn_ds": 0.15
        }
      ]
    }
  ]
}
```

**Homology by symbol:**
```
GET /homology/symbol/{species}/{symbol}
```

**Example:**
```python
r = requests.get(f"{ENSEMBL}/homology/symbol/homo_sapiens/TP53",
                 params={"type": "orthologues", "target_species": "mus_musculus"},
                 headers=ENSEMBL_HEADERS, timeout=120)  # slow endpoint, see below
r.raise_for_status()
data = r.json()["data"]
[(d["id"], [h["target"]["id"] for h in d["homologies"]]) for d in data]
```

2026-10-07: `/homology/symbol` took 45-105 s, against 8-16 s for `/homology/id` on the same gene.
Resolve the symbol with `/lookup/symbol` first and query `/homology/id` when speed matters.

---

### 11. Regulatory features

The current REST catalogue no longer lists the older `/regulatory/species/.../id/...`
lookup. Use the current Ensembl regulatory data/download documentation and
release-specific feature identifiers; do not assume an ENSR identifier from an
older release resolves through the live API. The overlap endpoint's supported
feature types are release-dependent.

### 12. Species information

```
GET /info/species
```

Returns all available species with assembly info.

---

### 13. Assembly information

```
GET /info/assembly/{species}
```

**Example:**
```python
r = requests.get(f"{ENSEMBL}/info/assembly/homo_sapiens", headers=ENSEMBL_HEADERS, timeout=30)
r.raise_for_status()
asm = r.json()
{"assembly_name": asm["assembly_name"], "karyotype": asm.get("karyotype"),
 "top_level_regions": len(asm["top_level_region"])}
```

Returns chromosome names, lengths, assembly name (GRCh38), coordinate system, etc.

---

### 14. Phenotype by gene

```
GET /phenotype/gene/{species}/{gene}
```

**Example:**
```python
# 443 records for TP53; this took about 30 s on 2026-10-07
r = requests.get(f"{ENSEMBL}/phenotype/gene/homo_sapiens/TP53", headers=ENSEMBL_HEADERS, timeout=60)
r.raise_for_status()
phenotypes = r.json()
{"returned": len(phenotypes), "first": [(p.get("description"), p.get("source")) for p in phenotypes[:5]]}
```

---

### 15. LD (Linkage Disequilibrium)

```
GET /ld/{species}/pairwise/{rsid1}/{rsid2}?population_name={pop}
```

**Example:**
```python
r = requests.get(f"{ENSEMBL}/ld/homo_sapiens/pairwise/rs699/rs4762",
                 params={"population_name": "1000GENOMES:phase_3:CEU"}, headers=ENSEMBL_HEADERS, timeout=30)
r.raise_for_status()
[{k: x.get(k) for k in ("variation1", "variation2", "population_name", "r2", "d_prime")} for x in r.json()]
```

---

## Common Species Names

| Species | API Name |
|---------|----------|
| Human | `homo_sapiens` |
| Mouse | `mus_musculus` |
| Rat | `rattus_norvegicus` |
| Zebrafish | `danio_rerio` |
| Fruit fly | `drosophila_melanogaster` |
| Chicken | `gallus_gallus` |
| Dog | `canis_lupus_familiaris` |
| Pig | `sus_scrofa` |

## Rate Limits

- **15 requests per second** for general users (no API key).
- Use the returned rate-limit headers; there is no documented public API-key registration workflow for a higher quota.
- Requests exceeding the limit receive HTTP 429 with a `Retry-After` header.
- Batch endpoints (POST) count as a single request -- use them to reduce call count.
- Max 1000 IDs per batch POST for `/lookup/id`.
- Max 200 variants per batch POST for VEP.
- Rate limit headers are returned: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

## Error Format

```json
{
  "error": "ID 'ENSG999' not found"
}
```

HTTP 400 for bad requests, 404 for not found, 429 for rate limiting, 503 for service unavailable.

2026-10-07: the service intermittently answered HTTP 500/503 with an HTML page (not this JSON),
or timed out. Check `r.headers.get("Content-Type")` before parsing, then wait a few seconds and
retry once.

## Tips

- Always send `headers={"Accept": "application/json"}` (or `params={"content-type": "application/json"}`) on GET requests -- the default is XML/HTML.
- Use the GRCh37 base URL (`grch37.rest.ensembl.org`) if you need hg19 coordinates.
- The `/lookup/symbol` endpoint is the fastest way to go from gene symbol to Ensembl ID.
- For VEP, the HGVS endpoint is most convenient for single variants; the region POST endpoint is best for batch.
- Combine `/xrefs/id` with gene IDs to cross-reference to UniProt, NCBI Gene, HGNC, and other databases.
