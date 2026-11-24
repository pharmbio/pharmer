---
name: skill-name
description: "One or two sentences, third person. Say WHAT the skill does and WHEN to use it, with the words a user would actually type (file types, tool names, domain terms). Example: Builds dose-response curves from plate-reader exports and fits 4PL models. Use when the user has IC50/EC50 data, plate-reader CSVs, or asks for a dose-response fit. Max 1024 characters."
---

# Skill title

<!--
Delete every HTML comment before you publish the skill.

Rules for SKILL.md:
- Keep it under ~500 lines. Move long material into references/ and link to it from here.
- Write for a capable colleague: only what the agent would not already know.
- Prefer numbered steps the agent can follow and check.
- Use forward slashes in paths and refer to files relative to the skill folder.
-->

One short paragraph: what a good result looks like and why the skill exists.

## Workflow (follow in order)

### 1. Understand the request
- What to ask or infer before starting.
- Sensible defaults when the user does not say.

### 2. Do the work
- The main procedure.
- Run `python scripts/example.py <input>` for the deterministic part instead of writing that code from scratch.
- For details on <topic>, read `references/REFERENCE.md`.

### 3. Check the result
- How to verify the output (a script to run, a checklist, a preview to look at).
- What to do when a check fails: fix, re-run, re-check.

### 4. Deliver
- Which files to produce, where to save them, and what to report back to the user.

## Rules
- Things the agent must always or never do (data integrity, safety, naming conventions).

## Helpers
| File | What it does |
|---|---|
| `scripts/example.py` | One-line description. Run with `python scripts/example.py --help`. |
| `references/REFERENCE.md` | Detailed reference; read when step 2 needs it. |

## Known limits
- What the skill does not cover, and what the user should check by hand.
