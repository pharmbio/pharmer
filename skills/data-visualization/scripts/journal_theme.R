# data-visualization skill — ggplot2 companion to pubfig.py / kernel.py
# Usage:  source("journal_theme.R"); p <- ggplot(...) + theme_journal("nature")
#         save_journal(p, "fig1", journal = "nature", width = "double", height_mm = 80)
# Numbers mirror JOURNAL_SPECS in kernel.py (see references/journal_specs.md).
suppressPackageStartupMessages(library(ggplot2))

JOURNALS <- list(
  nature   = list(widths = c(single = 89, onehalf = 120, double = 183), max_h = 170, base = 7, min = 5, label_case = "lower", label_size = 8, dpi = 450, fmt = c("pdf", "png")),
  cell     = list(widths = c(single = 85, onehalf = 114, double = 174), max_h = 225, base = 7, min = 6, label_case = "upper", label_size = 8, dpi = 500, fmt = c("pdf", "tiff")),
  science  = list(widths = c(single = 90, onehalf = 144, double = 184), max_h = 199, base = 7, min = 6, label_case = "upper", label_size = 9, dpi = 300, fmt = c("pdf", "tiff")),
  pnas     = list(widths = c(single = 87, onehalf = 114, double = 178), max_h = 225, base = 7, min = 6, label_case = "upper", label_size = 9, dpi = 600, fmt = c("pdf", "tiff")),
  plos     = list(widths = c(single = 132, double = 190.5), max_h = 222.3, base = 8, min = 8, label_case = "upper", label_size = 10, dpi = 600, fmt = c("tiff")),
  elife    = list(widths = c(single = 100, double = 200), max_h = 240, base = 7, min = 6, label_case = "upper", label_size = 9, dpi = 300, fmt = c("pdf", "tiff")),
  elsevier = list(widths = c(single = 90, onehalf = 140, double = 190), max_h = 240, base = 7, min = 6, label_case = "lower", label_size = 8, dpi = 500, fmt = c("pdf", "tiff")),
  acs      = list(widths = c(single = 82.5, double = 177.8), max_h = 232.8, base = 7, min = 6, label_case = "lower", label_size = 8, dpi = 600, fmt = c("pdf", "tiff")),
  neurips  = list(widths = c(single = 139.7, half = 68), max_h = 200, base = 8, min = 6, label_case = "lower", label_size = 9, dpi = 300, fmt = c("pdf")),
  icml     = list(widths = c(single = 82.6, double = 171.5), max_h = 220, base = 7, min = 6, label_case = "lower", label_size = 8, dpi = 300, fmt = c("pdf")),
  generic  = list(widths = c(single = 89, onehalf = 136, double = 183), max_h = 170, base = 7, min = 6, label_case = "lower", label_size = 8, dpi = 600, fmt = c("pdf", "png"))
)

OKABE_ITO <- c("#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#CC79A7", "#F0E442", "#000000")
# ggplot linewidth L draws lwd = L * .pt (1/96 in units), i.e. L * .pt * 0.75 pt  ->  inverse:
pt_lw <- function(pt) pt / (ggplot2::.pt * 0.75)

theme_journal <- function(journal = "generic", base_size = NULL, family = "Arial") {
  s <- JOURNALS[[journal]]
  if (is.null(s)) { message("unknown journal -> generic"); s <- JOURNALS$generic }
  b <- if (is.null(base_size)) s$base else base_size
  small <- max(s$min, b - 1)
  lw <- pt_lw(0.6)                                   # 0.6 pt axis lines
  theme_classic(base_size = b, base_family = family) %+replace% theme(
    axis.text = element_text(size = small, colour = "black"),
    axis.title = element_text(size = b),
    axis.line = element_line(linewidth = lw, colour = "black"),
    axis.ticks = element_line(linewidth = lw, colour = "black"),
    axis.ticks.length = unit(0.8, "mm"),
    legend.text = element_text(size = small), legend.title = element_text(size = small),
    legend.key.size = unit(3, "mm"), legend.background = element_blank(),
    strip.text = element_text(size = b), strip.background = element_blank(),
    plot.title = element_text(size = b, hjust = 0),
    plot.tag = element_text(size = s$label_size, face = "bold"),
    plot.margin = margin(1, 1, 1, 1, "mm")
  )
}

scale_colour_okabe <- function(...) scale_colour_manual(values = OKABE_ITO, ...)
scale_fill_okabe <- function(...) scale_fill_manual(values = OKABE_ITO, ...)

panel_tags <- function(journal = "generic") {
  # for patchwork: p1 + p2 + plot_annotation(tag_levels = panel_tags("cell"))
  if (JOURNALS[[journal]]$label_case == "upper") "A" else "a"
}

save_journal <- function(plot, stem, journal = "generic", width = "single", height_mm = NULL, aspect = 0.75, formats = NULL) {
  s <- JOURNALS[[journal]]
  w <- if (is.numeric(width)) width else unname(s$widths[[width]])
  h <- if (is.null(height_mm)) w * aspect else height_mm
  if (h > s$max_h) warning(sprintf("height %.0f mm > %s max %.0f mm", h, journal, s$max_h))
  fmts <- if (is.null(formats)) s$fmt else formats
  out <- character(0)
  for (f in fmts) {
    path <- paste0(stem, ".", f)
    if (f == "pdf") ggsave(path, plot, width = w, height = h, units = "mm", device = cairo_pdf)
    else if (f %in% c("tif", "tiff")) ggsave(path, plot, width = w, height = h, units = "mm", dpi = min(s$dpi, 600), compression = "lzw", device = "tiff")
    else ggsave(path, plot, width = w, height = h, units = "mm", dpi = s$dpi)
    out <- c(out, path)
  }
  invisible(out)
}
