# gnomAD (Genome Aggregation Database) API Reference

## Contents
- Overview
- API Type: GraphQL
- Key Queries
  - Variant lookup by variant ID
  - Gene lookup
  - Variants in a gene
  - Variants in a region
  - Transcript lookup
- Dataset values
- Population frequency fields
- Response example (illustrative counts, not a current frequency estimate)
- Rate Limits
- Notes

## Overview
gnomAD aggregates exome and genome sequencing data to provide allele frequencies
and variant annotations across diverse populations.

## API Type: GraphQL
- **Endpoint**: `https://gnomad.broadinstitute.org/api`
- **Method**: POST with JSON body containing GraphQL query (`requests.post(GNOMAD, json={"query": ..., "variables": {...}})`)
- **Auth**: None required (public, unauthenticated)
- **Response format**: JSON (`data` wrapper with GraphQL structure)
- **Variable types** (schema, 2026-10-07): `dataset: DatasetId!` (enum, e.g. `gnomad_r4`), `reference_genome: ReferenceGenomeId!` (`GRCh37`/`GRCh38`), `variantId: String`, `gene_symbol: String`, `transcript_id: String!`, `chrom: String!`, `start`/`stop: Int!`. Enum values are sent as plain strings in `variables`. Check `body.get("errors")`: GraphQL errors arrive with HTTP 200.

## Key Queries

### Variant lookup by variant ID
Variant IDs use format: `{chrom}-{pos}-{ref}-{alt}` with **1-based positions in the build of the selected dataset**. An rsID can identify multiple alleles; resolve the exact reference/alternate allele before querying. The example below is the GRCh38 G>A allele at rs11591147, not the more common G>T allele.

```python
import time
import requests

GNOMAD = "https://gnomad.broadinstitute.org/api"

query = """
query Variant($variantId: String!, $dataset: DatasetId!) {
  variant(variantId: $variantId, dataset: $dataset) {
    variant_id rsids chrom pos ref alt exome { ac an af } genome { ac an af }
  }
}
"""
variables = {"variantId": "1-55039974-G-A", "dataset": "gnomad_r4"}
r = requests.post(GNOMAD, json={"query": query, "variables": variables}, timeout=30)
r.raise_for_status()
body = r.json()
if body.get("errors"):
    raise RuntimeError(body["errors"])
body["data"]["variant"]
```

### Gene lookup
```python
time.sleep(1)  # ~1 request/second (see Rate Limits)
query = "query Gene($symbol: String!, $ref: ReferenceGenomeId!) { gene(gene_symbol: $symbol, reference_genome: $ref) { gene_id symbol chrom start stop strand } }"
r = requests.post(GNOMAD, json={"query": query, "variables": {"symbol": "BRCA1", "ref": "GRCh38"}}, timeout=30)
r.raise_for_status()
body = r.json()
if body.get("errors"):
    raise RuntimeError(body["errors"])
body["data"]["gene"]
```

### Variants in a gene
`variants` takes only `dataset` (no paging), so one response holds every variant in the gene
(4,544 for PCSK9 in `gnomad_r4` on 2026-10-07). Summarize it; do not print it whole.
```python
time.sleep(1)
query = """
query GeneVariants($symbol: String!, $ref: ReferenceGenomeId!, $dataset: DatasetId!) {
  gene(gene_symbol: $symbol, reference_genome: $ref) {
    variants(dataset: $dataset) { variant_id consequence rsids exome { ac an af } genome { ac an af } }
  }
}
"""
variables = {"symbol": "PCSK9", "ref": "GRCh38", "dataset": "gnomad_r4"}
r = requests.post(GNOMAD, json={"query": query, "variables": variables}, timeout=60)
r.raise_for_status()
body = r.json()
if body.get("errors"):
    raise RuntimeError(body["errors"])
gene_variants = body["data"]["gene"]["variants"]
{"n_variants": len(gene_variants), "first": [v["variant_id"] for v in gene_variants[:3]]}
```

### Variants in a region
```python
time.sleep(1)
query = """
query RegionVariants($chrom: String!, $start: Int!, $stop: Int!, $ref: ReferenceGenomeId!, $dataset: DatasetId!) {
  region(chrom: $chrom, start: $start, stop: $stop, reference_genome: $ref) {
    variants(dataset: $dataset) { variant_id rsids consequence exome { ac af } genome { ac af } }
  }
}
"""
# PCSK9 spans 1:55039447-55064852 (GRCh38); this test window is 101 bp around rs11591147
variables = {"chrom": "1", "start": 55039924, "stop": 55040024, "ref": "GRCh38", "dataset": "gnomad_r4"}
r = requests.post(GNOMAD, json={"query": query, "variables": variables}, timeout=60)
r.raise_for_status()
body = r.json()
if body.get("errors"):
    raise RuntimeError(body["errors"])
region_variants = body["data"]["region"]["variants"]
{"n_variants": len(region_variants), "first": [v["variant_id"] for v in region_variants[:3]]}
```

### Transcript lookup
```python
time.sleep(1)
query = "query Transcript($id: String!, $ref: ReferenceGenomeId!) { transcript(transcript_id: $id, reference_genome: $ref) { transcript_id gene_id chrom start stop strand } }"
r = requests.post(GNOMAD, json={"query": query, "variables": {"id": "ENST00000357654", "ref": "GRCh38"}}, timeout=30)
r.raise_for_status()
body = r.json()
if body.get("errors"):
    raise RuntimeError(body["errors"])
body["data"]["transcript"]
```

## Dataset values
- `gnomad_r4` -- gnomAD v4 (GRCh38, latest major release)
- `gnomad_r3` -- gnomAD v3.1.2 (GRCh38, genomes only)
- `gnomad_r2_1` -- gnomAD v2.1.1 (GRCh37, exomes + genomes)

## Population frequency fields
Within `exome` or `genome` objects, population-specific frequencies are available via
`populations { id ac an }` (compute AF as AC/AN only when AN is positive). Ancestry-group IDs and availability vary by dataset;
read the returned IDs rather than applying a fixed cross-release list.

## Response example (illustrative counts, not a current frequency estimate)
```json
{
  "data": {
    "variant": {
      "variant_id": "1-55039974-G-A",
      "rsids": ["rs11591147"],
      "chrom": "1",
      "pos": 55039974,
      "ref": "G",
      "alt": "A",
      "exome": { "ac": 1234, "an": 250000, "af": 0.004936 },
      "genome": { "ac": 456, "an": 150000, "af": 0.00304 }
    }
  }
}
```

## Rate Limits
- No published rate limits, but aggressive querying will be throttled
- Use reasonable request pacing (~1 req/sec recommended)
- For bulk downloads, use gnomAD's Hail tables on Google Cloud or download VCFs

## Notes
- The GraphQL schema is not versioned separately; it tracks the gnomAD web interface
- Use the browser's network inspector on gnomad.broadinstitute.org to discover
  additional query fields and structures
- Structural variants (SV) have a separate query structure (`structural_variant`)
- Constraint metrics (pLI, LOEUF) are available on gene queries via `gnomad_constraint`.
- A null exome/genome result is unavailable data, not zero frequency. Even AC=0 must be interpreted with AN, coverage, filters, dataset and ancestry. Population frequency alone does not classify clinical pathogenicity.
