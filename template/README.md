# Templates

Starting points for a new skill. See [Creating a skill](../docs/creating-a-skill.md) for the full walkthrough.

| Folder / file | Copy to | What it is |
|---|---|---|
| `skill/` | `skills/<skill-name>/` | The skill itself: `SKILL.md`, `scripts/`, `references/`, `requirements.txt` |
| `skill-doc.md` | `docs/skills/<skill-name>.md` | The page people read before installing |

```bash
NAME=my-skill-name
cp -R template/skill      skills/$NAME
cp    template/skill-doc.md docs/skills/$NAME.md
```

Then replace every `skill-name` with your skill's name, and set `name:` in `SKILL.md` to the folder name.
