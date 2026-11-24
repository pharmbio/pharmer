---
name: data-visualization
description: "Journal-ready scientific figures. Use whenever a figure is headed for a manuscript, preprint, thesis, poster or grant, when a journal or venue is named (Nature, Cell, Science, PNAS, PLOS, eLife, Elsevier, ACS, IEEE, NeurIPS/ICLR/ICML/ACL), or when asked to make a figure publication-ready or fix its size, fonts or dpi. Covers life-science figure types: group comparisons and stats, dose-response, bulk omics (volcano, heatmap, PCA, enrichment, GWAS), single-cell and spatial (UMAP, dot plots), structural biology (pLDDT, PAE, contact maps, MD), microscopy and Cell Painting (montages, scale bars, plate QC), chemistry/drug discovery, clinical (Kaplan-Meier, forest) and ML/agent research (benchmarks with CIs, learning curves, cost-accuracy Pareto, trajectories, calibration). Provides journal size/font/dpi specs, a kernel library that builds figures at final print size and audits the figure and exported file, colour-blind checks, and a figure-type cookbook."
---

# Data visualization for journals

A figure is ready for a journal when three things hold:

1. **It fits the journal's specification.** Width, height, font, font size, line weight, file format, resolution and colour mode all match.
2. **It shows the data honestly.** The individual points are visible where n is small, the error bars are defined, the axes are honest, and image integrity is preserved.
3. **A reader can take in its message at print size**, including the roughly 8 % of men with colour-vision deficiency.

This skill turns all three into a procedure that you can check.

Kernel helpers are auto-loaded on skill load (see `kernel.py`). In another environment or in a script, use
`sys.path.insert(0, "<skill>/scripts"); import pubfig as pf` (an identical copy). For R/ggplot2, use `source("<skill>/scripts/journal_theme.R")`.

Related skills: `figure-style` holds general legibility rules and `figure-composer` handles multi-panel orchestration. This skill adds the
**journal specifications, domain figure types and file-level audits**. If both are loaded, call `apply_journal_style()` / `new_figure()`
**after** `apply_figure_style()`, so the journal sizes win.

## Workflow (follow in order)

### 1. Pin the target and the claim
- **Journal.** Use the one the user named. If none was named, use `"generic"`, say so, and mention that re-targeting is a single argument.
  `journal_spec("Nature Communications")` resolves aliases; `list_journals()` prints the table. For a journal that is not listed, look up
  its artwork guide and call `register_journal("bioinformatics", base="generic", widths_mm={...}, font_min_pt=...)`.
- **Width class.** Single column for 1–2 simple panels, double column for multi-panel figures. Choose this **before** plotting.
- **One-sentence claim per panel.** If a panel has no claim, it belongs in the supplement.

### 2. Choose the chart from the data's shape
Open `references/figure_types.md` at the matching section and follow its rules and recipe. Quick map:

| Data | Default |
|---|---|
| groups, n ≤ 15 | points + mean ± s.d. → `plot_points_summary` |
| groups, n > 15 | box + points / violin + box |
| per-cell measurements in replicates | `superplot` (stats on replicate means) |
| paired samples | slope plot |
| x–y relationship | scatter + fit + r and n; hexbin above 5k points |
| time / dose | lines + CI ribbon; log-dose with 4PL fit |
| matrix (genes × samples, features × compounds) | clustered heatmap, row z-score, diverging map centred at 0 |
| embedding (UMAP/t-SNE/PCA) | rasterised small points, `embedding_axes`, `label_clusters` |
| microscopy | greyscale channels + magenta/green merge, `add_scale_bar`, fixed display range |
| method/benchmark comparison | sorted dot plot + 95 % CI over seeds/tasks |
| survival | Kaplan–Meier + numbers at risk |

Never use: pie charts with more than 3 slices, 3D bars, dual y-axes (use two panels), radar charts, rainbow/jet colour maps,
red–green pairs, or bars with truncated axes.

### 3. Build at final print size
```python
fig, axd = new_figure("nature", "double", height_mm=90,
                      mosaic=[["a", "b", "c"], ["d", "d", "e"]])   # mm, journal rcParams, constrained layout
```
- Never draw large and shrink later, because text size is meaningful only at print size. Never use `bbox_inches="tight"`, since it changes the width.
- Do not set `fontsize=` by hand. The style sets body text at `base_pt` and tick/legend text one point smaller, within the journal's range.
  The only bigger text is the panel letters (`add_panel_labels`).
- Colours: `categorical_palette(n)` (Okabe–Ito). Define one `dict` per categorical variable (cell type → colour, condition →
  colour) and reuse it in **every** panel and figure. Use sequential `viridis`/`magma`/`cividis` for magnitudes and diverging `RdBu_r`/`vlag`
  with symmetric limits for signed values. Make your method or condition the accent colour and the references grey (`NEUTRAL_GREY`).
- Large point clouds and images: `rasterized=True` keeps the PDF small while text stays as vectors.
- **Height follows content.** Choose `height_mm` so that every row of panels is filled. A row with one small panel and empty space beside it
  should be rebalanced with `width_ratios` / mosaic spans, not padded. The audit reports blank bands (`WHITESPACE`).
- **Heatmap numbers:** use `annotate_heatmap(ax, M, "{:.0f}", journal=...)`. It writes values only if they fit the cell at a legal size and
  otherwise writes nothing. Show percentages as integers, and do not annotate more than about 8 columns per 80 mm. Shorten or wrap long category names,
  or transpose the matrix so long names run along the y-axis.
- **Colour bars and size keys:** `add_colorbar(fig, mappable, ax, label)` and `add_size_legend(ax, values, sizes, title)`. Never place them
  with `fig.add_axes`, `inset_axes` or `cax=`. Constrained layout cannot see hand-placed axes, so their labels end up clipped at the edge.
- **Size encodings (dot plots, bubbles):** set the size scale so the largest marker's diameter stays below the grid spacing
  (`s_max ≈ (0.9 * spacing_pt)**2`). The audit does not detect overlapping markers, so check this in the preview.
- **Category tick labels** (task names, cell types, conditions): after setting them, call `fit_tick_labels(ax, "x")`. It keeps them
  horizontal if they fit, otherwise wraps at word boundaries, then rotates 45°, then 90°. Never split words by hand ("visu alization").
- **Log axes** (cost, concentration, p-values): `clean_log_axis(ax, "x", fmt=lambda v: f"${v:g}")` gives plain 1-2-5 labels in place of
  `2×10⁻²`-style clutter.
- **Groups on a shared embedding (condition, sample, batch):** draw one small panel per group, showing that group's cells
  coloured on top of all cells in light grey, so the overlap is visible and no group hides another. If they must share one panel,
  plot in a shuffled order and say so in the legend. Never plot group A and then group B on top of it.

### 4. Annotate the panels
- **Axis labels** give the quantity and unit in parentheses: "Concentration (µM)", "log2 fold change", "Time (h)". Use sentence case.
- **No chart titles** inside panels unless they label a column of small multiples. The message goes in the legend.
- **Direct labels** beat legends: label lines at their ends and clusters at their centres. For embeddings call
  `label_clusters(ax, xy, labels, colors=palette_dict)`. With `colors=` it labels the separated clusters directly and moves every
  stack of touching clusters into a counted legend beside the axes ("Treg (305)"). Always pass `colors=` when clusters touch. If a legend is needed, put it without a frame where it hides no data.
- **Statistics on the plot**: `add_significance(ax, x1, x2, y, format_p(p))`, with exact P values.
- **Panel letters**: `add_panel_labels(fig, axd, journal)` gives lowercase bold for Nature, uppercase for Cell/Science/PNAS/PLOS/eLife,
  and (a) for Elsevier/ACS/IEEE/ML. Letters in a row are aligned.
- **Scale bars** on every micrograph (`add_scale_bar(ax, 10, pixel_size_um)`). State "Scale bar, 10 µm" in the legend if the bar is unlabelled.

### 5. Audit, fix and re-audit (mandatory)
```python
audit_figure(fig, journal, strict=True)    # size, fonts, text overlaps (incl. rotated ticks), clipping, blank bands, thin lines, rainbow cmaps
paths = save_figure(fig, "fig2", journal)  # journal's formats: vector PDF (Type 42 fonts) + TIFF/PNG at the right dpi, RGB
for p in paths: audit_file(p, journal, strict=True)   # the exported file itself: page size, live text sizes, Type 3 fonts, dpi
check_legend(legend, fig, strict=True)     # no placeholders; legend panel letters == figure panel letters
cvd_preview(fig)                           # QC image -> qc/cvd_preview.png (never next to the deliverables)
check_palette(list(colors.values()))       # min ΔE under deutan/protan/tritan vision
```
**Write the audit as a gate.** If you are writing a script you will not see run, as in a chat answer or a batch job, use
`strict=True` everywhere. A failing audit then raises `FigureAuditError` listing every issue, and that message comes back to you as the error
to fix. **Each issue line ends with the fix to apply** (for `WHITESPACE` the exact `height_mm` to use, and for overlapping ticks
`fit_tick_labels`). Apply every one before resending. Do not wrap the audits in `try/except`, and do not drop `strict=True` to make the script finish. Fix the cause instead: shorten labels,
change `height_mm`, transpose, or drop the heatmap numbers.

**Keep QC out of the deliverables.** Previews, CVD strips and test renders go in `qc/`. The only files next to the
figure are the submission files, `preview.png`, the legend and the source data.

When you can view images, also **look at the rendered PNG** at 100 %. Check for:
- overlapping labels, a legend covering data, labels cut off,
- tick labels that collide or are rotated more than 45°,
- empty space taking up more than ~25 % of a panel, or panels with unequal font sizes,
- colours that match the dict across panels,
- that the claim in step 1 is visible within 5 seconds.

The audit cannot see whether the statistics are right or the chart choice is apt. You check those.

### 6. Deliver
- Files in the journal's required formats (`save_figure`): **PLOS = TIFF**, Cell/Science/PNAS/Elsevier/eLife = PDF + TIFF,
  Nature = PDF (+ PNG preview), ML venues = PDF.
- **Figure legend** (`legend_template(...)`). **Build it in the same script from the same variables you plotted:** take the panel letters from
  the list you passed to `add_panel_labels`, the n values from `len(...)` or `groupby().size()`, and the P values from the test you ran. Never type a
  number into the legend by hand, and never leave a placeholder ("n = X"). It contains a bold title sentence stating the finding, then one clause per panel, then
  what the points, centre and error bars are, the exact n with its unit ("n = 3 independent experiments, 312 cells"),
  the statistical test with exact P values and multiple-comparison correction, and any image processing (the same display range for all
  conditions; "Scale bar, 20 µm").
- **Source data**: a CSV of the plotted values for each panel (required by eLife and Nature, and good practice everywhere).
- Report the audit result (e.g. "183 × 120 mm, text 6–7 pt Arial, Type 42, 450 dpi — all checks pass").

## Non-negotiables (integrity)
- Adjust brightness and contrast linearly on the **whole** image, applied equally to controls. No cloning, no local edits, and **no AI-generated or
  AI-altered images** of data.
- Keep uncropped originals of blots and gels. Mark splices with lines. Separate juxtaposed fields with visible gaps.
- Never smooth, interpolate or subsample data without saying so. Never drop outliers silently, and if any are excluded, give the rule in the legend.
- Bars start at 0. A log axis is labelled as log.
- n means independent biological replicates unless stated otherwise. Cells or fields are technical units, so do not inflate n with them (use SuperPlots).

## Journal quick sheet (details and sources: `references/journal_specs.md`)

| Journal key | Widths (mm) | Max h (mm) | Text (pt) | Letters | Export |
|---|---|---|---|---|---|
| nature | 89 / 120–136 / 183 | 170 | 5–7, Arial/Helvetica | **a** 8 pt | PDF (editable text); images ≥300 dpi |
| cell | 85 / 114 / 174 | ~225 | 6–8, Arial | **A** | PDF/TIFF; 300/500/1000 dpi |
| science | 90 / ≤144 / 184 | 199 | 6–8, Myriad/Helvetica | **A** 9 pt | PDF/TIFF ≥300 dpi |
| pnas | 87 / 114 / 178 | 225 | 6–12 | **A** | TIFF/EPS/PDF; 300/600/1000 ppi |
| plos | any 66.8–190.5 (132 text col) | 222 | 8–12, Arial/Times | **A** | **TIFF only** 300–600 dpi, ≤10 MB |
| elife | ≥100 (≥200 full page) | 1 page | 6–10 | **A** | TIFF/PDF ≥300 dpi + source data |
| elsevier | 90 / 140 / 190 | 240 | ~7 (≥6) | (a) | TIFF/PDF; 300/500/1000 dpi |
| acs | ≤84.6 / 106–178 | 233 incl. caption | ≥4.5 (aim ≥6) | (a) | TIFF/PDF; 300/600/1200 dpi |
| neurips · icml · acl | 139.7 · 82.6/171.5 · 77/160 | page | ~caption size | (a) | PDF, Type 42 |

## Helper index (kernel.py / scripts/pubfig.py)
`journal_spec`, `list_journals`, `register_journal`, `apply_journal_style`, `new_figure`, `figure_width_mm`, `mm_to_in`,
`categorical_palette`, `OKABE_ITO`, `TOL_MUTED`, `NEUTRAL_GREY`, `plot_points_summary`, `superplot`, `format_p`,
`add_significance`, `label_clusters`, `embedding_axes`, `channel_composite`, `add_scale_bar`, `add_panel_labels`,
`audit_figure`, `save_figure`, `audit_file`, `check_palette`, `simulate_cvd`, `cvd_preview`, `legend_template`,
`annotate_heatmap`, `clean_log_axis`, `fit_tick_labels`, `add_colorbar`, `add_size_legend`, `check_legend`, `FigureAuditError` (raised by any check with `strict=True`).
CLI: `python scripts/check_figure.py fig.pdf fig.tiff --journal plos`. R: `theme_journal()`, `save_journal()`, `pt_lw()`,
`scale_colour_okabe()`, `panel_tags()` in `scripts/journal_theme.R`.

## Known limits
- Okabe–Ito separates 8 colours for colour-vision deficiency, but orange (#E69F00) and sky blue (#56B4E9) have similar lightness in greyscale. If a figure may
  be printed in greyscale, add shape or line-style redundancy.
- `audit_figure` checks text against text (rotated text included) and blank bands. It does not detect text sitting over dense data or
  a misleading chart choice, so a visual check is still needed whenever you can view images.
- `audit_figure` does not check marker sizes or whether the statistics are correct.
- Keep scripts compact: call the helpers rather than re-implementing them. Long scripts are the most common cause of truncated answers.
- Journal numbers change. `references/journal_specs.md` lists the source URLs to re-check before final submission.
