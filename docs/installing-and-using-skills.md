# Installing and using skills

A skill is installed by putting its folder (the one under `skills/`, with `SKILL.md` at the top) where the agent
looks for skills, or by uploading it as a zip. Pick the section for the agent you use.

- [How an agent uses a skill](#how-an-agent-uses-a-skill)
- [Claude Code](#claude-code)
- [Claude apps (claude.ai, desktop)](#claude-apps-claudeai-desktop)
- [Claude API](#claude-api)
- [Other agents](#other-agents)
- [Dependencies](#dependencies)
- [Using a skill](#using-a-skill)
- [Troubleshooting](#troubleshooting)

## How an agent uses a skill

1. At startup the agent reads only the `name` and `description` of every installed skill. This costs a few dozen tokens per skill.
2. When your request matches a description, the agent opens that skill's `SKILL.md` and follows it.
3. `SKILL.md` points to scripts and reference files. The agent runs or reads them only when a step needs them.

Because of this, you can install many skills without slowing the agent down. The description decides when a skill is used,
so it is the part worth getting right (see [Creating a skill](creating-a-skill.md#2-write-the-description)).

## Claude Code

Claude Code reads skills from two places:

| Scope | Folder | Who gets it |
|---|---|---|
| Personal | `~/.claude/skills/<skill-name>/` | You, in every project |
| Project | `<project>/.claude/skills/<skill-name>/` | Everyone who works in that project (commit the folder) |

**Option A: link to your clone (recommended).** `git pull` then updates the skill everywhere.

```bash
git clone <repo-url> ~/pharmer-skills
mkdir -p ~/.claude/skills
ln -s ~/pharmer-skills/skills/data-visualization ~/.claude/skills/data-visualization
```

**Option B: copy the folder.** Use this for a project, so collaborators get the skill without cloning this repo.

```bash
mkdir -p .claude/skills
cp -R ~/pharmer-skills/skills/data-visualization .claude/skills/
```

Start a new session after installing. To check it loaded, type `/` and look for the skill's name, or ask
"what skills do you have?".

To remove a skill, delete its folder or link from the skills directory.

## Claude apps (claude.ai, desktop)

1. Zip the skill folder from the repo root. The zip must contain the folder itself, with `SKILL.md` inside it:
   ```bash
   (cd skills && zip -r ~/data-visualization.zip data-visualization -x '*.DS_Store' '*__pycache__*')
   ```
2. In Claude, open **Customize** and choose **Add skill**, then upload `~/data-visualization.zip`.
3. Make sure the skill is turned on. It is available in new chats.

Skills that run code need code execution to be enabled for your account.

On Team and Enterprise plans an admin can add a skill for the whole organisation, so members don't have to upload it themselves.

## Claude API

Skills can be uploaded through the API and attached to requests that use the code execution tool.
Upload the zipped skill folder, then reference the returned skill ID in the request's container.
The endpoint, beta header and request shape are in Anthropic's *Agent Skills* API docs; check them before you build this in,
because the API was still in beta when this guide was written. The Claude API sandbox has no network access, so every package
in the skill's `requirements.txt` must already be available there.

## Other agents

**Agents that support `SKILL.md` skills:** copy or link the skill folder into the agent's skills directory (see that agent's docs for the path).
The folder layout is the same everywhere.

**Agents without skill support** (or a plain chat model): give the agent `SKILL.md` as instructions, for example as a
system prompt, a rules file (`AGENTS.md`, `.cursorrules` and similar), or the first message. Make the `scripts/` and `references/`
folders available in its working directory, so the paths in `SKILL.md` still resolve.

## Dependencies

Skills that run code list their Python packages in `skills/<skill-name>/requirements.txt`. Install them in the environment the agent
runs code in:

```bash
pip install -r skills/data-visualization/requirements.txt
```

The skill's page in `docs/skills/` lists anything else it needs (R, command-line tools, API keys).

## Using a skill

You usually don't need to do anything special. Ask for the task in plain words, and the agent picks the skill whose description matches:

> Make Figure 2 for our Nature Communications submission from `cells.csv`: a UMAP by cell type and a marker dot plot.

To force a specific skill:

- Claude Code: type `/<skill-name>` followed by your request, e.g. `/data-visualization make this plot ready for Cell Reports`.
- Any agent: name it, e.g. "Use the data-visualization skill to ...".

Tips:

- Give the agent the inputs the skill expects: attach the files, or run the agent from a folder where it can read them.
- Say the target when there is one (journal, file format, audience). Skills fill in sensible defaults, but they can't guess your goal.
- Read what the skill reports back, such as audit results and warnings. Skills are there to make the agent check its work, so the report is often the useful part.

## Troubleshooting

| Problem | Likely cause and fix |
|---|---|
| The skill never triggers | It isn't installed where the agent looks, or you didn't start a new session. Check the folder path, and check that `SKILL.md` is directly inside the skill folder (not one level deeper). |
| It triggers for the wrong tasks, or not for the right ones | The description is too vague or misses the words users type. Edit the description and open a PR. |
| `ModuleNotFoundError` when a script runs | The packages in `requirements.txt` aren't installed in the agent's environment. |
| The upload is rejected | The zip must contain the skill folder with `SKILL.md` inside it, and the frontmatter must be valid (`name` matches the folder, `description` present and at most 1,024 characters). |
| Two skills compete for the same task | Make each description say clearly when *not* to use it, or name the skill in your request. |
