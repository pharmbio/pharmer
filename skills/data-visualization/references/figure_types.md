# Figure-type cookbook

Each entry gives three things: **when to use it**, the **rules that reviewers and journals check**, and a **minimal
recipe** built on the kernel helpers (`new_figure`, `plot_points_summary`, `superplot`, `embedding_axes`,
`label_clusters`, `annotate_heatmap`, `clean_log_axis`, `channel_composite`, `add_scale_bar`, `add_panel_labels`, `audit_figure`, `save_figure`).
The recipes assume `apply_journal_style()` has already set sizes, so never pass `fontsize=` larger than the journal maximum.

Contents: 1 Group comparisons · 2 Distributions · 3 Relationships · 4 Time course & dose–response · 5 Bulk omics &
genomics · 6 Single-cell & spatial · 7 Protein & structural biology · 8 Microscopy & Cell Painting · 9 Chemistry & drug
discovery · 10 ML / AI-agent research · 11 Clinical & epidemiology · 12 Networks, flows, schematics

---

## 1. Group comparisons

| Data | Use | Avoid |
|---|---|---|
| n ≤ ~15 per group | every point + mean ± s.d. (`plot_points_summary`) | bar + error bar alone ("dynamite plot") |
| n ~15–100 | box plot (median, IQR, 1.5×IQR whiskers) **with points overlaid** | violin without the points |
| n > 100 | violin or box; points rasterised or as a strip | 10,000 overlapping dots drawn as vectors |
| cells nested in replicates | **SuperPlot** (`superplot`), with stats on the replicate means | treating cells as n (pseudoreplication) |
| paired / before–after | slope plot (lines join each subject) | unpaired dots |
| counts / proportions | bars starting at 0, ideally with points; stacked 100 % bars for composition | bars with a truncated y-axis |

Rules:
- In the legend, define the centre and the spread ("mean ± s.d."), the exact n **and its unit**, the test, and exact P values.
- Bars must start at zero. Dots, boxes and lines may use a truncated axis.
- Prefer exact P values (`format_p`) to stars. If stars are used, define them in the legend.
- Never let the colour encode the same thing as the x-axis **and** need a legend. Use one or the other.

```python
fig, ax = new_figure("cell", "single", height_mm=55)
st = plot_points_summary(ax, {"WT": wt, "KO": ko, "KO+rescue": res}, error="sd")
ax.set_ylabel("Relative mRNA (2$^{-ΔΔCt}$)")
add_significance(ax, 0, 1, ymax*1.05, format_p(p_ko))
```

SuperPlot (for imaging or per-cell measurements):
```python
s = superplot(ax, df, x="condition", y="nuclear_area", replicate="experiment")
# statistics: t-test / mixed model on s[g]["rep_means"], n = independent experiments
```

## 2. Distributions

- Histogram: choose the bin width deliberately and state it if it matters. For comparing groups, use overlaid **step**
  histograms or ECDFs, not stacked bars.
- ECDF: no binning choices, and good for comparing more than two distributions.
- Ridgeline: many groups along one axis (e.g. expression across 20 cell types).
- Log scale for heavy-tailed data (counts, intensities, concentrations). Label it "log10 (x)" or use a log axis with real-value ticks.

## 3. Relationships

- Scatter: give the r or ρ value **and** n. Show the fit with its CI band, and say whether the fit is OLS or robust.
- Use an equal-aspect identity line when comparing measurements of the same quantity (predicted vs observed).
- Use a Bland–Altman plot for agreement between methods. Correlation is not agreement.
- More than about 5,000 points: use `rasterized=True`, small `s`, `alpha`, or `hexbin`/2D density.
- Correlation matrices: diverging map fixed at −1 to 1 (`vmin=-1, vmax=1`), with clustered order if helpful.

## 4. Time course & dose–response

- Show replicate traces faintly, with the mean line and a CI ribbon. Mark the treatment time with a vertical line.
- Dose–response: log10 concentration on x with real units (nM or µM). Fit a 4-parameter logistic and report IC50/EC50 with a 95 % CI.
  Show the points at each concentration (mean ± s.d.) and keep the fit curve within the tested range only.
- Survival: see §11.
- Many conditions: use small multiples with shared axes rather than eight overlapping lines with a legend. If lines must share a panel,
  label them directly at the line ends.

```python
from scipy.optimize import curve_fit
def ll4(x, bottom, top, logic50, hill): return bottom + (top-bottom)/(1+10**((x-logic50)*hill))
popt, pcov = curve_fit(ll4, np.log10(conc), resp, p0=[0,100,np.log10(np.median(conc)),1])
xx = np.linspace(np.log10(conc.min()), np.log10(conc.max()), 200)
ax.plot(10**xx, ll4(xx, *popt)); ax.set_xscale("log"); ax.set_xlabel("Compound (µM)")
```

## 5. Bulk omics & genomics

**Volcano plot**: x = log2 fold change, y = −log10 (adjusted P). Draw dashed threshold lines and give their values in the legend.
Use grey for non-significant genes and two colours for up and down. Label only the top ~10 genes, with leader lines
(`adjustText` if available, otherwise manual offsets). Rasterise the point cloud (`rasterized=True`) and keep the text as vector.
Give the counts up and down in the legend or a corner annotation.

**MA plot**: mean expression (log) against log2FC. Useful for showing low-count shrinkage.

**Heatmap**:
- Z-score rows (genes) when patterns matter more than absolute level, and say so in the colour-bar label ("Row z-score").
- Diverging colour map centred on 0 (`RdBu_r`, `vlag`) for z-scores and fold changes. Sequential (`viridis`, `magma`) for
  non-negative values such as expression or counts.
- Clip at symmetric limits (e.g. ±2.5) and say so in the legend.
- Annotate column groups with a colour strip and a legend. Clustering must state the distance and linkage.
- More than about 50 rows: drop the individual row labels and label clusters or selected genes instead.
- Use `seaborn.clustermap(..., figsize=(mm_to_in(w), mm_to_in(h)))`, then `audit_figure(g.fig)`.

**PCA**: axis labels "PC1 (34.2 %)", equal aspect, colour by condition and shape by batch. Show the scree plot in supplementary.

**Enrichment dot plot**: y = terms ordered by significance, x = gene ratio or NES, size = gene count, colour = −log10 FDR
on a sequential map. Keep it to 10–20 terms and wrap long names (`textwrap.fill(term, 40)`).

**GWAS**: Manhattan plot with alternating chromosome greys, the genome-wide line at 5 × 10⁻⁸ and lead SNPs labelled,
plus a QQ plot showing λGC.

**Genome tracks / coverage**: shared x-axis in genomic coordinates (Mb), one track per sample, with the gene model underneath.

**Set overlaps**: Venn diagrams for 2–3 sets only. For four or more, use an UpSet plot (`upsetplot`).

**Oncoprint / mutation landscapes**: genes in rows, samples in columns, with a fixed colour per alteration type and the frequency bar on the right.

## 6. Single-cell & spatial

**UMAP / t-SNE embeddings**:
- No ticks or numbers, because the coordinates are meaningless. Use `embedding_axes(ax)` corner arrows. Equal aspect.
- Points: `s` around 0.5–3, depending on n and the panel area, with `linewidths=0, rasterized=True`. Plot in a **random order**
  (shuffle) so the last-drawn cluster does not hide the others.
- Clusters: up to 8 use Okabe–Ito. Beyond that, no palette stays separable by colour alone, so put **cluster labels on the
  plot** (`label_clusters`) and drop the legend. Use a meaningful order, with related types in similar hues.
- Keep the same cell-type colours across every panel and figure in the paper: define the mapping once (`dict`) and reuse it.
- State the number of cells and samples in the panel or the legend.
- Condition, sample or batch on the embedding: use small multiples, with each group coloured over all cells in grey (`ax.scatter(all, c=NEUTRAL_GREY)` then the group on top). A single panel coloured by condition hides whichever group is drawn first.

**Feature plots (expression on the embedding)**: sequential map from light grey to a strong colour (e.g. `["#D9D9D9", ...]` or
`viridis`). Draw high-expressing cells **on top** (sort by value). Clip the colour scale at the 99th percentile. Use the same
colour scale when comparing conditions, and give the colour bar a label ("log-normalised expression").

**Marker dot plot** (better than violins for many genes): genes on x grouped by cell type, cell types on y. Dot size =
% of cells expressing, colour = scaled mean expression. Both legends are needed: the size legend uses 3 reference sizes.

**Composition**: stacked 100 % bars **per sample** (not per condition pooled), or per-sample dots for each cell type
with a differential-abundance test that respects samples (e.g. scCODA or propeller).

**Trajectory / pseudotime**: embedding coloured by pseudotime (`viridis`), plus gene-trend lines along pseudotime with CI bands.

**Spatial transcriptomics**: tissue coordinates with equal aspect, a scale bar in µm (`add_scale_bar`), and the H&E image
under the spots if relevant. Same colour mapping as the UMAP.

```python
fig, axd = new_figure("nature", "double", height_mm=75, mosaic=[["umap", "umap", "dot", "dot", "dot"]])
ax = axd["umap"]; idx = rng.permutation(len(adata))
ax.scatter(*emb[idx].T, s=1, c=[ct_colors[c] for c in labels[idx]], linewidths=0, rasterized=True)
ax.set_aspect("equal"); embedding_axes(ax); label_clusters(ax, emb, labels)
```

## 7. Protein & structural biology

**Structure renders** (PyMOL, ChimeraX, Mol*):
- White background, orthographic projection, ray-traced or ambient-occlusion lighting, output ≥300 dpi **at the final panel size**.
- Colour by chain or domain (the same colours as the domain-architecture schematic), by pLDDT, or by a property (conservation, B-factor).
- AlphaFold pLDDT colours (the EBI/DeepMind standard): very high > 90 `#0053D6`, confident 70–90 `#65CBF3`, low 50–70
  `#FFDB13`, very low < 50 `#FF7D45`.
- Label key residues with one-letter code and number (e.g. "K48"). Show the ligand as sticks with a contrasting element colour and
  dashed lines for H-bonds. Distances in Å.
- Put the axis of view in the legend, or include an orientation inset when several views are shown.
- ChimeraX: `set bgColor white; lighting soft; graphics silhouettes true; save fig.png width 2000 supersample 3`.
- PyMOL: `bg_color white; set ray_opaque_background, 1; set antialias, 2; png fig.png, width=2000, dpi=600, ray=1`.

**pLDDT along the sequence**: line plot with the four confidence bands shaded in the colours above, and domain boundaries marked on top.

**PAE matrix**: `Greens_r` 0–30 Å (AlphaFold DB convention), equal aspect, residue index on both axes, chain boundaries as lines, and a colour bar
"Expected position error (Å)".

**Contact or distance maps**: equal aspect, sequential map with the colour bar in Å. For a contact-map comparison, show the predicted and observed maps in opposite triangles.

**Domain architecture / lollipop (mutations)**: a horizontal bar to scale (amino-acid ruler), domains as rounded boxes coloured
consistently with the structure, mutation lollipops with height = count and colour = mutation class.

**Sequence logos / MSA conservation**: `logomaker`. Hydrophobicity- or chemistry-based colour scheme, with the position numbering of
the reference sequence.

**MD simulations**: RMSD/RMSF against time or residue for each replicate (thin lines, mean thick), with the time unit (ns).
Distance or angle histograms by replicate. Free-energy landscapes as a 2D contour map (`magma`) with the colour bar in kcal mol⁻¹.

**Binding & biophysics**: binding isotherms with the fit and K_D ± error. SPR sensorgrams with the concentration series in
sequential colours (light = low). CD spectra in mdeg or MRE against nm. DSF melting curves with Tm marked.

**Mass spectrometry**: stick spectra (m/z vs relative intensity) with labelled b/y ions, and proteomics volcano plots as in §5.

```python
def plddt_colors(v): return np.select([v>90, v>70, v>50], ["#0053D6","#65CBF3","#FFDB13"], "#FF7D45")
im = ax.imshow(pae, cmap="Greens_r", vmin=0, vmax=30); ax.set_aspect("equal")
cb = fig.colorbar(im, ax=ax, shrink=0.8); cb.set_label("Expected position error (Å)")
```

## 8. Microscopy & Cell Painting

**Microscopy panels**:
- A scale bar on every image, or on the first image of a uniform montage with the legend saying "Scale bar, 10 µm (all panels)".
  Use `add_scale_bar(ax, 10, pixel_size_um)`.
- Single channels in **greyscale** (the eye resolves grey best). Merges in **magenta/green** (or magenta/green/cyan) rather than
  red/green. Give the LUT and channel in labels above the columns ("DAPI", "LC3", "Merge").
- Display settings: the same min/max for every condition that is being compared (compute from controls or pooled data,
  never per image), and gamma 1 unless declared. Raw intensities are quantified, never the display-adjusted ones.
- Insets: draw a box in the main image and the magnified inset with its own scale bar. Keep the inset's aspect.
- Separate juxtaposed images with a white gap of about 1 mm (`wspace`) and never butt different fields together.
- Use `imshow(..., interpolation="nearest")` and do not resample the original pixels. Images in vector PDFs are embedded rasters,
  so check that their effective dpi is ≥300 at print size.

**Cell Painting** (5 dyes / 6 compartments: DNA–Hoechst, ER–concanavalin A, RNA/nucleoli–SYTO 14, AGP actin–Golgi–plasma
membrane–phalloidin + WGA, Mito–MitoTracker):
- Example images: one row per perturbation, columns = the 5 channels in greyscale + 1 composite. The same display range per channel
  across all rows. Put the compound and concentration as row labels, with scale bars.
- Profiles: per-well features normalised to the negative control (DMSO) with robust z-scores (median/MAD), after feature selection.
- Profile heatmap: perturbations × features, diverging colour map centred at 0, clipped at ±3–5. Features grouped by compartment and
  feature class with a colour strip (Cells / Cytoplasm / Nuclei × AreaShape / Intensity / Texture / Granularity / Correlation).
- Embedding of well-level profiles (UMAP) coloured by MoA (≤8 colours, or direct labels) with DMSO in grey.
- Reproducibility: replicate correlation against a null distribution (percent replicating) or mAP per compound. Show it as a histogram
  with the null overlaid, or as a ranked dot plot.
- Plate QC: plate-layout heatmaps (rows A–P × columns 1–24) of cell count or of a key feature, used to reveal edge and drift effects.
- Phenotypic dose–response: induction or phenotypic distance against log concentration (§4).

```python
fig, axes = new_figure("plos", 132, height_mm=70, nrows=3, ncols=6, gridspec_kw=dict(wspace=0.02, hspace=0.02))
for r, cmpd in enumerate(cmpds):
    for c, ch in enumerate(CHANNELS):
        axes[r, c].imshow(imgs[cmpd][ch], cmap="gray", vmin=lims[ch][0], vmax=lims[ch][1], interpolation="nearest")
    axes[r, 5].imshow(channel_composite([imgs[cmpd][k] for k in ("DNA", "AGP", "Mito")]))
for a in axes.ravel(): a.set_axis_off()
add_scale_bar(axes[0, 0], 20, 0.656)
```

## 9. Chemistry & drug discovery

- Chemical structures: RDKit with ACS 1996 settings (`rdMolDraw2D`, `drawOptions().bondLineWidth`, fixed bond length), the same
  scale across all structures, and SVG/PDF for vector. Do not stretch structures.
- SAR grids/tables: core scaffold + R-group table, with activity as pIC50 and a sequential colour (not traffic-light red/green).
- Chemical space: UMAP or t-SNE of fingerprints. Colour by series or activity and keep the reference sets (approved drugs) in grey.
- Property distributions with the drug-likeness limits as dashed lines (MW 500, cLogP 5, TPSA 140).
- Reaction schemes: ChemDraw ACS-1996 style. Reagents above the arrows and conditions below.
- ACS TOC graphic: 3.25 × 1.75 in, readable at that size, without the article title.

## 10. ML / AI-agent research figures

- **Benchmark comparison**: dot plot (or bars starting at 0) with **95 % CIs over seeds or bootstrap over tasks**. Give the number
  of seeds/tasks in the legend. Sort methods by score. Your method gets the accent colour and baselines get greys.
- **Per-category results**: heatmap (method × task category) with values annotated (2 significant digits) and a sequential
  colour map at fixed limits (0–1 or 0–100 %). Or use small multiples.
- **Learning / scaling curves**: mean line ± s.d. ribbon over seeds. A log x-axis for compute/data/parameters, and a log-log axis when
  claiming a power law (report the fitted exponent). Label lines directly at their ends.
- **Cost–performance**: scatter of accuracy against cost (USD, tokens, latency) on a log x-axis, with the Pareto frontier drawn as a step line
  and points labelled directly.
- **Agent trajectories**: Gantt/timeline of tool calls per episode (colour = tool type), distribution of steps to success,
  a Sankey/alluvial plot for failure modes, and a stacked bar of error categories per method.
- **Classification**: confusion matrix (row-normalised, with counts annotated and a sequential map), ROC and PR curves with
  AUC ± CI in the legend, and a calibration (reliability) diagram with the identity line and the ECE value.
- **Human evaluation / Likert**: diverging stacked bars centred on neutral.
- **Win-rate matrices**: diverging colour map centred at 50 %.
- Avoid radar charts: area exaggerates differences and the axis order is arbitrary. Avoid 3D bars.
- Venue fonts: build at `\columnwidth` (ICML 3.25 in) or `\linewidth` (NeurIPS 5.5 in) so that figure text matches the caption size.

## 11. Clinical & epidemiology

- Kaplan–Meier: step curves with censor ticks and a **numbers-at-risk table** under the x-axis aligned with the time ticks.
  Give the HR (95 % CI) and log-rank P (`lifelines`).
- Forest plot: estimate ± CI on the log scale for ratios, a vertical null line at 1 (or 0), and the n per subgroup in a text column.
- ROC with AUC (95 % CI) and the operating point marked.
- CONSORT/flow diagrams: boxes with n at each step (a schematic tool or `matplotlib` patches).

## 12. Networks, flows, schematics

- Networks: a deterministic layout (`seed`), node size or colour mapped to a stated variable, edge width for weight, and labels for hubs only.
  More than about 200 nodes: show modules, not the hairball.
- Sankey/alluvial plots for flows between categorical states (e.g. cell-state transitions, agent failure modes).
- Schematics and graphical abstracts: draw in vector software (or matplotlib patches) at final size using the same font as the data panels.
  Icons from consistent sets (BioIcons, Servier, BioRender with a licence statement). **No AI-generated imagery** for scientific content
  (Nature, Science and Cell policies).
