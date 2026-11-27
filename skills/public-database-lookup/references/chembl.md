# ChEMBL REST API

## Contents
- Base URL
- Auth
- Key Endpoints
- Common Parameters
  - Filtering operators (append to field names)
- Example Calls
- Response Format (molecule collection)
- Rate Limits

## Base URL
```python
import requests

CHEMBL = "https://www.ebi.ac.uk/chembl/api/data"
```

## Auth
No API key required. Fully open and free.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/molecule/{chembl_id}` | Get molecule by ChEMBL ID |
| `/molecule/search?q={query}` | Free-text molecule search |
| `/target/{chembl_id}` | Get target by ChEMBL ID |
| `/target/search?q={query}` | Free-text target search |
| `/activity?molecule_chembl_id={id}` | Activities for a molecule |
| `/activity?target_chembl_id={id}` | Activities for a target |
| `/mechanism?molecule_chembl_id={id}` | Mechanism of action |
| `/drug_indication?molecule_chembl_id={id}` | Drug indications |
| `/similarity/{smiles}/{threshold}` | Similarity search (threshold 40-100) |
| `/substructure/{smiles}` | Substructure search |

`{smiles}` is a path segment: pass the raw SMILES through `requests.utils.quote(smiles, safe="")`. Query values (`q`, filters) go in `params`.

## Common Parameters

- `format=json` or `.json` — request JSON explicitly; do not assume the default negotiated format
- `limit` — results per page (default 20, max 1000)
- `offset` — pagination offset
- `order_by` — sort field (prefix `-` for descending)
- `only` — return only specified fields (comma-separated)

### Filtering operators (append to field names)
`__exact`, `__icontains`, `__gt`, `__gte`, `__lt`, `__lte`, `__in`, `__isnull`, `__startswith`, `__range`, `__regex`

## Example Calls

```python
# Get molecule by ID (single object, no page_meta)
r = requests.get(f"{CHEMBL}/molecule/CHEMBL25.json", timeout=30)
r.raise_for_status()
mol = r.json()

# Search molecules by name
r = requests.get(f"{CHEMBL}/molecule/search", params={"q": "aspirin", "format": "json"}, timeout=30)
r.raise_for_status()
found = r.json()

# Mechanism of action
r = requests.get(f"{CHEMBL}/mechanism", params={"molecule_chembl_id": "CHEMBL25", "format": "json"}, timeout=30)
r.raise_for_status()
moa = r.json()["mechanisms"]

{"molecule": [mol["molecule_chembl_id"], mol["pref_name"], mol["max_phase"]],
 "search_total": found["page_meta"]["total_count"],
 "search_top": [m["molecule_chembl_id"] for m in found["molecules"][:5]],
 "mechanisms": [(m["mechanism_of_action"], m["target_chembl_id"]) for m in moa]}
```

```python
# Activities for a target with potency filter
r = requests.get(f"{CHEMBL}/activity", params={"target_chembl_id": "CHEMBL240", "pchembl_value__gte": 6,
                                               "format": "json", "limit": 100}, timeout=30)
r.raise_for_status()
acts = r.json()
# page_meta.next is a site-relative path: next_url = "https://www.ebi.ac.uk" + acts["page_meta"]["next"]

# Similarity search (80% threshold): quote the raw SMILES
smiles = "CC(=O)Oc1ccccc1C(=O)O"
r = requests.get(f"{CHEMBL}/similarity/{requests.utils.quote(smiles, safe='')}/80.json", timeout=30)
r.raise_for_status()
similar = r.json()

# Approved drugs only
r = requests.get(f"{CHEMBL}/molecule", params={"max_phase": 4, "format": "json"}, timeout=30)
r.raise_for_status()
approved = r.json()

{"activities": {"total": acts["page_meta"]["total_count"], "next": acts["page_meta"]["next"],
                "first": {k: acts["activities"][0][k] for k in ("molecule_chembl_id", "standard_type",
                          "standard_relation", "standard_value", "standard_units", "pchembl_value")}},
 "similar": [(m["molecule_chembl_id"], m["similarity"]) for m in similar["molecules"][:5]],
 "approved_total": approved["page_meta"]["total_count"]}
```

## Response Format (molecule collection)
```json
{
  "page_meta": {"limit": 20, "offset": 0, "total_count": 150},
  "molecules": [{
    "molecule_chembl_id": "CHEMBL25",
    "pref_name": "ASPIRIN",
    "max_phase": 4,
    "molecule_properties": {
      "full_mwt": 180.16, "full_molformula": "C9H8O4",
      "alogp": 1.31, "hba": 3, "hbd": 1, "psa": 63.60
    },
    "molecule_structures": {
      "canonical_smiles": "CC(=O)Oc1ccccc1C(=O)O",
      "standard_inchi_key": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
    }
  }]
}
```

## Rate Limits
No strict limit. Keep under ~10 req/sec. No auth required.

Single `/molecule/{id}.json` returns the molecule object directly, while list/search
responses include `page_meta` and `molecules`. Follow `page_meta.next`. Molecular
weights can be numeric strings; retain activity units, relation qualifiers and assay
type rather than treating every reported value as comparable binding affinity.
