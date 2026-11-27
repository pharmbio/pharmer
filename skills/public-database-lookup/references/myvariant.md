# MyVariant.info

Public annotation aggregation service: `https://myvariant.info/v1`.
[Annotation contract](https://docs.myvariant.info/en/latest/doc/variant_annotation_service.html)
and [query contract](https://docs.myvariant.info/en/latest/doc/variant_query_service.html).

```python
import requests

MYVARIANT = "https://myvariant.info/v1"

r = requests.get(f"{MYVARIANT}/query", params={"q": "rs28934578", "fields": "cadd.phred,dbsnp.rsid", "size": 5},
                 timeout=30)
r.raise_for_status()
hits = r.json()
hgvs_id = "chr17:g.7578406C>G"  # path segment: quote the ">" and ":"
r = requests.get(f"{MYVARIANT}/variant/{requests.utils.quote(hgvs_id, safe='')}",
                 params={"fields": "cadd.phred,dbsnp.rsid"}, timeout=30)
r.raise_for_status()
one = r.json()
# Batch: POST /variant with form data; ids is one comma-separated string
r = requests.post(f"{MYVARIANT}/variant", data={"ids": "chr17:g.7578406C>G,chr17:g.7578406C>T", "fields": "cadd.phred"},
                  timeout=30)
r.raise_for_status()
{"query_total": hits["total"], "query_ids": [h["_id"] for h in hits["hits"]],
 "variant": {"_id": one["_id"], "cadd_phred": one.get("cadd", {}).get("phred")},
 "batch": [(h["query"], h.get("cadd", {}).get("phred"), h.get("notfound", False)) for h in r.json()]}
```

`/variant/{id}` uses HGVS genomic identifiers on hg19 as documented. A returned
`hg38` coordinate field does not change the input identifier convention.
An rsID can produce multiple alternate-allele hits; compare alleles and assembly
before selecting a hit. `fields` supports comma-separated fields and dot paths.
Batch POST `/variant` accepts at most 1,000 `ids`; larger inputs can be omitted.
Query results use `hits`, `total`, and pagination parameters `size`/`from`.

Scores are aggregated from particular source releases. Record source and model
versions, genome assembly, alleles, transcript and retrieval date. A difference
between a stored CADD score and an Ensembl VEP score may reflect a release,
assembly or model difference; there is no justified universal PHRED threshold
for declaring a score stale. For clinical classifications, retrieve the full
ClinVar record, review status, condition and conflicting submissions.
