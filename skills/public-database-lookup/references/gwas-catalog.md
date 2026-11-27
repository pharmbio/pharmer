# GWAS Catalog (EBI) — REST API v2

## Contents
- Base URL
- Auth
- Key Endpoints
- Filters
- Pagination
- Response Format
- Example Calls
- Rate Limits
- Scope and interpretation

## Base URL
```
https://www.ebi.ac.uk/gwas/rest/api/v2
```

The legacy v1 API (`/gwas/rest/api/...` without `/v2`: HAL `/search/findBy...` finders,
camelCase parameters, `/singleNucleotidePolymorphisms`, `/efoTraits`) returns HTTP 410
"This legacy GWAS Catalog REST API is no longer available" (checked 2026-10-07). Do not use it.
v2 differs in more than the path: snake_case parameters, filters on the resource itself instead
of finder endpoints, and new response schemas. See the
[v2 migration guide](https://www.ebi.ac.uk/gwas/docs/news/rest-api-v2-migration-guide) and the
[API documentation](https://www.ebi.ac.uk/gwas/rest/api/v2/docs).

## Auth
No API key required.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/studies/{accession_id}` | Single study (e.g. `GCST001633`) |
| `/studies` | Filter studies (see **Filters**) |
| `/studies/{accession_id}/ancestries` | Initial/replication ancestry, sample sizes, countries |
| `/associations` | Filter associations |
| `/associations/{association_id}` | Single association |
| `/single-nucleotide-polymorphisms/{rs_id}` | Variant record (locations, alleles, MAF, consequence, mapped genes) |
| `/single-nucleotide-polymorphisms/{rs_id}/genomic-contexts` | Genes overlapping or near the variant, with distance |
| `/single-nucleotide-polymorphisms` | Filter variants |
| `/efo-traits`, `/efo-traits/{efo_id}` | Trait search and lookup (EFO/MONDO/other ontology IDs) |
| `/publications` | Filter publications |
| `/genes/{gene_name}` | Gene record (Ensembl and Entrez IDs, location) |

## Filters

Unrecognised or unsupported parameters are **silently ignored**: the request returns HTTP 200
with the unfiltered collection. Use only the filters below, and compare `page.totalElements`
with what you expect; a count in the hundreds of thousands means the filter was dropped.

Tested on 2026-10-07 (a nonsense value returns 0 for an honoured filter and the full
collection for an ignored one):

| Endpoint | Honoured | Ignored |
|---|---|---|
| `/associations` | `rs_id`, `efo_id`, `efo_trait`, `mapped_gene` (+ `extended_geneset`), `pubmed_id`, `accession_id` | `p_value`, `p_upper`, `p_lower`, `reported_trait` |
| `/studies` | `accession_id`, `pubmed_id`, `efo_id`, `efo_trait`, `disease_trait`, `mapped_gene`, `cohort`, `ancestral_group`, `full_pvalue_set`, `gxe` | — |
| `/single-nucleotide-polymorphisms` | `rs_id`, `mapped_gene`, `pubmed_id`, `bp_location` (exact position only) | `chromosome`, `bp_start`, `bp_end`, position ranges such as `bp_location=40982974-40984974` |
| `/efo-traits` | `efo_trait` (text search: `asthma` matches 13 traits), `efo_id` | `short_form` |
| `/publications` | `pubmed_id`, `title` (text search), `first_author` | — |
| `/genes` | none: use `/genes/{gene_name}` | `gene_name`, `ensembl_gene_id` |

- **P-value thresholds cannot be applied server-side.** Retrieve the records and filter locally
  on `p_value`, or on `pvalue_mantissa`/`pvalue_exponent` near the float limit (the smallest
  values appear as `p_value` `1e-323`, exponent `-323`). Rank with
  `sort=p_value&direction=asc`. An unknown `sort` key is ignored without an error.
- **Region queries are not available**: `bp_location` matches one exact position. For a region,
  find variants in Ensembl or dbSNP first, then query each rsID.
- **Gene sets**: `mapped_gene` defaults to `extended_geneset=false`, which uses the genes the
  variant maps to plus the nearest upstream and downstream genes, as shown on the website.
  `extended_geneset=true` uses all nearby Ensembl and RefSeq genes, which is what v1 did
  (HBB: 279 vs 363 associations).
- **Child traits**: the documentation describes `show_child_traits=true` (the default) as also
  returning more specific child traits. On 2026-10-07, `true` and `false` returned identical
  totals for asthma (3,234 associations) and for diabetes mellitus `MONDO_0005015` (1,291),
  although its child type 2 diabetes `MONDO_0005148` alone has 8,864. Do not rely on
  server-side expansion. Resolve the descendant trait IDs (e.g. OLS/EFO), query each `efo_id`,
  and deduplicate by `association_id`.
- Prefer `efo_id` over trait text for precision. `disease_trait` on `/studies` is the authors'
  reported trait text, not the ontology mapping.

## Pagination
`page` (0-based) and `size` (default 20). Every collection response has
`page = {size, totalElements, totalPages, number}`. Follow `_links.next.href`, which already
carries the filters, until it is absent. Large pages are slow: `size=2000` for type 2 diabetes
associations timed out after 120 s, so use `size` 200–500.

Some `_links` hrefs are URI templates (`.../ancestries{?sort,direction}`). Strip the `{...}`
part before requesting them.

## Response Format
JSON with snake_case fields. Collections are under `_embedded.<resource>`: `studies`,
`associations`, `snps`, `efo_traits`, `publications`, `genes`. A collection with no matches
has `page.totalElements == 0` and may omit `_embedded`.

Association fields include `association_id`, `accession_id`, `pubmed_id`, `first_author`,
`reported_trait` (list), `efo_traits` (`[{efo_id, efo_trait}]`), `bg_efo_traits`,
`p_value`, `pvalue_mantissa`, `pvalue_exponent`, `pvalue_description`, `or_value` (string),
`or_per_copy_num` (number), `beta` (string with unit and direction, e.g.
`"0.0211 unit decrease"`; `"-"` when not reported), `ci_lower`, `ci_upper`, `range`,
`risk_frequency` (string), `snp_effect_allele` (e.g. `["rs7329174-G"]`; `rs7329174-?` means
the study did not report the effect allele, so its effect direction is unknown), `snp_allele`,
`locations`, `mapped_genes`, `multi_snp_haplotype`, and `snp_interaction`. Optional fields such
as `or_value` are omitted when absent, so read them with `.get()`.

Variant `locations` are GRCh38 (rs7329174 is reported at 13:40983974, the same as Ensembl
GRCh38).

## Example Calls

Associations for a variant, strongest first, plus the variant record:
```python
import time
import requests

GWAS_V2 = "https://www.ebi.ac.uk/gwas/rest/api/v2"
GWAS_HEADERS = {"Accept": "application/json"}

r = requests.get(f"{GWAS_V2}/associations",
                 params={"rs_id": "rs7329174", "sort": "p_value", "direction": "asc", "size": 20},
                 headers=GWAS_HEADERS, timeout=60)
r.raise_for_status()
body = r.json()
assoc = body.get("_embedded", {}).get("associations", [])
time.sleep(0.1)
snp = requests.get(f"{GWAS_V2}/single-nucleotide-polymorphisms/rs7329174", headers=GWAS_HEADERS, timeout=60)
snp.raise_for_status()
v = snp.json()
{"variant": (v["rs_id"], v["locations"], v["alleles"], v["most_severe_consequence"]),
 "total": body["page"]["totalElements"],
 "top": [(a["accession_id"], a["reported_trait"], a["p_value"], a["snp_effect_allele"],
          a.get("or_value", a["beta"])) for a in assoc[:5]]}
```

Resolve trait text to ontology IDs, then find studies with full summary statistics:
```python
r = requests.get(f"{GWAS_V2}/efo-traits", params={"efo_trait": "type 2 diabetes", "size": 20},
                 headers=GWAS_HEADERS, timeout=60)
r.raise_for_status()
traits = [(t["efo_id"], t["efo_trait"]) for t in r.json().get("_embedded", {}).get("efo_traits", [])]
time.sleep(0.1)
r = requests.get(f"{GWAS_V2}/studies",
                 params={"efo_id": "MONDO_0005148", "full_pvalue_set": "true", "size": 5},
                 headers=GWAS_HEADERS, timeout=60)
r.raise_for_status()
studies = r.json()
{"trait_matches": traits[:10],
 "studies_with_full_sumstats": studies["page"]["totalElements"],
 "first": [(s["accession_id"], s["pubmed_id"], s["disease_trait"])
           for s in studies.get("_embedded", {}).get("studies", [])]}
```

All associations for a gene, following `next` links, with the genome-wide significance
threshold applied locally:
```python
url = f"{GWAS_V2}/associations"
params = {"mapped_gene": "HBB", "size": 200}
records, batches, expected = [], [], None
while url and len(batches) < 50:
    r = requests.get(url, params=params, headers=GWAS_HEADERS, timeout=60)
    r.raise_for_status()
    body = r.json()
    if expected is None:
        expected = body["page"]["totalElements"]
    page = body.get("_embedded", {}).get("associations", [])
    records.extend(page)
    batches.append({"page": body["page"]["number"], "returned": len(page), "cumulative": len(records)})
    url = body["_links"]["next"]["href"] if "next" in body["_links"] else None
    params = None  # the next link already carries the filters
    time.sleep(0.1)
significant = [a for a in records if a["p_value"] is not None and a["p_value"] <= 5e-8]
{"expected": expected, "retrieved": len(records), "complete": url is None, "batches": batches,
 "p_le_5e-8": len(significant), "studies": len(set(a["accession_id"] for a in significant))}
```

A study with its ancestry breakdown and publication:
```python
acc = "GCST001633"
r = requests.get(f"{GWAS_V2}/studies/{acc}", headers=GWAS_HEADERS, timeout=60)
r.raise_for_status()
study = r.json()
r = requests.get(f"{GWAS_V2}/studies/{acc}/ancestries", headers=GWAS_HEADERS, timeout=60)
r.raise_for_status()
ancestries = [(a["type"], a["number_of_individuals"], [g["ancestral_group"] for g in a["ancestral_groups"]])
              for a in r.json()["_embedded"]["ancestries"]]
r = requests.get(f"{GWAS_V2}/publications", params={"pubmed_id": study["pubmed_id"]},
                 headers=GWAS_HEADERS, timeout=60)
r.raise_for_status()
pub = r.json()["_embedded"]["publications"][0]
{"study": (study["accession_id"], study["disease_trait"], [t["efo_id"] for t in study["efo_traits"]],
           study["full_summary_stats_available"]),
 "ancestries": ancestries,
 "publication": (pub["title"], pub["journal"], pub["publication_date"])}
```

## Rate Limits
15 requests per second (documented); beyond that the API slows subsequent calls. For whole-catalog
analyses use the downloads (https://www.ebi.ac.uk/gwas/downloads, FTP at
ftp.ebi.ac.uk/pub/databases/gwas/) instead of paging through the API.

## Scope and interpretation
The API serves the literature-curated top associations and study metadata, not full genome-wide
summary statistics. A study's `full_summary_stats` field links to them when available, and a
separate summary-statistics API is under development. An association is a reported statistical
signal for the effect allele in that study's population. `mapped_genes` and genomic contexts are
positional annotations, not causal genes. Keep `reported_trait` and the `efo_traits` mapping
separate when reporting.
