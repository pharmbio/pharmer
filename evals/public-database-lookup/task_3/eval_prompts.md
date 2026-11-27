## Prompt

What is the clinical significance of rs334, and how common is it in the population?

## A good answer

Values checked on 2026-11-27 (ClinVar VCV000015333.185, gnomAD `gnomad_r4`).

- Resolves rs334 through dbSNP and notices it names **several alternate alleles** at GRCh38 chr11:5,227,002
  (T>A, T>C, T>G). It does not report one frequency or classification for "rs334" as a whole.
- Identifies the sickle-cell allele: genomic T>A = HBB `c.20A>T` (p.Glu7Val, HbS). It explains the strand flip
  (HBB is on the minus strand) or at least keeps genomic and transcript alleles straight.
- **ClinVar**: VCV000015333 (with its version), germline classification *Pathogenic*, review status
  "criteria provided, multiple submitters, no conflicts", conditions including Hb SS disease (sickle cell
  disease) and malaria susceptibility. Keeps
  germline classification separate from somatic or oncogenicity fields, which are empty here.
- Notes the other alleles without mixing them in: T>C = `c.20A>C` (p.Glu7Ala), *Likely benign* (VCV000015175);
  T>G is a singleton in gnomAD exomes. ClinVar also holds compound records that include `c.20A>T` together with
  a second change (VCV000446735 and others); these are not the same variant.
- **gnomAD r4**, variant `11-5227002-T-A` (1-based, GRCh38): genomes AC 1,937 / AN 152,294, AF ≈ 0.0127;
  exomes AC 2,335 / AN 1,458,356, AF ≈ 0.0016. Genome and exome frequencies are reported separately, or a
  combination is clearly labelled, and the dataset version is named.
- Good: says the frequency varies strongly by ancestry (highest in African/African-American groups) and either
  retrieves the population breakdown or says it was not retrieved.
- Does not present the allele frequency as a disease risk or carrier probability.
- Provenance: databases, requests, build, access date.
