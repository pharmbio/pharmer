# pharmer skills

This repository is an agent's SKILL library of Pharmbio. 

A skill is a folder of instructions, scripts and reference files that an AI agent loads when a task needs it. 

Every skill here uses the `SKILL.md` format, so it works in
Claude Code, the Claude apps, the Claude API, and any other agents that support skills.

## Available skills

| Skill                                              | What it does                                                                                                                                                        |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`data-visualization`](skills/data-visualization/) | Journal-ready scientific figures: builds at the journal's size, fonts and dpi, checks colour-blind safety, audits the exported files, and writes the figure legend. |
| [`plate-layout-design`](skills/plate-layout-design/) | Microplate layouts (96/384/1536) with the PLAID constraint solver from iPLAID: spreads dose series, balances controls, keeps edges empty, checks the result and writes an iPLAID-compatible layout CSV and plate map. |
| [`public-database-lookup`](skills/public-database-lookup/) | Reproducible lookups in 46 public scientific database APIs (PubChem, ChEMBL, UniProt, Ensembl, ClinVar, gnomAD, ClinicalTrials.gov and more): resolves identifiers, paginates and reconciles counts, and reports provenance. |

## Quick start

Install a skill for Claude Code on your machine:

```bash
git clone <repo-url> pharmer-skills
cd pharmer-skills
mkdir -p ~/.claude/skills
ln -s "$PWD/skills/data-visualization" ~/.claude/skills/data-visualization
```

Then start a new Claude Code session and ask for something the skill covers, or type `/data-visualization`.

For the Claude apps, the API, other agents, and project-level installs, see
**[Installing and using skills](docs/installing-and-using-skills.md)**.

## Repository layout

```
.
├── skills/                 # one folder per skill; each folder is what gets installed
│   └── data-visualization/
│       ├── SKILL.md        # instructions the agent reads (required)
│       ├── scripts/        # code the agent runs
│       ├── references/     # detail the agent reads only when needed
│       └── requirements.txt
├── evals/                  # test tasks per skill: prompts + data (not installed)
│   └── data-visualization/
├── docs/
│   ├── creating-a-skill.md
│   ├── installing-and-using-skills.md
│   └── skills/             # one page per skill, written for people
└── template/               # copy this to start a new skill
```

Only the folder under `skills/` is installed. Test data and docs stay in the repo, so they never use up the agent's context.

## Adding a skill

1. Copy the template: see [`template/README.md`](template/README.md).
2. Write the skill, following **[Creating a skill](docs/creating-a-skill.md)**.
3. Add test tasks under `evals/<skill-name>/` and run them with and without the skill.
4. Go through the [checklist](docs/creating-a-skill.md#checklist).
5. Add a row to the table above and open a pull request.

**IMPORTANT:** You do not need to do it manually! Feel free to ask agent/Claude to do it for you. The more important thing is to make sure the SKILLs work properly.

## Rules for this repo

- One skill per folder under `skills/`. The folder name and the `name:` in `SKILL.md` must match.
- Skill names use lowercase letters, digits and hyphens, for example `data-visualization` or `plate-qc`.
- No real patient data, customer data, credentials or API keys anywhere in the repo. 
- The skills will be available for all members of our groups. 
