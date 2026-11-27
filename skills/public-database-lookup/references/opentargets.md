# Open Targets Platform API

## Contents
- Base URLs
- Authentication
- GraphQL API
  - 1. Target information (by Ensembl Gene ID)
  - 2. Disease information (by EFO ID)
  - 3. Target-Disease associations
  - 4. Disease-Target associations (from disease side)
  - 5. Evidence for a target-disease pair
  - 6. Drug/molecule information
  - 7. Search across targets, diseases, and drugs
  - 8. Drugs and clinical candidates for a target
  - 9. Tractability (druggability)
- Key Identifiers
- Datasource IDs
- Pagination
- Rate Limits
- Error Format
- Tips

## Base URLs

**GraphQL API (primary, recommended):**
```
https://api.platform.opentargets.org/api/v4/graphql
```

**Important:** The GraphQL endpoint requires HTTP POST with a JSON body. `requests.post(..., json=...)` sets `Content-Type: application/json`; pass IDs as `variables`, not inside the query text:
```python
import requests

OPENTARGETS = "https://api.platform.opentargets.org/api/v4/graphql"

query = "query T($ensemblId: String!) { target(ensemblId: $ensemblId) { approvedSymbol approvedName } }"
r = requests.post(OPENTARGETS, json={"query": query, "variables": {"ensemblId": "ENSG00000157764"}}, timeout=30)
r.raise_for_status()
body = r.json()
if body.get("errors"):
    raise RuntimeError(body["errors"])
body["data"]["target"]
```

## Authentication

No API key required. All endpoints are public.

## GraphQL API

All GraphQL queries are sent as POST requests to the GraphQL endpoint: the query text below as
`query`, its **Variables** as `variables`. For example, query 3 (fields trimmed) with its
`Pagination` input object:

```python
query = """
query Associations($ensemblId: String!, $page: Pagination!) {
  target(ensemblId: $ensemblId) {
    approvedSymbol
    associatedDiseases(page: $page) { count rows { disease { id name } score } }
  }
}
"""
variables = {"ensemblId": "ENSG00000141510", "page": {"index": 0, "size": 10}}
r = requests.post(OPENTARGETS, json={"query": query, "variables": variables}, timeout=30)
r.raise_for_status()
body = r.json()
if body.get("errors"):  # GraphQL errors arrive with HTTP 200
    raise RuntimeError(body["errors"])
assoc = body["data"]["target"]["associatedDiseases"]
{"count": assoc["count"], "top": [(row["disease"]["id"], row["disease"]["name"], round(row["score"], 3)) for row in assoc["rows"][:5]]}
```

### 1. Target information (by Ensembl Gene ID)

```graphql
query TargetInfo($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    approvedName
    biotype
    proteinIds {
      id
      source
    }
    tractability {
      label
      modality
      value
    }
    safetyLiabilities {
      event
      effects {
        direction
        dosing
      }
    }
    pathways {
      pathway
      pathwayId
    }
    functionDescriptions
    subcellularLocations {
      location
    }
  }
}
```

**Variables:** `{ "ensemblId": "ENSG00000141510" }`


---

### 2. Disease information (by EFO ID)

```graphql
query DiseaseInfo($efoId: String!) {
  disease(efoId: $efoId) {
    id
    name
    description
    therapeuticAreas {
      id
      name
    }
    synonyms {
      terms
    }
  }
}
```

**Variables:** `{ "efoId": "MONDO_0004992" }` (cancer)

The argument is named `efoId` but takes any current disease ID. Obsolete IDs return `disease: null`
without an error: on 2026-10-07 (API 26.9) `EFO_0000311` returned null and was listed in
`MONDO_0004992`'s `obsoleteTerms`. Resolve names with the search query (7) first.


---

### 3. Target-Disease associations

```graphql
query Associations($ensemblId: String!, $page: Pagination!) {
  target(ensemblId: $ensemblId) {
    approvedSymbol
    associatedDiseases(page: $page) {
      count
      rows {
        disease {
          id
          name
        }
        score
        datasourceScores {
          id
          score
        }
      }
    }
  }
}
```

**Variables:**
```json
{
  "ensemblId": "ENSG00000141510",
  "page": { "index": 0, "size": 10 }
}
```


---

### 4. Disease-Target associations (from disease side)

```graphql
query DiseaseAssociations($efoId: String!, $page: Pagination!) {
  disease(efoId: $efoId) {
    name
    associatedTargets(page: $page) {
      count
      rows {
        target {
          id
          approvedSymbol
        }
        score
        datasourceScores {
          id
          score
        }
      }
    }
  }
}
```

**Variables:**
```json
{
  "efoId": "MONDO_0004992",
  "page": { "index": 0, "size": 10 }
}
```

---

### 5. Evidence for a target-disease pair

```graphql
query Evidence($ensemblId: String!, $efoId: String!, $size: Int!) {
  disease(efoId: $efoId) {
    evidences(ensemblIds: [$ensemblId], size: $size) {
      count
      rows {
        id
        score
        datasourceId
        datatypeId
        literature
        diseaseFromSource
        targetFromSourceId
        resourceScore
        urls {
          niceName
          url
        }
      }
    }
  }
}
```

**Variables:**
```json
{
  "ensemblId": "ENSG00000141510",
  "efoId": "MONDO_0004992",
  "size": 10
}
```

`evidences` returns direct evidence unless `enableIndirect: true`. On 2026-10-07 this pair gave
`count: 0` direct and ~197,000 indirect (a 14 s query); prefer a specific disease ID.

---

### 6. Drug/molecule information

```graphql
query DrugInfo($chemblId: String!) {
  drug(chemblId: $chemblId) {
    id
    name
    drugType
    maximumClinicalStage
    mechanismsOfAction {
      rows {
        mechanismOfAction
        targets {
          id
          approvedSymbol
        }
      }
    }
    indications {
      rows {
        disease {
          id
          name
        }
        maxClinicalStage
      }
    }

  }
}
```

**Variables:** `{ "chemblId": "CHEMBL25" }` (aspirin)


---

### 7. Search across targets, diseases, and drugs

```graphql
query Search($queryString: String!, $entityNames: [String!], $page: Pagination!) {
  search(queryString: $queryString, entityNames: $entityNames, page: $page) {
    total
    hits {
      id
      entity
      name
      description
      score
    }
  }
}
```

**Variables:**
```json
{
  "queryString": "BRAF melanoma",
  "entityNames": ["target", "disease", "drug"],
  "page": { "index": 0, "size": 10 }
}
```


---

### 8. Drugs and clinical candidates for a target

```graphql
query ClinicalCandidates($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    approvedSymbol
    drugAndClinicalCandidates {
      count
      rows {
        id
        maxClinicalStage
        drug { id name drugType maximumClinicalStage }
        clinicalReports { id source clinicalStage url }
      }
    }
  }
}
```

Variables: `{ "ensemblId": "ENSG00000157764" }` (BRAF).
The current schema uses clinical-stage strings. Do not parse them as numeric
trial phases or infer withdrawal from a missing field.

---

### 9. Tractability (druggability)

Included in the target query (see endpoint 1 above). Modalities include:
- `SM` (small molecule)
- `AB` (antibody)
- `PR` (PROTAC)
- `OC` (other clinical)

---

## Key Identifiers

| Entity  | ID Format | Example |
|---------|-----------|---------|
| Target  | Ensembl Gene ID | `ENSG00000141510` (TP53) |
| Disease | EFO/Mondo/HP/Orphanet | `MONDO_0004992` (cancer), `MONDO_0007254` (breast cancer) |
| Drug    | ChEMBL ID | `CHEMBL25` (aspirin) |

## Datasource IDs

Datasource membership changes by release. Read `datasourceScores.id` or the
current Platform data-source documentation before setting evidence filters.
Do not assume the former Genetics Portal IDs remain current after integration
into the Platform. Association scores rank evidence support, not causal probability.

## Pagination

GraphQL uses `page: { index: Int, size: Int }` (0-based index).
Evidence connections instead use `size` plus an opaque `cursor`; request the
returned cursor and continue until exhausted. Other connections expose all rows
without pagination arguments: check the schema for each field.

## Rate Limits

- No API key required.
- Fair-use rate limiting applies. No hard published limit.
- For bulk data, use the Open Targets data downloads (Parquet files on GCS/FTP) rather than API.
- Respect HTTP 429 and `Retry-After` headers.

## Error Format

GraphQL errors:
```json
{
  "errors": [
    {
      "message": "Variable '$ensemblId' expected value of type 'String!' but got: null",
      "locations": [{"line": 1, "column": 7}]
    }
  ]
}
```

Inspect both HTTP status and GraphQL `errors`; an HTTP 200 can contain failed
fields or partial `data`.

## Tips

- Use the GraphQL API for maximum flexibility -- request only the fields you need.
- Send POST with JSON `query` and `variables`; no separate REST search API is documented.
- Combine target + disease queries to get association scores with evidence breakdown.
- Use `datasourceScores` in association queries to see which evidence sources contribute most.
- The Open Targets Platform web UI at `https://platform.opentargets.org` has a GraphQL playground for testing queries.

Current [GraphQL schema](https://api.platform.opentargets.org/api/v4/graphql/schema) and [API guide](https://platform-docs.opentargets.org/data-access/graphql-api).
