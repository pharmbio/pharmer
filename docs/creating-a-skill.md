# Creating a skill

This guide takes you from an idea to a skill merged into this repo. It assumes you have used an AI agent before,
but not written a skill.

- [1. Decide whether it should be a skill](#1-decide-whether-it-should-be-a-skill)
- [2. Write the description](#2-write-the-description)
- [3. Start from the template](#3-start-from-the-template)
- [4. Write SKILL.md](#4-write-skillmd)
- [5. Add scripts and references](#5-add-scripts-and-references)
- [6. Test it](#6-test-it)
- [7. Submit it](#7-submit-it)
- [Checklist](#checklist)

## 1. Decide whether it should be a skill

A skill is worth writing when:

- you keep giving an agent the same instructions or corrections for one kind of task,
- the task has a right way to do it that the agent doesn't know (a journal's figure specs, an internal data format, a lab protocol), or
- part of the task is deterministic and better done by a script than by the agent writing new code each time.

Start by doing the task with an agent a few times without a skill. Note what you had to explain, what it got wrong, and what you checked by hand.
Those notes become the skill.

## 2. Write the description

The `description` in the frontmatter is the only part the agent sees before it decides to load the skill.
If it is vague, the skill won't trigger. Write it before anything else.

- Third person: "Builds ...", "Checks ...", not "I can help you ..." or "You can use this to ...".
- Say **what** the skill does and **when** to use it.
- Include the words users actually type: file types, tool names, journal names, assay names.
- 1,024 characters at most.

Good:

```yaml
description: "Fits dose-response curves (4PL) to plate-reader exports and reports IC50/EC50 with confidence intervals. Use when the user has dose-response, IC50, EC50 or plate-reader data, or asks to fit or plot a dose-response curve."
```

Too vague to trigger reliably:

```yaml
description: "Helps with data analysis."
```

## 3. Start from the template

```bash
NAME=dose-response-fitting           # lowercase letters, digits and hyphens
cp -R template/skill        skills/$NAME
cp    template/skill-doc.md docs/skills/$NAME.md
mkdir -p evals/$NAME
```

Set `name: dose-response-fitting` in `skills/$NAME/SKILL.md`. It must match the folder name.
Then replace the `skill-name` placeholders in the other files.

Naming: describe the activity (`dose-response-fitting`, `plate-qc`, `data-visualization`). Avoid vague names
(`helper`, `tools`, `data`), and don't use the words `claude` or `anthropic`.

## 4. Write SKILL.md

`SKILL.md` is the agent's instructions. It has a frontmatter block followed by Markdown:

```markdown
---
name: dose-response-fitting
description: "..."
---

# Dose-response fitting

## Workflow (follow in order)
### 1. ...
```

Guidelines:

- **Write only what the agent doesn't already know.** It knows Python and statistics. It doesn't know your lab's
  plate layout, your naming rules, or which mistakes reviewers flag. Every line costs context, so leave out the rest.
- **Give a procedure.** Numbered steps the agent follows in order work better than a list of tips.
- **Make it check its own work.** Add a step that runs a validation script or a checklist and says what to do when a check fails.
  This is usually where a skill earns its keep: [`data-visualization`](../skills/data-visualization/SKILL.md) audits each figure and
  fixes what fails before delivering it.
- **Set defaults.** Say what to do when the user doesn't specify something, instead of listing options.
- **Be firm where mistakes are costly.** Use "always" and "never" for data integrity, safety and anything that would be rejected.
  Leave the agent free to choose elsewhere.
- **Keep it under about 500 lines.** Move long material (specs, API notes, recipes) into `references/` and link to it.
- **Don't put dates or versions in the instructions** that will go stale ("after March, use ..."). Put time-sensitive numbers in a reference file with
  the date you checked them and a link to the source.
- **Use forward slashes and paths relative to the skill folder** (`scripts/fit.py`, `references/assays.md`).

## 5. Add scripts and references

```
skills/<skill-name>/
├── SKILL.md             # required
├── scripts/             # code the agent runs; only the output enters its context
├── references/          # detail the agent reads only when a step needs it
└── requirements.txt     # Python packages the scripts need
```

**Scripts.** Put deterministic or fiddly steps in scripts: parsing an instrument export, validating an output, converting units.
A tested script is more reliable than code the agent writes on the fly, and it saves tokens.

- Tell the agent in `SKILL.md` whether to *run* a script (`Run python scripts/fit.py data.csv`) or *read* it.
- Print error messages that say what went wrong and how to fix it. The agent reads them and acts on them.
- Handle errors in the script rather than leaving them for the agent to work out.
- List every package in `requirements.txt`, and say in `SKILL.md` how to install it.

**References.** Detail that only some requests need: specs, lookup tables, recipes per case.

- Link each reference file directly from `SKILL.md`. Don't chain references to other references; the agent may not follow them.
- Use descriptive file names (`journal_specs.md`, not `ref2.md`).
- Start any file over ~100 lines with a contents list, so the agent can jump to the right section.

Large files cost nothing until the agent opens them, so you can include full specs or long tables if they help.

## 6. Test it

Test the skill on real tasks before submitting it.

1. **Write 2–5 test tasks** in `evals/<skill-name>/task_N/`. Each task folder holds the input data and an `eval_prompts.md` with
   a prompt a user would really send and a short list of things a good answer must get right.
   [`evals/data-visualization/`](../evals/data-visualization/) is a worked example. Use synthetic or public data only.
2. **Run each prompt twice** in fresh sessions: once with the skill installed and once without. The skill should clearly improve the result.
   If it doesn't, it's not adding anything yet.
3. **Watch what the agent does.** Does it load the skill when it should? Does it follow the steps, open the right reference, run the scripts?
   Where it goes wrong, fix the instruction that misled it, then run again.
4. **Check triggering both ways.** Ask a few things the skill should handle, phrased differently, and a few it shouldn't.
   Adjust the description until both behave.
5. **Try the models your team uses.** Instructions that are enough for a large model can be too thin for a smaller one.

Before submitting, check the frontmatter by hand: `name` is lowercase letters, digits and hyphens (64 characters at most)
and matches the folder name, and `description` is present, has no XML tags, and is 1,024 characters at most.

## 7. Submit it

1. Fill in `docs/skills/<skill-name>.md`: what the skill does, how to install it, example prompts, limitations, and the owner.
2. Add a row for the skill to the table in the top-level [README](../README.md).
3. Open a pull request. In the description, say what you tested and paste a short before/after comparison from your test tasks.

To change an existing skill later, edit it in place, rerun its test tasks, and say in the PR what changed and why.

## Checklist

- [ ] `name` matches the folder name; lowercase, digits and hyphens only
- [ ] `description` says what it does and when to use it, in the third person, with the words users type
- [ ] `SKILL.md` is under ~500 lines and gives a step-by-step procedure with a check step
- [ ] Every script and reference file is linked from `SKILL.md`
- [ ] Packages are listed in `requirements.txt`
- [ ] No template comments or placeholders left
- [ ] Test tasks in `evals/<skill-name>/`, run with and without the skill
- [ ] No real patient data, customer data, credentials or API keys
- [ ] `docs/skills/<skill-name>.md` written, with an owner, and README table updated
