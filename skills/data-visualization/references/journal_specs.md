# Journal figure specifications (verified November 2026)

All numbers below come from the publisher's own artwork guide. Each row lists its source. Publishers revise these
guides, so when a submission is imminent, open the current guide (URLs at the bottom) and, if anything changed, update
`JOURNAL_SPECS` at runtime with `register_journal(key, base=..., **overrides)`.

Units: 1 in = 25.4 mm = 72 pt. "Width" means the printed width of the whole figure, including all panels and the panel letters.

## Size and type

| Key | Journal family | Column widths | Max height | Text | Panel letters | Fonts |
|---|---|---|---|---|---|---|
| `nature` | Nature, Nature Methods/Biotech/Genetics/…, Nat Commun, Commun Biol, npj, Sci Rep | 89 mm single · 120–136 mm 1.5 · 183 mm double | 170 mm (so the legend fits on the page; 247 mm is the absolute page depth) | 5–7 pt | 8 pt **bold lowercase** (a, b, c) | Arial or Helvetica |
| `cell` | Cell, Mol Cell, Cell Rep, Neuron, Immunity, iScience, Curr Biol, … | 85 mm · 114 mm · 174 mm | full page, with the legend on the same page (~225 mm) | 6–8 pt | bold **uppercase** (A, B, C) | Arial |
| `science` | Science, Sci Adv, Sci Transl Med, Sci Signal, Sci Immunol | 90 mm (1 col) · ≤144 mm (intermediate) · 184 mm (2 col) | 199 mm (19.9 cm depth) | 8 pt default, ≥6 pt | 9 pt **bold uppercase** | Myriad Pro (preferred), Helvetica, Arial |
| `pnas` | PNAS, PNAS Nexus | 87 mm (8.7 cm) · 114 mm · 178 mm | 225 mm | 6–12 pt after reduction, consistent | bold uppercase | Arial, Helvetica |
| `plos` | PLOS ONE / Biology / Comp Biol / Genetics / Pathogens / Medicine | any width 66.8–190.5 mm (789–2250 px at 300 dpi); text column 132 mm | 222.3 mm (2625 px at 300 dpi) | 8–12 pt | bold uppercase (house convention) | Arial, Times, Symbol |
| `elife` | eLife | ≥100 mm wide (≥200 mm for full-page figures) | single page | no explicit rule; 6–10 pt by convention | bold uppercase (house style) | sans serif |
| `elsevier` | Elsevier journals (generic) | 30 mm minimum · 90 mm single · 140 mm 1.5 · 190 mm double | ~240 mm | ~7 pt; sub/superscripts ≥6 pt | per journal; lowercase in parentheses is common | Arial, Helvetica, Times, Courier, Symbol |
| `acs` | JACS, J Med Chem, ACS Chem Biol, JCIM, Anal Chem, … | single ≤3.33 in (84.6 mm; 3.25 in preferred) · double 4.17–7 in (106–178 mm) | 9.167 in (232.8 mm) **including the caption** | ≥4.5 pt (JACS Au / ACS Materials Au: ≥8 pt); aim for ≥6 pt | per journal | Arial, Helvetica |
| `ieee` | IEEE Transactions | ~3.5 in single · ~7.16 in double (template) | page | 8–10 pt | (a), (b) — usually in captions | Times / Helvetica |
| `neurips` | NeurIPS, ICLR, COLM, TMLR | text width 5.5 in (139.7 mm), single column | page | match the caption (~8–9 pt) | (a), (b) | free; Type 42 / Type 1 |
| `icml` | ICML, CVPR, ICCV, AAAI | column 3.25 in · text 6.75 in (CVPR 6.875 in) | page | ~7–9 pt | (a), (b) | free |
| `acl` | ACL, EMNLP, NAACL | column 7.7 cm · text 16 cm | page | ~7–9 pt | (a), (b) | free |
| `generic` | unknown target, preprint, thesis | 89 / 136 / 183 mm | 170 mm | 6–8 pt | bold lowercase | Arial |

## Resolution, format, colour

| Key | Raster resolution at final size | Accepted files | Colour | Other rules |
|---|---|---|---|---|
| `nature` | images ≥300 dpi (450 preferred in the guide) | AI, EPS, PDF (vector, **editable text**), TIFF/JPEG for photos | RGB | Line weights 0.25–1 pt. Text must not be outlined. Each figure on its own page/file. Keep text out of images where possible. |
| `cell` | 300 dpi colour/greyscale · 500 dpi combination (image + text) · 1000 dpi line art | PDF, EPS, AI, TIFF | RGB | Figure and legend must fit on one page. Titles go in the legend, not the image. Graphical abstract: 1200 × 1200 px (min), Arial 8–12 pt. |
| `science` | ≥300 dpi | PDF, EPS, AI, TIFF | RGB | Panel labels 9 pt bold caps. Units in parentheses. Avoid red/green. |
| `pnas` | 300 ppi photos · 600–900 ppi combination · 1000–1200 ppi line art | TIFF, EPS, PDF, PPT | RGB | Text 6–12 pt and consistent across figures. |
| `plos` | 300–600 dpi (higher is resized) | **TIFF (LZW) or EPS only** | RGB, 8-bit | ≤10 MB per file. No alpha layers. Figures are checked by the PACE tool. Text must be within 8–12 pt. |
| `elife` | ≥300 dpi | TIFF (8-bit), JPG, EPS, AI, PDF | RGB | One page per figure. Source data file per figure ("Figure 1—source data 1"). Supplements as "Figure 1—figure supplement 1". Uncropped blots/gels required. |
| `elsevier` | 300 dpi halftone · 500 dpi combination · 1000 dpi line art | TIFF, EPS, PDF, JPEG (photos) | RGB | Lettering ~7 pt. Avoid very thin lines. |
| `acs` | 300 dpi colour · 600 dpi greyscale · 1200 dpi line art | TIFF, PDF, EPS | RGB | Lines ≥0.5 pt. Contrast 4.5:1 for text and 3:1 for graphics (WCAG). TOC/abstract graphic 3.25 × 1.75 in. |
| ML venues | vector PDF preferred | PDF (Type 42 or Type 1 fonts, no Type 3), PNG for photos | RGB | Build at `\columnwidth` / `\linewidth` so text is not rescaled. |

## Cross-publisher rules worth enforcing everywhere

1. **Build at final size.** Text size is only meaningful at the printed width. A 6 pt label on a 300 mm canvas scaled to
   89 mm prints at about 1.8 pt.
2. **Editable text in vector files.** In matplotlib set `pdf.fonttype = 42` (Type 3 fonts get flagged). Never outline text.
3. **RGB, not CMYK**, unless the journal asks for CMYK at proof stage.
4. **Colour-blind safety.** Nature, Science and ACS name this explicitly. Avoid red/green pairs. Use magenta/green for
   two-channel overlays and perceptually uniform colour maps (viridis, cividis, magma; diverging RdBu_r/vlag centred on 0).
5. **Show the data.** Nature-portfolio reporting summaries ask for individual data points when n is small, for error bars that
   say whether they are s.d., s.e.m. or CI, for exact n with its unit (cells, mice, independent experiments), and for the
   test used, with exact P values.

## Image integrity (Nature portfolio policy; Cell, Science, eLife and PLOS are equivalent)

- Brightness, contrast and colour adjustments are allowed only when applied to the **whole image, controls included**.
  They must not hide, remove or introduce features.
- No cloning, healing, or selective enhancement of one region. **No generative-AI-created or AI-altered images** in research figures.
- Gels and blots: keep the **uncropped, unprocessed originals** and provide them as supplementary source data.
  Mark splices with dividing lines. Do not combine exposures without saying so.
- Images placed side by side from different fields, samples or exposures must be visibly separated (gap or line) and declared in the legend.
- Comparative images use identical acquisition **and** display settings. State the LUT/range when it matters.
- Microscopy: every image needs a scale bar (not magnification), and the bar length goes in the image or the legend.
- Keep the raw files. Journals can ask for them, and eLife and Nature require source data for graphs.

## Sources (accessed November 2026)

- Nature: *Guide to preparing final artwork* — https://www.nature.com/documents/nature-final-artwork.pdf ;
  Research Figure Guide — https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/ ;
  Image integrity — https://www.nature.com/nature-portfolio/editorial-policies/image-integrity
- Cell Press: https://www.cell.com/information-for-authors/figure-guidelines ;
  Graphical abstract guide — https://www.cell.com/pb/assets/raw/shared/figureguidelines/GA_guide.pdf
- Science family: *Guide to preparing figures* (2026) —
  https://www.science.org/cms/asset/76887697-528f-4a22-afea-cee904504e76/sciadv_guide_to_preparing_figures_2026.pdf
- PNAS: Digital Art Guidelines (author centre, pnas.org)
- PLOS ONE: https://journals.plos.org/plosone/s/figures
- eLife: Author Guide — https://submit.elifesciences.org/html/eLife_Author_Guide.pdf
- Elsevier: Artwork and media instructions (elsevier.com/authors/policies-and-guidelines/artwork-and-media-instructions)
- ACS: Author guidelines, graphics section — https://researcher-resources.acs.org/publish/author_guidelines
- IEEE / ML venues: the official LaTeX templates. Widths are derived from `\columnwidth` / `\textwidth`.

Values marked "convention" or "template" are not stated in the publisher guide. They are safe defaults, so confirm them per journal.
