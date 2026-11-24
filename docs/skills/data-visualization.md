# data-visualization

An agent skill for making journal-ready scientific figures. It comes with four test tasks.
It uses the standard `SKILL.md` format, so it works with any agent that can read instructions and run Python or R.

| | |
|---|---|
| Skill folder | [`skills/data-visualization/`](../../skills/data-visualization/) |
| Test tasks | [`evals/data-visualization/`](../../evals/data-visualization/) |
| Needs | Python 3 (`requirements.txt` in the skill folder), or R with ggplot2 |
| Owner | _to be filled in_ |

## What the skill does

When you ask an agent for a figure for a manuscript, preprint, thesis, poster or grant, the skill makes it:

1. **Fit the journal's specification**: width, height, font and font size, line weight, panel letters, file format, dpi and colour mode.
   Specs are built in for Nature (and Nature Portfolio), Cell Press, Science, PNAS, PLOS, eLife, Elsevier, ACS, IEEE, NeurIPS/ICLR, ICML/CVPR, ACL,
   plus a `generic` fallback. Other journals can be added with `register_journal(...)`.
2. **Show the data honestly**: individual points where n is small, defined error bars, SuperPlots for per-cell data
   (statistics on replicate means), bars that start at 0, no rainbow colour maps, no image manipulation.
3. **Stay readable at print size and for colour-blind readers**: the figure is built at its final size in mm and checked
   with an Okabe–Ito palette and a colour-vision-deficiency simulation.

It then **audits** the figure and the exported files (size, font sizes, overlapping or clipped text, blank space, thin lines,
dpi, Type 3 fonts) and fixes whatever fails before delivering the files, a figure legend and the source data.

Figure types covered: group comparisons and statistics, dose–response, bulk omics (volcano, heatmap, PCA, enrichment, GWAS),
single-cell and spatial (UMAP, dot plots), structural biology (pLDDT, PAE, contact maps, MD), microscopy and Cell Painting,
chemistry and drug discovery, clinical (Kaplan–Meier, forest plots) and ML/agent benchmarks.

## Files

```
skills/data-visualization/
├── SKILL.md                   # what the agent follows: workflow, rules, journal quick sheet
├── kernel.py                  # helper library, auto-loaded when the skill loads
├── requirements.txt           # Python packages the helpers need
├── scripts/
│   ├── pubfig.py              # the same helpers as an importable module (import pubfig as pf)
│   ├── check_figure.py        # command-line audit of exported figure files
│   └── journal_theme.R        # ggplot2 theme and save helpers for R users
└── references/
    ├── figure_types.md        # rules and recipes for each figure type
    └── journal_specs.md       # journal specs with links to the publishers' artwork guides

evals/data-visualization/
└── task_1/ … task_4/          # synthetic data + eval_prompts.md for each test task
```

## Installing

Follow [Installing and using skills](../installing-and-using-skills.md). Then install the Python packages in the
environment the agent runs code in:

```bash
pip install -r skills/data-visualization/requirements.txt
```

The agent loads the skill whenever a request mentions a journal, a manuscript figure, or making a figure publication-ready.
You can also ask for it by name ("use the data-visualization skill").

## Trying it out

Each task folder has a ready-to-paste prompt in `eval_prompts.md` and the data it needs:

| Task | Journal | Figure | Data |
|---|---|---|---|
| `task_1` | Nature Communications | UMAP by cell type, UMAP by condition, marker-gene dot plot | `t1_cells.csv` (6,000 cells), `t1_markers.csv` |
| `task_2` | Cell Reports | qPCR (WT / KO / KO+rescue, n = 4) and nuclear area (3 experiments × ~100 cells) with statistics | `t2_qpcr.csv`, `t2_nuclear_area.csv` |
| `task_3` | PNAS | AlphaFold model: per-residue pLDDT with domains, PAE matrix, patient mutations along the protein | `t3_plddt.csv`, `t3_pae.npy` (350 × 350, Å), `t3_domains.csv`, `t3_mutations.csv` |
| `task_4` | PLOS ONE | Cell Painting montage (5 channels + merge, 3 conditions) and a profile heatmap grouped by mechanism of action | `t4_images.npz`, `t4_meta.json`, `t4_profiles.csv` (24 compounds × 60 features) |

To run a task:

1. Start a new chat or session with the skill installed.
2. Attach or upload the data files from the task folder (or run the agent from the repo root so it can read them).
3. Paste the prompt from that folder's `eval_prompts.md`.

You should get the figure in the journal's file format(s) (for example PDF + TIFF for Cell Reports, TIFF only for PLOS ONE),
a PNG preview, a figure legend, the size in mm, and the audit result.

To see what the skill changes, run the same prompt again **without** the skill and compare the two figures.
Things worth checking: is the figure the journal's column width, are the fonts within the journal's range, are panel letters in the
journal's style, are individual data points shown, are statistics on biological replicates rather than cells,
does a micrograph have a scale bar, and does the legend contain real n and P values instead of placeholders?

## Using the helpers without an agent

The helper library works as an ordinary Python module:

```python
import sys
sys.path.insert(0, "skills/data-visualization/scripts")
import pubfig as pf

fig, axd = pf.new_figure("cell", "single", height_mm=55, mosaic=[["A", "B"]])
# ... plot into axd["A"], axd["B"] ...
pf.add_panel_labels(fig, axd, "cell")
pf.audit_figure(fig, "cell", strict=True)          # raises FigureAuditError listing every problem and its fix
for path in pf.save_figure(fig, "fig3", "cell"):   # writes the formats the journal asks for
    pf.audit_file(path, "cell", strict=True)
```

Check files you already have from the command line:

```bash
python skills/data-visualization/scripts/check_figure.py fig3.pdf fig3.tiff --journal cell
python skills/data-visualization/scripts/check_figure.py --list      # list the built-in journals
```

In R, `source("skills/data-visualization/scripts/journal_theme.R")` gives `theme_journal()`, `save_journal()`, `scale_colour_okabe()` and `panel_tags()`.

`SKILL.md` lists every helper. `references/figure_types.md` has the recipe for each figure type.

## Requirements

Python 3 with `numpy`, `pandas`, `matplotlib`, `scipy` and `pillow`. Auditing PDF files also needs `pdfplumber` and `pypdf`.

## Limitations

- Journal requirements change. The numbers were checked against the publishers' artwork guides in November 2026, and
  `references/journal_specs.md` links each guide so you can recheck before you submit.
- The audit checks size, text, layout and files. It cannot tell whether the statistics are correct or the chart type suits the data,
  and it does not catch text sitting on top of dense data or overlapping markers. Look at the preview yourself.
- Okabe–Ito orange and sky blue have similar lightness in greyscale. If the figure may be printed in black and white, add
  different marker shapes or line styles as well.

## Data

Everything in `evals/data-visualization/` is synthetic and was generated for these tests. None of it comes from patients, experiments or published studies.
