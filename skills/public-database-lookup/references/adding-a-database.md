# Adding a Database or Editing a Reference File

For maintainers. Lookups do not need this file.

## Contents
- Admission rule
- Steps
- Reference file layout
- Writing rules
- Testing

## Admission rule

Add only databases that can be queried without an API key, account or licence. An optional key
that only raises rate limits is fine (NCBI, OpenFDA).

## Steps

```
Adding a database:
- [ ] 1. Write references/<database-name>.md using the layout below
- [ ] 2. Add a row to the matching table under "Databases" in SKILL.md (Use for, Fallback)
- [ ] 3. Add identifier formats to "Identifiers" in SKILL.md if they are new
- [ ] 4. Add pagination to the table in references/exhaustive-retrieval.md
- [ ] 5. Run every python block against the live API (see Testing)
- [ ] 6. Update the database count in the SKILL.md description if it changed
```

## Reference file layout

Use the section names the existing files use, in this order. Leave out sections that do not apply.

- `# <Database name>`, then `## Contents` if the file is over 100 lines
- `## Base URL`
- `## Auth`: "No API key required", or the optional key and what it raises
- `## Key Endpoints`: HTTP notation (`GET /path/{id}`) plus parameter tables
- `## Example Calls`: `requests` or `fetch` snippets that run in plain Python 3
- `## Response Format`: the fields a lookup needs, with a short example
- `## Pagination`: style, parameter names, page-size cap, the total-count field
- `## Rate Limits`
- `## Notes`: server-side vs. local filters, identifier conventions, known completeness or
  ambiguity hazards

## Writing rules

- **Link only to SKILL.md**, never to another reference file. Agents may read a second-level link
  only partially.
- **Show calls, not URLs with baked-in values**: raw values in `params`, `requests.utils.quote`
  for path segments, GraphQL values in `variables`.
- **Keep snippets portable**: standard library plus `requests` only, relying on the imports in
  SKILL.md, **The fetch helper**. End each block with a small summary expression (counts, IDs, a
  few fields), never the whole payload, and write binary or large output to a file.
- **Date live observations**: write "On 2026-10-07 this returned HTTP 500 …" rather than
  "currently" or "recently", and keep the instruction itself valid after the date passes.
- **Justify constants**: a non-default timeout, page size or sleep gets a comment saying why.
- **Keep terminology**: "reference file", "endpoint", "server-side filter", "local filter",
  "targeted lookup", "exhaustive retrieval", "count reconciliation".

## Testing

Run each `python` block against the live API in a fresh Python 3 process with `requests`
installed. This runner, started from the skill folder, defines the `fetch` helper from SKILL.md
and prints each block's final summary expression:

```python
import ast
import re
from pathlib import Path

def blocks(path):
    return re.findall(r"```python\n(.*?)```", Path(path).read_text(), re.S)

def run(block, ns):
    tree = ast.parse(block)
    last = tree.body.pop() if tree.body and isinstance(tree.body[-1], ast.Expr) else None
    exec(compile(tree, "<block>", "exec"), ns)
    return eval(compile(ast.Expression(last.value), "<block>", "eval"), ns) if last else None

ns = {}
run(blocks("SKILL.md")[0], ns)  # the fetch helper and its imports
for block in blocks("references/<file>.md"):
    print(repr(run(block, ns))[:500])
```

A block passes when it prints its summary rather than raising an exception or HTTP error. Then
run any evaluation scenarios that touch the database.
