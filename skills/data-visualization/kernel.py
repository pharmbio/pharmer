# data-visualization skill — helper library (auto-loaded into the python kernel on skill load).
# Portable copy for any Python env: scripts/pubfig.py  (`import pubfig as pf`).
# Journal numbers verified against publisher guides, Nov 2026 — see references/journal_specs.md.
import math
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

MM_PER_INCH = 25.4

# Okabe-Ito (Wong, Nat Methods 2011) — ordered so the first colours are the most separable.
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#CC79A7", "#F0E442", "#000000"]
TOL_MUTED = ["#332288", "#88CCEE", "#44AA99", "#117733", "#999933", "#DDCC77", "#CC6677", "#882255", "#AA4499"]
TOL_LIGHT = ["#77AADD", "#EE8866", "#EEDD88", "#FFAABB", "#99DDFF", "#44BB99", "#BBCC33", "#AAAA00"]
NEUTRAL_GREY = "#BBBBBB"
BAD_CMAPS = ["jet", "jet_r", "rainbow", "rainbow_r", "hsv", "gist_rainbow", "nipy_spectral", "gist_ncar",
             "prism", "flag", "Spectral", "Spectral_r", "gist_stern", "CMRmap", "brg"]

# widths_mm: named column widths. width_ranges_mm: any width inside these ranges is also valid.
JOURNAL_SPECS = {
    "nature": {"name": "Nature & Nature Portfolio", "widths_mm": {"single": 89, "onehalf": 120, "double": 183},
               "width_ranges_mm": [[120, 136]], "max_height_mm": 170, "fonts": ["Arial", "Helvetica"],
               "font_min_pt": 5, "font_max_pt": 7, "base_pt": 7,
               "panel_label": {"case": "lower", "size": 8, "weight": "bold", "parens": False},
               "line_min_pt": 0.25, "export": ["pdf", "png"], "raster_dpi": 450, "max_dpi": None,
               "notes": "Max height 170 mm leaves room for the legend. Vector (AI/EPS/PDF) with editable text; images >=300 dpi; RGB."},
    "cell": {"name": "Cell Press (Cell, Mol Cell, Cell Rep, Neuron, Immunity ...)", "widths_mm": {"single": 85, "onehalf": 114, "double": 174},
             "width_ranges_mm": [], "max_height_mm": 225, "fonts": ["Arial"],
             "font_min_pt": 6, "font_max_pt": 8, "base_pt": 7,
             "panel_label": {"case": "upper", "size": 8, "weight": "bold", "parens": False},
             "line_min_pt": 0.5, "export": ["pdf", "tiff"], "raster_dpi": 500, "max_dpi": None,
             "notes": "300 dpi colour/greyscale, 500 dpi combination, 1000 dpi line art; RGB; figure + legend on one page. Graphical abstract 1200x1200 px, Arial 8-12 pt."},
    "science": {"name": "Science / Science Advances / Sci Transl Med", "widths_mm": {"single": 90, "onehalf": 144, "double": 184},
                "width_ranges_mm": [[90, 144]], "max_height_mm": 199, "fonts": ["Myriad Pro", "Helvetica", "Arial"],
                "font_min_pt": 6, "font_max_pt": 8, "base_pt": 7,
                "panel_label": {"case": "upper", "size": 9, "weight": "bold", "parens": False},
                "line_min_pt": 0.3, "export": ["pdf", "tiff"], "raster_dpi": 300, "max_dpi": None,
                "notes": "1 col 9 cm, 2 col 18.4 cm, intermediate <=14.4 cm; max depth 19.9 cm. Text 6-8 pt (8 default) sans serif, Myriad preferred; panel labels 9 pt bold caps."},
    "pnas": {"name": "PNAS", "widths_mm": {"single": 87, "onehalf": 114, "double": 178},
             "width_ranges_mm": [], "max_height_mm": 225, "fonts": ["Arial", "Helvetica"],
             "font_min_pt": 6, "font_max_pt": 12, "base_pt": 7,
             "panel_label": {"case": "upper", "size": 9, "weight": "bold", "parens": False},
             "line_min_pt": 0.25, "export": ["pdf", "tiff"], "raster_dpi": 600, "max_dpi": None,
             "notes": "300 ppi halftone, 600-900 ppi with text, 1000-1200 ppi line art; 6-12 pt after reduction, consistent; RGB; TIFF/EPS/PDF."},
    "plos": {"name": "PLOS (ONE, Biology, Comp Biol, Genetics ...)", "widths_mm": {"single": 132, "double": 190.5},
             "width_ranges_mm": [[66.8, 190.5]], "max_height_mm": 222.3, "fonts": ["Arial", "Times New Roman", "Times"],
             "font_min_pt": 8, "font_max_pt": 12, "base_pt": 8,
             "panel_label": {"case": "upper", "size": 10, "weight": "bold", "parens": False},
             "line_min_pt": 0.5, "export": ["tiff", "pdf"], "raster_dpi": 600, "max_dpi": 600,
             "notes": "Upload TIFF (LZW) or EPS only; 300-600 dpi (higher gets resized); 789-2250 px wide at 300 dpi; <=10 MB; Arial/Times/Symbol 8-12 pt. PDF is for your own preview."},
    "elife": {"name": "eLife", "widths_mm": {"single": 100, "double": 200},
              "width_ranges_mm": [[100, 230]], "max_height_mm": 240, "fonts": ["Arial", "Helvetica"],
              "font_min_pt": 6, "font_max_pt": 10, "base_pt": 7,
              "panel_label": {"case": "upper", "size": 9, "weight": "bold", "parens": False},
              "line_min_pt": 0.5, "export": ["pdf", "tiff"], "raster_dpi": 300, "max_dpi": None,
              "notes": ">=300 dpi and >=10 cm wide (>=20 cm for full-page figures); TIFF 8-bit/JPG/EPS/AI/PDF; single page; 'Figure N-source data 1' per figure (<100 MB); 'Figure N-figure supplement M'. No font size rule (6-10 pt is house convention)."},
    "elsevier": {"name": "Elsevier (generic; check the journal's Guide for Authors)", "widths_mm": {"single": 90, "onehalf": 140, "double": 190},
                 "width_ranges_mm": [[30, 90]], "max_height_mm": 240, "fonts": ["Arial", "Helvetica", "Times New Roman", "Courier"],
                 "font_min_pt": 6, "font_max_pt": 10, "base_pt": 7,
                 "panel_label": {"case": "lower", "size": 8, "weight": "bold", "parens": True},
                 "line_min_pt": 0.5, "export": ["pdf", "tiff"], "raster_dpi": 500, "max_dpi": None,
                 "notes": "Lettering ~7 pt, sub/superscripts >=6 pt; 300 dpi halftone, 500 dpi combination, 1000 dpi line art; minimal width 30 mm."},
    "acs": {"name": "ACS journals (JACS, J Med Chem, ACS Chem Biol, JCIM ...)", "widths_mm": {"single": 82.5, "double": 177.8},
            "width_ranges_mm": [[40, 84.6], [105.9, 177.8]], "max_height_mm": 232.8, "fonts": ["Arial", "Helvetica"],
            "font_min_pt": 4.5, "font_max_pt": 10, "base_pt": 7,
            "panel_label": {"case": "lower", "size": 8, "weight": "bold", "parens": True},
            "line_min_pt": 0.5, "export": ["pdf", "tiff"], "raster_dpi": 600, "max_dpi": None,
            "notes": "Single column <=3.33 in (3.25 in preferred); double 4.17-7 in; max depth 9.167 in incl. caption. Lettering >=4.5 pt (JACS Au / ACS Materials Au: >=8 pt) — aim for >=6 pt. Lines >=0.5 pt. 1200 dpi line art / 600 greyscale / 300 colour. WCAG contrast 4.5:1 text, 3:1 graphics."},
    "ieee": {"name": "IEEE Transactions (template-derived; verify per journal)", "widths_mm": {"single": 88.9, "double": 181.9},
             "width_ranges_mm": [], "max_height_mm": 230, "fonts": ["Arial", "Helvetica", "Times New Roman"],
             "font_min_pt": 7, "font_max_pt": 10, "base_pt": 8,
             "panel_label": {"case": "lower", "size": 8, "weight": "normal", "parens": True},
             "line_min_pt": 0.5, "export": ["pdf", "png"], "raster_dpi": 600, "max_dpi": None,
             "notes": "Column ~3.5 in, text width ~7.16 in. Subfigure labels (a), (b) usually set in captions."},
    "neurips": {"name": "NeurIPS / ICLR / COLM / TMLR (single column, 5.5 in text width)", "widths_mm": {"single": 139.7, "half": 68.0},
                "width_ranges_mm": [[40, 139.7]], "max_height_mm": 200, "fonts": ["Arial", "Helvetica", "Times New Roman", "DejaVu Sans"],
                "font_min_pt": 6, "font_max_pt": 10, "base_pt": 8,
                "panel_label": {"case": "lower", "size": 9, "weight": "bold", "parens": True},
                "line_min_pt": 0.5, "export": ["pdf", "png"], "raster_dpi": 300, "max_dpi": None,
                "notes": "Text width 5.5 in (from the LaTeX style file). Build at the width you \\includegraphics at, so figure text ~ caption size (8-9 pt). Vector PDF, Type 42 fonts."},
    "icml": {"name": "ICML / CVPR / ICCV / AAAI (two column, ~3.25 in column)", "widths_mm": {"single": 82.6, "double": 171.5},
             "width_ranges_mm": [], "max_height_mm": 220, "fonts": ["Arial", "Helvetica", "Times New Roman", "DejaVu Sans"],
             "font_min_pt": 6, "font_max_pt": 10, "base_pt": 7,
             "panel_label": {"case": "lower", "size": 8, "weight": "bold", "parens": True},
             "line_min_pt": 0.5, "export": ["pdf", "png"], "raster_dpi": 300, "max_dpi": None,
             "notes": "ICML column 3.25 in, text width 6.75 in (CVPR 6.875 in). Include with width=\\columnwidth."},
    "acl": {"name": "ACL / EMNLP / NAACL (two column)", "widths_mm": {"single": 77.0, "double": 160.0},
            "width_ranges_mm": [], "max_height_mm": 220, "fonts": ["Arial", "Helvetica", "Times New Roman", "DejaVu Sans"],
            "font_min_pt": 6, "font_max_pt": 10, "base_pt": 7,
            "panel_label": {"case": "lower", "size": 8, "weight": "bold", "parens": True},
            "line_min_pt": 0.5, "export": ["pdf", "png"], "raster_dpi": 300, "max_dpi": None,
            "notes": "Column 7.7 cm, text width 16 cm."},
    "generic": {"name": "Generic life-science journal (safe default until the target is known)", "widths_mm": {"single": 89, "onehalf": 136, "double": 183},
                "width_ranges_mm": [[85, 90], [114, 144], [174, 190]], "max_height_mm": 170, "fonts": ["Arial", "Helvetica"],
                "font_min_pt": 6, "font_max_pt": 8, "base_pt": 7,
                "panel_label": {"case": "lower", "size": 8, "weight": "bold", "parens": False},
                "line_min_pt": 0.5, "export": ["pdf", "png"], "raster_dpi": 600, "max_dpi": None,
                "notes": "Satisfies the intersection of Nature/Cell/Science/PNAS closely; re-target once the journal is chosen."},
}

JOURNAL_ALIASES = {
    "nature": ["nature", "natcommun", "naturecommunications", "naturemethods", "naturebiotechnology", "naturegenetics",
               "naturecellbiology", "naturechemicalbiology", "natureportfolio", "communicationsbiology", "npj",
               "naturemachineintelligence", "naturecomputationalscience", "scientificreports"],
    "cell": ["cell", "cellpress", "molecularcell", "cellreports", "neuron", "immunity", "iscience", "cellsystems",
             "cellgenomics", "cellchemicalbiology", "cellmetabolism", "developmentalcell", "currentbiology", "structure",
             "cancercell", "cellstemcell", "patterns", "cellreportsmethods"],
    "science": ["science", "scienceadvances", "sciadv", "sciencetranslationalmedicine", "sciencesignaling", "scienceimmunology", "aaas"],
    "pnas": ["pnas", "proceedingsofthenationalacademyofsciences"],
    "plos": ["plos", "plosone", "plosbiology", "ploscomputationalbiology", "ploscompbiol", "plosgenetics", "plospathogens", "plosmedicine"],
    "elife": ["elife"],
    "elsevier": ["elsevier", "bba", "biomaterials", "talanta", "jmolbiol", "journalofmolecularbiology", "computersinbiologyandmedicine"],
    "acs": ["acs", "jacs", "jmedchem", "journalofmedicinalchemistry", "acschemicalbiology", "jcim", "jproteomeres",
            "analchem", "biochemistry", "acscentralscience", "acsomega"],
    "ieee": ["ieee", "tmi", "tpami", "tcbb", "jbhi"],
    "neurips": ["neurips", "nips", "iclr", "colm", "tmlr"],
    "icml": ["icml", "cvpr", "iccv", "eccv", "aaai", "ijcai"],
    "acl": ["acl", "emnlp", "naacl", "eacl", "coling"],
    "generic": ["generic", "default", "biorxiv", "medrxiv", "arxiv", "preprint", "thesis"],
}


def mm_to_in(mm):
    return float(mm) / MM_PER_INCH


def journal_spec(journal="generic", quiet=False):
    """Spec dict for a journal name/alias (case/space/punctuation-insensitive). Unknown -> 'generic' + message."""
    key = "".join(ch for ch in str(journal).lower() if ch.isalnum())
    if key in JOURNAL_SPECS:
        return dict(JOURNAL_SPECS[key], key=key)
    for k, names in JOURNAL_ALIASES.items():
        if key in names:
            return dict(JOURNAL_SPECS[k], key=k)
    for k, names in JOURNAL_ALIASES.items():
        if any(key.startswith(n) for n in names if len(n) >= 4):
            return dict(JOURNAL_SPECS[k], key=k)
    if not quiet:
        print(f"[data-visualization] '{journal}' not in JOURNAL_SPECS -> using 'generic'. "
              "Look up the journal's artwork guide and call register_journal().")
    return dict(JOURNAL_SPECS["generic"], key="generic")


def register_journal(key, base="generic", **overrides):
    """Add/override a journal at runtime, e.g. register_journal('bioinformatics', widths_mm={'single': 86, 'double': 178})."""
    spec = dict(JOURNAL_SPECS[base])
    spec.update(overrides)
    spec.setdefault("name", key)
    JOURNAL_SPECS[key] = spec
    return spec


def list_journals():
    for k, s in JOURNAL_SPECS.items():
        w = ", ".join(f"{n} {v} mm" for n, v in s["widths_mm"].items())
        print(f"{k:9s} | {w} | text {s['font_min_pt']}-{s['font_max_pt']} pt | max h {s['max_height_mm']} mm | {s['name']}")


def figure_width_mm(journal="generic", width="single"):
    spec = journal_spec(journal, quiet=True)
    if isinstance(width, (int, float)):
        return float(width)
    if width not in spec["widths_mm"]:
        raise ValueError(f"width must be one of {list(spec['widths_mm'])} or a number in mm")
    return float(spec["widths_mm"][width])


def apply_journal_style(journal="generic", base_pt=None, font=None):
    """Set matplotlib rcParams for print-size figures in the journal's style. Returns the spec."""
    spec = journal_spec(journal)
    base = float(base_pt if base_pt is not None else spec["base_pt"])
    small = max(spec["font_min_pt"], base - 1)
    lw = max(spec["line_min_pt"], 0.6)
    fonts = ([font] if font else []) + spec["fonts"] + ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"]
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": fonts, "font.size": base,
        "axes.titlesize": base, "axes.labelsize": base, "axes.titleweight": "normal",
        "xtick.labelsize": small, "ytick.labelsize": small, "legend.fontsize": small,
        "legend.title_fontsize": small, "figure.titlesize": base,
        "axes.linewidth": lw, "xtick.major.width": lw, "ytick.major.width": lw,
        "xtick.minor.width": lw * 0.8, "ytick.minor.width": lw * 0.8,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.minor.size": 1.5, "ytick.minor.size": 1.5,
        "xtick.major.pad": 2, "ytick.major.pad": 2, "axes.labelpad": 2.5, "axes.titlepad": 3,
        "xtick.direction": "out", "ytick.direction": "out",
        "axes.spines.top": False, "axes.spines.right": False,
        "lines.linewidth": 1.0, "lines.markersize": 3, "patch.linewidth": lw,
        "errorbar.capsize": 1.5, "legend.frameon": False, "legend.handlelength": 1.2,
        "legend.handletextpad": 0.4, "legend.borderaxespad": 0.3, "legend.columnspacing": 0.8,
        "axes.prop_cycle": mpl.cycler(color=OKABE_ITO), "image.cmap": "viridis",
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "savefig.dpi": spec["raster_dpi"], "figure.dpi": 150, "savefig.transparent": False,
        "mathtext.default": "regular", "mathtext.fontset": "custom", "mathtext.rm": fonts[0],
        "mathtext.it": fonts[0] + ":italic", "mathtext.bf": fonts[0] + ":bold", "mathtext.sf": fonts[0],
        "axes.unicode_minus": True,
        "figure.constrained_layout.w_pad": 0.02, "figure.constrained_layout.h_pad": 0.02,
        "figure.constrained_layout.wspace": 0.03, "figure.constrained_layout.hspace": 0.03,
    })
    return spec


def new_figure(journal="generic", width="single", height_mm=None, aspect=0.75, nrows=1, ncols=1,
               mosaic=None, base_pt=None, **kwargs):
    """Figure at FINAL print size (mm) with journal style + constrained layout.
    width: named column ('single'|'onehalf'|'double') or a number in mm. Returns (fig, axes) / (fig, axd) for mosaic."""
    spec = apply_journal_style(journal, base_pt=base_pt)
    w = figure_width_mm(journal, width)
    h = float(height_mm) if height_mm is not None else w * aspect
    if h > spec["max_height_mm"]:
        print(f"[data-visualization] height {h:.0f} mm > {spec['max_height_mm']} mm max for {spec['name']}; split or shrink.")
    figsize = (mm_to_in(w), mm_to_in(h))
    if mosaic is not None:
        return plt.subplot_mosaic(mosaic, figsize=figsize, layout="constrained", **kwargs)
    return plt.subplots(nrows, ncols, figsize=figsize, layout="constrained", **kwargs)


def categorical_palette(n, kind="auto"):
    """Colour-blind-aware categorical colours. n<=8 Okabe-Ito, n==9 Tol muted. Beyond ~8 no palette is
    CVD-safe by colour alone: the function still returns n colours but you must add direct labels."""
    if kind == "okabe" or (kind == "auto" and n <= 8):
        return OKABE_ITO[:n]
    if kind == "tol" or (kind == "auto" and n <= 9):
        return TOL_MUTED[:n]
    base = TOL_MUTED + TOL_LIGHT + OKABE_ITO[:7]
    print(f"[data-visualization] {n} categories: colour alone cannot separate these for CVD readers — "
          "label groups directly on the plot (label_clusters) or merge into fewer lineages.")
    if n > len(base):
        cm = mpl.colormaps["turbo"]
        return [mpl.colors.to_hex(cm(i / max(n - 1, 1))) for i in range(n)]
    return base[:n]


def ax_auto(axes, tbs, tb):
    ax = axes[[id(t) for t in tbs].index(id(tb))]
    return ax.get_aspect() == "auto"


def add_panel_labels(fig, axes, journal="generic", labels=None, start=0, dx_mm=0.0, dy_mm=0.5, align_rows=True):
    """Panel letters in the journal's style (a / A / (a)), just outside each axes' tight bbox (top-left).
    align_rows=True puts letters of panels starting in the same grid row on one baseline."""
    spec = journal_spec(journal, quiet=True)
    pl = spec["panel_label"]
    axes = list(axes.values()) if isinstance(axes, dict) else list(np.ravel(axes))
    if labels is None:
        labels = [chr(ord("a") + start + i) for i in range(len(axes))]
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    tbs = [ax.get_tightbbox(r) for ax in axes]
    rows = []
    for ax in axes:
        try:
            rows.append(ax.get_subplotspec().rowspan.start)
        except Exception:
            rows.append(None)
    tops = {}
    if align_rows:
        for tb, row in zip(tbs, rows):
            if row is not None and ax_auto(axes, tbs, tb):
                tops[row] = max(tops.get(row, -1e9), tb.y1)
    out = []
    for ax, tb, row, lab in zip(axes, tbs, rows, labels):
        if ax.get_aspect() != "auto":      # images / equal-aspect panels: letter at their own top-left
            row = None
        lab = lab.upper() if pl["case"] == "upper" else lab.lower()
        if pl.get("parens"):
            lab = f"({lab})"
        top = tops.get(row, tb.y1)
        off_x = (ax.bbox.x0 - tb.x0) / fig.dpi + mm_to_in(dx_mm)
        off_y = (top - ax.bbox.y1) / fig.dpi + mm_to_in(dy_mm)
        tr = ax.transAxes + mpl.transforms.ScaledTranslation(-off_x, off_y, fig.dpi_scale_trans)
        out.append(ax.text(0, 1, lab, transform=tr, fontsize=pl["size"], fontweight=pl["weight"],
                           ha="left", va="bottom"))
    fig._pf_panel_letters = list(getattr(fig, "_pf_panel_letters", [])) + [t.get_text() for t in out]
    return out


def add_scale_bar(ax, length, pixel_size, unit="µm", loc="lower right", color="white", thickness_px=None,
                  label=True, fontsize=None, pad=0.4):
    """Scale bar on an image axes whose data units are pixels. length in `unit`; pixel_size in unit/pixel."""
    from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
    import matplotlib.font_manager as fm
    size_px = length / pixel_size
    h = abs(ax.get_ylim()[1] - ax.get_ylim()[0])
    thick = thickness_px if thickness_px is not None else max(h * 0.012, 1.0)
    fp = fm.FontProperties(size=fontsize or mpl.rcParams["xtick.labelsize"])
    sb = AnchoredSizeBar(ax.transData, size_px, f"{length:g} {unit}" if label else "", loc, pad=pad,
                         color=color, frameon=False, size_vertical=thick, fontproperties=fp,
                         label_top=True, sep=1.5)
    ax.add_artist(sb)
    return sb


def plot_points_summary(ax, groups, order=None, colors=None, center="mean", error="sd", jitter=0.12,
                        point_size=10, bar=False, seed=0, alpha=0.85, capsize=2.0, labels=True):
    """Every data point + summary (mean±SD / SEM / 95% CI, or median+IQR). groups: dict name -> values.
    Returns {name: {n, center, lo, hi}} for the legend ('mean ± s.d., n = ...')."""
    rng = np.random.default_rng(seed)
    order = list(order or groups.keys())
    colors = colors or categorical_palette(len(order))
    stats = {}
    for i, g in enumerate(order):
        v = np.asarray(groups[g], float)
        v = v[np.isfinite(v)]
        n = v.size
        if center == "median":
            c = float(np.median(v))
            lo, hi = np.percentile(v, [25, 75])
        else:
            c = float(v.mean())
            sd = v.std(ddof=1) if n > 1 else 0.0
            if error == "sem":
                e = sd / math.sqrt(n) if n > 0 else 0.0
            elif error == "ci95":
                from scipy import stats as st
                e = st.t.ppf(0.975, n - 1) * sd / math.sqrt(n) if n > 1 else 0.0
            else:
                e = sd
            lo, hi = c - e, c + e
        col = colors[g] if isinstance(colors, dict) else colors[i % len(colors)]
        if bar:
            ax.bar(i, c, width=0.6, color=col, alpha=0.35, edgecolor=col, linewidth=0.8, zorder=1)
        ax.scatter(i + rng.uniform(-jitter, jitter, n), v, s=point_size, color=col, alpha=alpha,
                   edgecolor="white", linewidth=0.3, zorder=3)
        ax.errorbar(i + 0.28, c, yerr=[[c - lo], [hi - c]], fmt="o" if not bar else "none", color="black",
                    ms=3, lw=0.8, capsize=capsize, zorder=4)
        stats[g] = {"n": int(n), "center": c, "lo": float(lo), "hi": float(hi)}
    ax.set_xticks(range(len(order)))
    if labels:
        ax.set_xticklabels(order)
    ax.set_xlim(-0.6, len(order) - 0.4)
    return stats


def superplot(ax, df, x, y, replicate, order=None, colors=None, jitter=0.15, cell_size=3, rep_size=22, seed=0):
    """SuperPlot (Lord et al., JCB 2020): per-cell values faint, per-replicate means as large markers
    coloured by replicate; mean ± SD of replicate means. Statistics belong on replicate means (n = replicates)."""
    rng = np.random.default_rng(seed)
    order = list(order or list(dict.fromkeys(df[x])))
    reps = list(dict.fromkeys(df[replicate]))
    colors = colors or categorical_palette(len(reps))
    summary = {}
    for i, g in enumerate(order):
        sub = df[df[x] == g]
        means = []
        for j, r in enumerate(reps):
            v = sub.loc[sub[replicate] == r, y].to_numpy(float)
            if v.size == 0:
                continue
            rc = colors[r] if isinstance(colors, dict) else colors[j % len(colors)]
            ax.scatter(i + rng.uniform(-jitter, jitter, v.size), v, s=cell_size, color=rc,
                       alpha=0.25, linewidth=0, zorder=2, rasterized=v.size > 500)
            m = float(np.mean(v))
            means.append(m)
            ax.scatter(i + rng.uniform(-jitter / 2, jitter / 2), m, s=rep_size, color=rc,
                       edgecolor="black", linewidth=0.5, zorder=4)
        mu = float(np.mean(means))
        sd = float(np.std(means, ddof=1)) if len(means) > 1 else 0.0
        ax.errorbar(i, mu, yerr=sd, fmt="_", color="black", ms=10, mew=1.0, lw=0.8, capsize=3, zorder=5)
        summary[g] = {"n_replicates": len(means), "n_cells": int(len(sub)), "mean_of_means": mu, "sd": sd, "rep_means": means}
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(order)
    return summary


def format_p(p, style="nature"):
    """Exact P text: 'P = 0.003', 'P = 2.1 × 10$^{-5}$' (mathtext; style='nature'), or APA 'p < .001'."""
    if style == "apa":
        return "p < .001" if p < 0.001 else f"p = {p:.3f}".replace("0.", ".", 1)
    if p >= 0.001:
        return f"P = {p:.3f}" if p < 0.01 else f"P = {p:.2f}"
    m, e = f"{p:.1e}".split("e")
    return f"P = {m} × 10$^{{{int(e)}}}$"   # mathtext superscript; fonts set by apply_journal_style


def add_significance(ax, x1, x2, y, text, h=None, lw=0.6, fontsize=None):
    """Bracket from x1 to x2 at height y (data units) with text — prefer exact P over stars."""
    yl = ax.get_ylim()
    h = h if h is not None else 0.02 * (yl[1] - yl[0])
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], color="black", lw=lw, clip_on=False)
    ax.text((x1 + x2) / 2, y + h, text, ha="center", va="bottom", fontsize=fontsize or mpl.rcParams["font.size"])


def label_clusters(ax, xy, labels, fontsize=None, min_size=1, color="black", halo=True, repel=True,
                   max_iter=300, leader=True, colors=None, max_shift_mm=4.0, counts=True, stack_min=3, gap_mm=1.0):
    """Write each category name at its median position (direct labelling for UMAP / t-SNE / PCA).
    repel=True pushes overlapping labels apart and draws a leader line when a label moved > 1.5 mm.
    colors={label: colour}: labels that would have to move more than max_shift_mm (touching clusters) are
    removed from the plot and listed in a legend beside the axes instead (with cell counts if counts=True). The same
    happens to every chain of >= stack_min labels sitting within gap_mm of each other (a crowded stack).
    Pass colors whenever clusters touch — it is the reliable fix for crowded label stacks."""
    import matplotlib.patheffects as pe
    xy = np.asarray(xy)
    labels = np.asarray(labels)
    out, anchors = [], []
    for lab in np.unique(labels):
        m = labels == lab
        if m.sum() < min_size:
            continue
        cx, cy = np.median(xy[m, 0]), np.median(xy[m, 1])
        t = ax.text(cx, cy, str(lab), ha="center", va="center", color=color, zorder=10,
                    fontsize=fontsize or mpl.rcParams["xtick.labelsize"])
        if halo:
            t.set_path_effects([pe.withStroke(linewidth=1.5, foreground="white")])
        out.append(t)
        anchors.append((cx, cy))
    if not (repel and len(out) > 1):
        return out
    fig = ax.figure
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    pos = np.array([ax.transData.transform(a) for a in anchors], float)   # display px
    orig = pos.copy()
    wh = np.array([[t.get_window_extent(r).width, t.get_window_extent(r).height] for t in out]) + 2.0
    axbb = ax.get_window_extent(r)
    for _ in range(max_iter):
        moved = False
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                dx, dy = pos[j] - pos[i]
                ox = (wh[i, 0] + wh[j, 0]) / 2 - abs(dx)
                oy = (wh[i, 1] + wh[j, 1]) / 2 - abs(dy)
                if ox > 0 and oy > 0:          # overlap: separate along the cheaper axis
                    if oy <= ox:
                        step = (oy / 2 + 0.5) * (1 if dy >= 0 else -1)
                        pos[i, 1] -= step; pos[j, 1] += step
                    else:
                        step = (ox / 2 + 0.5) * (1 if dx >= 0 else -1)
                        pos[i, 0] -= step; pos[j, 0] += step
                    moved = True
        pos[:, 0] = np.clip(pos[:, 0], axbb.x0 + wh[:, 0] / 2, axbb.x1 - wh[:, 0] / 2)
        pos[:, 1] = np.clip(pos[:, 1], axbb.y0 + wh[:, 1] / 2, axbb.y1 - wh[:, 1] / 2)
        if not moved:
            break
    inv = ax.transData.inverted()
    thr = mm_to_in(1.5) * fig.dpi
    far = mm_to_in(max_shift_mm) * fig.dpi
    keyed = []
    crowded = set()
    if colors is not None and len(out) >= stack_min:
        g = mm_to_in(gap_mm) * fig.dpi
        adj = [[j for j in range(len(out)) if j != i and abs(pos[i, 0] - pos[j, 0]) < (wh[i, 0] + wh[j, 0]) / 2 + g
                and abs(pos[i, 1] - pos[j, 1]) < (wh[i, 1] + wh[j, 1]) / 2 + g] for i in range(len(out))]
        seen = set()
        for i in range(len(out)):
            if i in seen:
                continue
            comp, stack = set(), [i]
            while stack:
                k = stack.pop()
                if k in comp:
                    continue
                comp.add(k)
                stack += adj[k]
            seen |= comp
            if len(comp) >= stack_min:
                crowded |= comp
    for idx, (t, p, o) in enumerate(zip(out, pos, orig)):
        shift = np.hypot(*(p - o))
        if colors is not None and (shift > far or idx in crowded):
            keyed.append(t)
            continue
        t.set_position(inv.transform(p))
        if leader and shift > thr:
            a0, a1 = inv.transform(o), inv.transform(p)
            ax.plot([a0[0], a1[0]], [a0[1], a1[1]], color=color, lw=0.5, zorder=9)
    if keyed:
        from matplotlib.lines import Line2D
        handles = []
        for t in keyed:
            lab = t.get_text()
            n = int((labels == lab).sum()) if counts else None
            handles.append(Line2D([], [], ls="", marker="o", ms=3, color=colors.get(lab, "grey"),
                                  label=f"{lab} ({n:,})" if counts else lab))
            t.remove()
        ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.0, 1.0), frameon=False,
                  handletextpad=0.2, borderaxespad=0.2, title=None)
        out = [t for t in out if t not in keyed]
        fig.canvas.draw()          # let constrained layout make room for the new legend before any audit
    return out


def embedding_axes(ax, xlabel="UMAP 1", ylabel="UMAP 2", arrow_frac=0.18):
    """Replace meaningless embedding ticks/frame with short labelled corner arrows."""
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    kw = dict(xycoords="axes fraction", textcoords="axes fraction",
              arrowprops=dict(arrowstyle="-|>", lw=0.6, color="black", mutation_scale=5))
    ax.annotate("", xy=(arrow_frac, 0), xytext=(0, 0), **kw)
    ax.annotate("", xy=(0, arrow_frac), xytext=(0, 0), **kw)
    fs = mpl.rcParams["xtick.labelsize"]
    ax.text(0.0, -0.015, xlabel, transform=ax.transAxes, ha="left", va="top", fontsize=fs)
    ax.text(-0.015, 0.0, ylabel, transform=ax.transAxes, ha="right", va="bottom", rotation=90, fontsize=fs)


def channel_composite(channels, colors=None, clip_pct=(0.5, 99.5)):
    """Merge 2-4 greyscale channels into an RGB image with CVD-safe pseudo-colours (default magenta/green/cyan/grey).
    The same percentile window is computed per channel from that channel's whole image (no regional tweaks)."""
    if colors is None:
        colors = ["#FF00FF", "#00FF00", "#00FFFF", "#FFFFFF"]
    out = None
    for ch, col in zip(channels, colors):
        a = np.asarray(ch, float)
        lo, hi = np.percentile(a, clip_pct)
        a = np.clip((a - lo) / (hi - lo + 1e-12), 0, 1)
        rgb = np.array(mpl.colors.to_rgb(col))
        layer = a[..., None] * rgb
        out = layer if out is None else out + layer
    return np.clip(out, 0, 1)


def save_figure(fig, stem, journal="generic", formats=None, dpi=None):
    """Export at exact design size (never bbox_inches='tight' — it silently changes the width).
    Vector pdf/eps/svg keep TrueType (Type 42) text; tiff = LZW, RGB, dpi tag; png with dpi tag. Returns paths."""
    import os
    from PIL import Image
    spec = journal_spec(journal, quiet=True)
    formats = formats or spec["export"]
    rdpi = dpi or spec["raster_dpi"]
    if spec.get("max_dpi"):
        rdpi = min(rdpi, spec["max_dpi"])
    paths = []
    for fmt in formats:
        fmt = fmt.lower().lstrip(".")
        path = f"{stem}.{fmt}"
        if fmt in ("pdf", "eps", "svg"):
            fig.savefig(path, format=fmt)
        elif fmt in ("tif", "tiff"):
            tmp = f"{stem}__tmp.png"
            fig.savefig(tmp, dpi=rdpi, format="png")
            with Image.open(tmp) as im:
                im.convert("RGB").save(path, compression="tiff_lzw", dpi=(rdpi, rdpi))
            os.remove(tmp)
        else:
            fig.savefig(path, dpi=rdpi, format=fmt)
            if fmt == "png":
                with Image.open(path) as im:
                    rgb = im.convert("RGB")
                rgb.save(path, dpi=(rdpi, rdpi))
        paths.append(path)
    return paths


def width_ok(w_mm, spec, tol=1.5):
    if any(abs(v - w_mm) <= tol for v in spec["widths_mm"].values()):
        return True
    return any(lo - 0.5 <= w_mm <= hi + 0.5 for lo, hi in spec.get("width_ranges_mm") or [])


class FigureAuditError(AssertionError):
    """Raised by audit_figure / audit_file / check_legend with strict=True. The message lists every issue."""


def _raise_if(issues, strict, what):
    if strict and issues:
        raise FigureAuditError(f"{what} found {len(issues)} issue(s) — fix them and re-run:\n  - " + "\n  - ".join(issues))


def _text_rect(t, r):
    """Oriented rectangle (centre, half-axes vectors) of a text in display px. The axis-aligned extent of a rotated
    rectangle shares its centre, so centre = AABB centre; size comes from the unrotated extent."""
    bb = t.get_window_extent(r)
    rot = t.get_rotation()
    if rot % 360:
        t.set_rotation(0)
        ub = t.get_window_extent(r)
        t.set_rotation(rot)
        w, h = ub.width, ub.height
    else:
        w, h = bb.width, bb.height
    th = math.radians(rot)
    u = np.array([math.cos(th), math.sin(th)]) * w / 2
    v = np.array([-math.sin(th), math.cos(th)]) * h / 2
    return np.array([(bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2]), u, v


def _rect_overlap(A, B, shrink=0.85):
    """Separating-axis test for two oriented rectangles (centre, u, v); halves shrunk so glyph padding doesn't count."""
    (ca, ua, va), (cb, ub, vb) = A, B
    ua, va, ub, vb = ua * shrink, va * shrink, ub * shrink, vb * shrink
    d = cb - ca
    for ax_ in (ua, va, ub, vb):
        n = np.linalg.norm(ax_)
        if n == 0:
            continue
        k = ax_ / n
        ra = abs(ua @ k) + abs(va @ k)
        rb = abs(ub @ k) + abs(vb @ k)
        if abs(d @ k) > ra + rb:
            return False
    return True


def _rotated_tick_overlaps(ax, r):
    """Overlap test for oblique tick labels: consecutive labels at angle t collide when spacing*sin(t) < text height."""
    out = []
    for axis, name in ((ax.xaxis, "x"), (ax.yaxis, "y")):
        labs = [tk.label1 for tk in axis.get_major_ticks() if tk.label1.get_visible() and tk.label1.get_text().strip()]
        lo, hi = sorted(axis.get_view_interval())
        labs = [l for l, tk in zip(labs, axis.get_major_ticks()) if lo - 1e-9 <= tk.get_loc() <= hi + 1e-9] if labs else labs
        if len(labs) < 2:
            continue
        ang = abs(labs[0].get_rotation()) % 180
        ang = min(ang, 180 - ang)
        if ang in (0, 90):
            continue
        pos = sorted((ax.transData.transform((l.get_position()[0], 0))[0] if name == "x"
                      else ax.transData.transform((0, l.get_position()[1]))[1]) for l in labs)
        gap = np.min(np.diff(pos)) if len(pos) > 1 else 1e9
        hpx = labs[0].get_fontsize() / 72 * ax.figure.dpi
        if gap * math.sin(math.radians(ang)) < 0.95 * hpx:
            out.append(f"OVERLAP rotated {name}-tick labels collide (spacing {gap / ax.figure.dpi * 25.4:.1f} mm at {ang:.0f} deg) "
                       f"— shorten/abbreviate labels, rotate to 90 deg, widen the panel or transpose the heatmap")
    return out


def _empty_bands(fig, r, frac=0.18):
    """Largest fully blank horizontal / vertical band of the canvas (no axes, legend or text). Returns issue strings."""
    n = 120
    occ = np.zeros((n, n), bool)
    W, H = fig.bbox.width, fig.bbox.height
    arts = [ax.get_tightbbox(r) for ax in fig.axes if ax.get_visible()]
    arts += [t.get_window_extent(r) for t in fig.texts if t.get_visible() and t.get_text().strip()]
    arts += [lg.get_window_extent(r) for lg in fig.legends]
    for bb in arts:
        if bb is None:
            continue
        x0, x1 = int(np.clip(bb.x0 / W * n, 0, n)), int(np.clip(math.ceil(bb.x1 / W * n), 0, n))
        y0, y1 = int(np.clip(bb.y0 / H * n, 0, n)), int(np.clip(math.ceil(bb.y1 / H * n), 0, n))
        occ[y0:y1, x0:x1] = True
    out = []
    W_mm, H_mm = W / fig.dpi * MM_PER_INCH, H / fig.dpi * MM_PER_INCH
    for arr, name, dim_mm in ((occ.any(axis=1), "horizontal", H_mm), (occ.any(axis=0), "vertical", W_mm)):
        run = best = end = 0
        for k, v in enumerate(arr):
            run = 0 if v else run + 1
            if run > best:
                best, end = run, k
        if best / n > frac:
            band = best / n * dim_mm
            a0, a1 = (end - best + 1) / n * dim_mm, (end + 1) / n * dim_mm
            if name == "horizontal":
                where = f"from {dim_mm - a1:.0f} to {dim_mm - a0:.0f} mm below the top edge"
                fix = (f"set height_mm={max(dim_mm - band + 4, 20):.0f} in new_figure (was {dim_mm:.0f}); if the gap sits beside a "
                       f"short panel instead, give that row a smaller height_ratios entry or let a panel span it")
            else:
                where = f"from {a0:.0f} to {a1:.0f} mm from the left edge"
                fix = "use width_ratios / mosaic spans so panels fill the width, or move the legend/colour bar into the gap"
            out.append(f"WHITESPACE blank {name} band {band:.0f} mm ({100 * best / n:.0f}% of the figure) {where} — {fix}")
    return out


def audit_figure(fig, journal="generic", verbose=True, strict=False):
    """Pre-export QA at final size: width/height vs journal, each text's size vs min/max, font family,
    text-text overlaps (incl. rotated tick labels), text outside canvas, blank bands, too-thin lines, rainbow colormaps.
    Returns issue list ([] = pass). strict=True raises FigureAuditError instead — use it in scripts you cannot look at."""
    spec = journal_spec(journal, quiet=True)
    issues = []
    w_mm, h_mm = (np.asarray(fig.get_size_inches()) * MM_PER_INCH).tolist()
    if not width_ok(w_mm, spec):
        issues.append(f"WIDTH {w_mm:.1f} mm is not an allowed width {spec['widths_mm']} / ranges {spec.get('width_ranges_mm')}")
    if h_mm > spec["max_height_mm"] + 0.5:
        issues.append(f"HEIGHT {h_mm:.1f} mm > max {spec['max_height_mm']} mm")
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    fbb = fig.bbox
    hidden = set()
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            lo, hi = sorted(axis.get_view_interval())
            eps = (hi - lo) * 1e-6
            for tk in axis.get_major_ticks() + axis.get_minor_ticks():
                if not (lo - eps <= tk.get_loc() <= hi + eps):
                    hidden.update({id(tk.label1), id(tk.label2)})
    texts, _seen = [], set()
    for t in fig.findobj(mpl.text.Text):        # findobj can reach one artist twice (legend in axes + figure)
        if id(t) in _seen or id(t) in hidden or not t.get_visible() or not t.get_text().strip():
            continue
        _seen.add(id(t))
        texts.append(t)
    lab_size = spec["panel_label"]["size"]
    allowed = set(spec["fonts"]) | {"Arial", "Helvetica", "Liberation Sans", "DejaVu Sans", "Myriad Pro"}
    boxes = []
    for t in texts:
        s = t.get_fontsize()
        txt = t.get_text().strip().replace("\n", " ")[:30]
        if s < spec["font_min_pt"] - 0.05:
            issues.append(f"FONT {s:.1f} pt < min {spec['font_min_pt']} pt: '{txt}'")
        if s > max(spec["font_max_pt"], lab_size) + 0.05:
            issues.append(f"FONT {s:.1f} pt > max {max(spec['font_max_pt'], lab_size)} pt: '{txt}'")
        try:
            fn = t.get_fontname()
            if fn not in allowed:
                issues.append(f"FONTFAMILY '{fn}' not in {spec['fonts']}: '{txt}'")
        except Exception:
            pass
        try:
            bb = t.get_window_extent(r)
        except Exception:
            continue
        if bb.width <= 0 or bb.height <= 0:
            continue
        if bb.x0 < fbb.x0 - 1 or bb.x1 > fbb.x1 + 1 or bb.y0 < fbb.y0 - 1 or bb.y1 > fbb.y1 + 1:
            issues.append(f"CLIPPED text outside canvas: '{txt}'")
        boxes.append((bb, txt, t.get_rotation() % 90 == 0, t))
    nover = 0
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][0], boxes[j][0]
            if boxes[i][1] == boxes[j][1] and abs(a.x0 - b.x0) < 1 and abs(a.y0 - b.y0) < 1:
                continue                                  # same label drawn twice in the same place (twin/colorbar axes)
            if not (boxes[i][2] and boxes[j][2]):     # oblique text: exact oriented-rectangle test
                if a.overlaps(b) and _rect_overlap(_text_rect(boxes[i][3], r), _text_rect(boxes[j][3], r)):
                    nover += 1
                    if nover <= 8:
                        issues.append(f"OVERLAP text '{boxes[i][1]}' x '{boxes[j][1]}'")
                continue
            ix = min(a.x1, b.x1) - max(a.x0, b.x0)
            iy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ix > 1.0 and iy > 1.0 and ix * iy > 0.15 * min(a.width * a.height, b.width * b.height):
                nover += 1
                if nover <= 8:
                    issues.append(f"OVERLAP text '{boxes[i][1]}' x '{boxes[j][1]}'")
    if nover > 8:
        issues.append(f"OVERLAP ... {nover - 8} more overlapping text pairs")
    if any(x.startswith("CLIPPED") for x in issues):
        issues.append("HINT for CLIPPED text: it usually belongs to a colour bar, legend or axes placed by hand (fig.add_axes, inset_axes, "
                      "cax=, bbox_to_anchor outside the figure), which constrained layout cannot move. Use add_colorbar(fig, mappable, ax, "
                      "label) and add_size_legend(ax, values, sizes, title) instead; they reserve space inside the figure")
    if nover:
        issues.append("HINT for overlapping tick labels call fit_tick_labels(ax, 'x') (or 'y') after setting them — it wraps at word "
                      "boundaries, then rotates, then abbreviates until they fit; for other text move or shorten it")
    issues += _empty_bands(fig, r)
    lmin = spec["line_min_pt"]
    thin = sum(1 for ln in fig.findobj(mpl.lines.Line2D)
               if ln.get_visible() and ln.get_linestyle() not in ("None", "", " ") and 0 < ln.get_linewidth() < lmin - 1e-6)
    if thin:
        issues.append(f"LINES {thin} line(s) thinner than {lmin} pt")
    for obj in fig.findobj(lambda a: hasattr(a, "get_cmap") and hasattr(a, "get_array")):
        try:
            if obj.get_array() is not None and obj.get_cmap().name in BAD_CMAPS:
                issues.append(f"COLORMAP '{obj.get_cmap().name}' is not perceptually uniform — use viridis/cividis/magma or a diverging map (RdBu_r, vlag)")
        except Exception:
            continue
    if verbose:
        print(f"[audit] {spec['name']} | {w_mm:.1f} x {h_mm:.1f} mm | {len(texts)} text items | "
              + ("PASS" if not issues else f"{len(issues)} issue(s)"))
        for s in issues:
            print("  -", s)
    _raise_if(issues, strict, "audit_figure")
    return issues


def audit_file(path, journal="generic", verbose=True, strict=False):
    """Check an exported file. PDF: page size, live-text sizes (pdfplumber), Type 3 fonts (pypdf).
    TIFF/PNG: pixels, dpi tag, implied print size, colour mode. Returns issue list."""
    spec = journal_spec(journal, quiet=True)
    issues, info = [], {}
    p = str(path).lower()
    if p.endswith(".pdf"):
        import pdfplumber
        from pypdf import PdfReader
        with pdfplumber.open(path) as pdf:
            pg = pdf.pages[0]
            info["width_mm"], info["height_mm"] = round(pg.width / 72 * MM_PER_INCH, 1), round(pg.height / 72 * MM_PER_INCH, 1)
            # rotated glyphs: pdfplumber 'size' is the advance width; the font height is the box x-extent
            sizes = [round(c["size"] if c.get("upright", True) else (c["x1"] - c["x0"]), 2)
                     for c in pg.chars if c["text"].strip()]
            unknown_visible = sum(1 for c in pg.chars if c["fontname"] == "unknown" and c["text"].strip())
        # sub/superscripts (mathtext shrinks them to 70 %) are judged against 0.7 x the minimum
        uniq = sorted(set(sizes))
        script = {v for v in uniq if any(abs(v / 0.7 - u) < 0.15 for u in uniq)}
        body = [v for v in sizes if v not in script]
        info.update(min_font=min(body) if body else None, max_font=max(sizes) if sizes else None,
                    min_script=min(script) if script else None, n_chars=len(sizes))
        if body and min(body) < spec["font_min_pt"] - 0.05:
            issues.append(f"FONT min {min(body)} pt < {spec['font_min_pt']} pt")
        top = max(spec["font_max_pt"], spec["panel_label"]["size"])
        if sizes and max(sizes) > top + 0.05:
            issues.append(f"FONT max {max(sizes)} pt > {top} pt (journal text max / panel-letter size)")
        if script and min(script) < 0.7 * spec["font_min_pt"] - 0.05:
            issues.append(f"SCRIPT sub/superscript {min(script)} pt < {0.7 * spec['font_min_pt']:.1f} pt — enlarge the parent text")
        if not sizes:
            issues.append("NO live text in PDF (outlined or rasterised) — journals want editable text")
        ftypes, type3_glyphs = set(), 0
        def _scan(fonts):
            nonlocal type3_glyphs
            for f in (fonts or {}).values():
                fo = f.get_object()
                ftypes.add(str(fo.get("/Subtype")))
                if str(fo.get("/Subtype")) == "/Type3":
                    procs = fo.get("/CharProcs")
                    procs = procs.get_object() if procs is not None else {}
                    type3_glyphs += len(procs)
        for page in PdfReader(path).pages:
            res = page.get("/Resources") or {}
            _scan(res.get("/Font"))
            for x in (res.get("/XObject") or {}).values():
                _scan((x.get_object().get("/Resources") or {}).get("/Font"))
        info["font_types"] = sorted(ftypes)
        if type3_glyphs > 1 or unknown_visible:   # a lone Type 3 space glyph (cairo artefact) is harmless
            issues.append(f"Type 3 fonts with {type3_glyphs} glyph(s) — matplotlib: rcParams['pdf.fonttype'] = 42; R: cairo_pdf / embedFonts")
    else:
        from PIL import Image
        with Image.open(path) as im:
            im.load()
            size, mode, dpi = im.size, im.mode, im.info.get("dpi", (None, None))[0]
        info.update(px=size, mode=mode, dpi=round(float(dpi)) if dpi else None)
        if dpi:
            info["width_mm"] = round(size[0] / float(dpi) * MM_PER_INCH, 1)
            info["height_mm"] = round(size[1] / float(dpi) * MM_PER_INCH, 1)
            if float(dpi) < 299:
                issues.append(f"DPI {float(dpi):.0f} < 300")
            if spec.get("max_dpi") and float(dpi) > spec["max_dpi"] + 1:
                issues.append(f"DPI {float(dpi):.0f} > journal max {spec['max_dpi']}")
        else:
            issues.append("No dpi metadata — print size undefined")
        if mode not in ("RGB", "L"):
            issues.append(f"Colour mode {mode} — save RGB without alpha unless CMYK is requested")
    if info.get("width_mm"):
        if not width_ok(info["width_mm"], spec):
            issues.append(f"WIDTH {info['width_mm']} mm not an allowed width {spec['widths_mm']} / ranges {spec.get('width_ranges_mm')}")
        if info.get("height_mm") and info["height_mm"] > spec["max_height_mm"] + 0.5:
            issues.append(f"HEIGHT {info['height_mm']} mm > {spec['max_height_mm']} mm")
    if verbose:
        print(f"[audit_file] {path} | {info} | " + ("PASS" if not issues else f"{len(issues)} issue(s)"))
        for s in issues:
            print("  -", s)
    _raise_if(issues, strict, f"audit_file({path})")
    return issues


def srgb_to_lab(rgb):
    """sRGB in [0,1], shape (N,3) -> CIELAB (D65)."""
    rgb = np.asarray(rgb, float)
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = lin @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], axis=1)


def simulate_cvd(rgb, kind="deuteranopia"):
    """Colour-vision-deficiency simulation (Machado et al. 2009, severity 1) or greyscale, on sRGB (...,3) in [0,1]."""
    mats = {"protanopia": [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
            "deuteranopia": [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
            "tritanopia": [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]]}
    rgb = np.asarray(rgb, float)
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    if kind == "grayscale":
        y = lin @ np.array([0.2126, 0.7152, 0.0722])
        out = np.repeat(y[..., None], 3, axis=-1)
    else:
        out = np.clip(lin @ np.array(mats[kind]).T, 0, 1)
    return np.where(out <= 0.0031308, out * 12.92, 1.055 * np.power(out, 1 / 2.4) - 0.055)


def check_palette(colors, min_delta_e=12.0, verbose=True):
    """Minimum pairwise CIELAB ΔE of a categorical palette under normal, deutan, protan, tritan and greyscale vision."""
    rgb = np.array([mpl.colors.to_rgb(c) for c in colors])
    res = {}
    for kind in ["normal", "deuteranopia", "protanopia", "tritanopia", "grayscale"]:
        lab = srgb_to_lab(rgb if kind == "normal" else simulate_cvd(rgb, kind))
        d = np.sqrt(((lab[:, None, :] - lab[None, :, :]) ** 2).sum(-1))
        d[np.eye(len(colors), dtype=bool)] = np.inf
        i, j = np.unravel_index(np.argmin(d), d.shape)
        res[kind] = (round(float(d[i, j]), 1), colors[i], colors[j])
    if verbose:
        for k, (v, a, b) in res.items():
            flag = "" if (v >= min_delta_e or k == "grayscale") else "  <-- confusable"
            print(f"  {k:13s} min ΔE {v:5.1f} ({a} vs {b}){flag}")
    return res


def cvd_preview(fig_or_path, out_path="qc/cvd_preview.png", dpi=200):
    """QC only — never a deliverable. Renders original + deuteranopia + protanopia + tritanopia + greyscale side by side
    into qc/ (created if needed) so it cannot be mistaken for a submission file. Returns out_path."""
    import os
    if os.path.dirname(out_path):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
    from PIL import Image
    if isinstance(fig_or_path, str):
        img = np.asarray(Image.open(fig_or_path).convert("RGB"), float) / 255
    else:
        fig_or_path.canvas.draw()
        img = np.asarray(fig_or_path.canvas.buffer_rgba(), float)[..., :3] / 255
    kinds = ["original", "deuteranopia", "protanopia", "tritanopia", "grayscale"]
    h, w = img.shape[:2]
    pf, axs = plt.subplots(1, 5, figsize=(5 * w / dpi, h / dpi + 0.3), dpi=dpi)
    for ax, k in zip(axs, kinds):
        ax.imshow(img if k == "original" else simulate_cvd(img, k))
        ax.set_title(k, fontsize=7)
        ax.axis("off")
    pf.savefig(out_path, dpi=dpi)
    plt.close(pf)
    with Image.open(out_path) as im:
        rgb = im.convert("RGB")
    rgb.save(out_path)
    return out_path


def legend_template(title, panels, n_note=None, stats_note=None, source_data=None):
    """Assemble a figure legend: bold title sentence, one clause per panel, then n, statistics, source data.
    panels: list of (letter, description)."""
    parts = [f"**{title.rstrip('.')}.**"]
    for letter, desc in panels:
        parts.append(f"**{letter}**, {desc.rstrip('.')}.")
    for extra in (n_note, stats_note, source_data):
        if extra:
            parts.append(extra.rstrip(".") + ".")
    return " ".join(parts)


def annotate_heatmap(ax, M, fmt="{:.0f}", fontsize=None, min_pad_mm=0.6, threshold=None, journal="generic"):
    """Write values in heatmap cells only when they fit. Shrinks to the journal minimum font if needed;
    if they still do not fit, writes nothing and returns False (report values in a table instead).
    Text colour flips (white/black) on the cell luminance. M: 2-D array drawn with imshow/pcolormesh at integer centres."""
    spec = journal_spec(journal, quiet=True)
    M = np.asarray(M, float)
    fig = ax.figure
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bb = ax.get_window_extent(r)
    cw_mm = bb.width / M.shape[1] / fig.dpi * MM_PER_INCH
    ch_mm = bb.height / M.shape[0] / fig.dpi * MM_PER_INCH
    longest = max(len(fmt.format(v)) for v in M.ravel() if np.isfinite(v))
    fs = fontsize or mpl.rcParams["xtick.labelsize"]
    def fits(f):  # Arial digit ~0.56 em wide, cap height ~0.72 em
        return longest * 0.56 * f / 72 * MM_PER_INCH + min_pad_mm <= cw_mm and 0.9 * f / 72 * MM_PER_INCH <= ch_mm
    while not fits(fs) and fs > spec["font_min_pt"]:
        fs -= 0.5
    if not fits(fs):
        print(f"[data-visualization] cells {cw_mm:.1f} x {ch_mm:.1f} mm too small for '{fmt.format(M.flat[0])}' at "
              f"{spec['font_min_pt']} pt — no annotations; widen the panel, transpose, or give values in a table")
        return False
    im = ax.get_images()[0] if ax.get_images() else (ax.collections[0] if ax.collections else None)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if not np.isfinite(M[i, j]):
                continue
            col = "black"
            if im is not None:
                rgb = np.array(im.cmap(im.norm(M[i, j]))[:3])
                col = "white" if (rgb @ [0.2126, 0.7152, 0.0722]) < 0.45 else "black"
            ax.text(j, i, fmt.format(M[i, j]), ha="center", va="center", fontsize=fs, color=col)
    return True


def clean_log_axis(ax, axis="x", fmt=None, labels_at=(1, 2, 5)):
    """Readable log axis: labels only at 1-2-5 x 10^k inside the view range, plain numbers (no '2 x 10^-2' clutter),
    unlabelled minor ticks. fmt: callable(value)->str, e.g. lambda v: f"${v:g}"."""
    from matplotlib.ticker import FixedLocator, FuncFormatter, LogLocator, NullFormatter
    a = ax.xaxis if axis == "x" else ax.yaxis
    (ax.set_xscale if axis == "x" else ax.set_yscale)("log")
    lo, hi = sorted(a.get_view_interval())
    ticks = [m * 10 ** k for k in range(int(math.floor(math.log10(lo))) - 1, int(math.ceil(math.log10(hi))) + 1)
             for m in labels_at if lo <= m * 10 ** k <= hi]
    if len(ticks) > 6:
        ticks = [t for t in ticks if round(t / 10 ** math.floor(math.log10(t))) in (1, 5)] or ticks
    a.set_major_locator(FixedLocator(ticks))
    a.set_major_formatter(FuncFormatter(lambda v, _: fmt(v) if fmt else f"{v:g}"))
    a.set_minor_locator(LogLocator(subs=np.arange(2, 10)))
    a.set_minor_formatter(NullFormatter())
    return ticks


def check_legend(legend_text, fig=None, panels=None, verbose=True, strict=False):
    """Check a figure legend before delivery: unfilled placeholders (X, XX, TBD, [..], ??), and that the panel letters
    named in the legend match the panels drawn by add_panel_labels (or `panels`). Returns issue list."""
    import re as _re
    issues = []
    for pat, why in [(r"\bn\s*=\s*(X+|\?+|N)\b", "n placeholder"), (r"\bTBD\b|\bTODO\b|XXX|\?\?", "placeholder"),
                     (r"\[(?:X+|N|n|\?+|value|insert[^\]]*|add[^\]]*|fill[^\]]*|TBD|tbd|\.\.\.)\]", "bracketed placeholder"), (r"\bP\s*=\s*(X|\?)", "P placeholder")]:
        m = _re.search(pat, legend_text)
        if m:
            issues.append(f"LEGEND {why}: '{m.group(0)}' — compute the value in the script and insert it")
    named = set(_re.findall(r"\*\*\(?([A-Ha-h])\)?\*\*", legend_text)) | set(_re.findall(r"\(([A-Ha-h])\)", legend_text))
    named = {c.lower() for c in named}
    drawn = None
    if panels is not None:
        drawn = {str(p).strip("()").lower() for p in panels}
    elif fig is not None and getattr(fig, "_pf_panel_letters", None):
        drawn = {p.strip("()").lower() for p in fig._pf_panel_letters}
    if drawn is not None and named:
        if named - drawn:
            issues.append(f"LEGEND names panel(s) {sorted(named - drawn)} that are not in the figure {sorted(drawn)}")
        if drawn - named:
            issues.append(f"LEGEND does not describe panel(s) {sorted(drawn - named)}")
    if verbose:
        print("[check_legend] " + ("PASS" if not issues else f"{len(issues)} issue(s)"))
        for x in issues:
            print("  -", x)
    _raise_if(issues, strict, "check_legend")
    return issues


def fit_tick_labels(ax, axis="x", width_chars=(14, 10), max_lines=2, abbrev=12):
    """Make category tick labels fit without overlap. Tries in order: horizontal; wrapped at word boundaries
    (never mid-word); 45 deg; 90 deg; abbreviated with '…'. Re-checks with the exact rotated-box test each time and
    stops at the first layout with no collisions. Returns the strategy used. Call it after set_xticklabels / set_yticklabels."""
    import textwrap
    a = ax.xaxis if axis == "x" else ax.yaxis
    fig = ax.figure
    orig = [t.get_text() for t in a.get_ticklabels()]
    if not any(orig):
        fig.canvas.draw()
        orig = [t.get_text() for t in a.get_ticklabels()]
    def wrap(t, w):
        lines = textwrap.wrap(t, w, break_long_words=False, break_on_hyphens=True) or [t]
        return "\n".join(lines[:max_lines]) if len(lines) <= max_lines else None
    def collide():
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
        labs = [t for t in a.get_ticklabels() if t.get_visible() and t.get_text().strip()]
        lo, hi = sorted(a.get_view_interval())
        labs = [t for t in labs if lo - 1e-9 <= (t.get_position()[0] if axis == "x" else t.get_position()[1]) <= hi + 1e-9]
        rects = [_text_rect(t, r) for t in labs]
        return any(_rect_overlap(rects[i], rects[i + 1], shrink=1.12) for i in range(len(rects) - 1))   # demand ~1 char-height clearance
    def setl(texts, rot):
        if axis == "x":
            ha = "center" if rot in (0, 90) else "right"
            ax.set_xticks(a.get_majorticklocs(), texts, rotation=rot, ha=ha, rotation_mode="anchor" if rot not in (0, 90) else "default")
        else:
            ax.set_yticks(a.get_majorticklocs(), texts, rotation=0 if rot == 0 else rot)
    tries = [("horizontal", orig, 0)]
    for w in width_chars:
        wr = [wrap(t, w) for t in orig]
        if all(x is not None for x in wr):
            tries.append((f"wrapped@{w}", wr, 0))
    if axis == "x":
        tries += [("rotated 45", orig, 45), ("rotated 90", orig, 90)]
    short = [t if len(t) <= abbrev else t[:abbrev - 1].rstrip() + "…" for t in orig]
    tries += [("abbreviated 90" if axis == "x" else "abbreviated", short, 90 if axis == "x" else 0)]
    for name, texts, rot in tries:
        setl(texts, rot)
        if not collide():
            if name.startswith("abbreviated"):
                print("[data-visualization] tick labels abbreviated — define the abbreviations in the figure legend")
            return name
    print("[data-visualization] tick labels still collide — widen the panel, transpose the plot, or use fewer categories")
    return "unresolved"


def add_colorbar(fig, mappable, ax, label="", location="right", fraction=0.05, shrink=0.8, ticks=None):
    """Layout-managed colour bar (constrained layout reserves room, so tick labels and title are never clipped).
    ax: axes (or list of axes) the bar belongs to. Use this instead of fig.add_axes / cax=."""
    cb = fig.colorbar(mappable, ax=ax, location=location, fraction=fraction, shrink=shrink, ticks=ticks)
    cb.set_label(label, size=mpl.rcParams["axes.labelsize"])
    cb.outline.set_linewidth(mpl.rcParams["axes.linewidth"])
    cb.ax.tick_params(labelsize=mpl.rcParams["xtick.labelsize"], width=mpl.rcParams["xtick.major.width"], length=2)
    return cb


def add_size_legend(ax, values, sizes, title="", fmt="{:g}", color="0.4", loc="outside right upper"):
    """Legend for a size encoding (dot plots, bubble charts). values: data values shown, sizes: the matching scatter
    `s` values (points^2). Drawn as a figure legend with an 'outside ...' location, which constrained layout reserves
    room for, so it is never clipped and never covers data. Works alongside add_colorbar (bar beside the axes,
    key at the figure's right edge). Other locations: 'outside right lower', 'outside lower center'."""
    from matplotlib.lines import Line2D
    h = [Line2D([], [], ls="", marker="o", markersize=math.sqrt(s), markerfacecolor="white", markeredgecolor=color,
                markeredgewidth=0.6, label=fmt.format(v)) for v, s in zip(values, sizes)]
    return ax.figure.legend(handles=h, title=title, loc=loc, frameon=False, labelspacing=0.9, handletextpad=0.4)
