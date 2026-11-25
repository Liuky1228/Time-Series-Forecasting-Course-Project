# 00_setup.R -- project paths, packages, and small helpers
if (!exists("ROOT")) ROOT <- normalizePath(".", winslash = "/")
if (!dir.exists(file.path(ROOT, "R")) || !dir.exists(file.path(ROOT, "data"))) {
  stop("Project root must contain R/ and data/.")
}

DATA   <- file.path(ROOT, "data")
FIGDIR <- file.path(ROOT, "output", "figures")
TABDIR <- file.path(ROOT, "output", "tables")
MODDIR <- file.path(ROOT, "output", "models")
EQDIR  <- file.path(ROOT, "output", "equations")
for (d in c(FIGDIR, TABDIR, MODDIR, EQDIR)) dir.create(d, showWarnings = FALSE, recursive = TRUE)

suppressPackageStartupMessages({
  library(forecast)
  library(tseries)
  library(ggplot2)
  library(lmtest)
  library(zoo)
  library(scales)
  library(cowplot)
  library(dplyr)
  library(tidyr)
})

theme_set(theme_bw(base_size = 11) +
            theme(panel.grid.minor = element_blank()))

save_gg <- function(p, name, width = 7, height = 4.0) {
  ggsave(file.path(FIGDIR, name), p, width = width, height = height, dpi = 300)
  cat("saved figure:", name, "\n")
}

write_tab <- function(x, name) {
  write.csv(x, file.path(TABDIR, name), row.names = FALSE, na = "")
  cat("saved table:", name, "\n")
}

# Quarter index helpers: 1994Q1 = 1, 1994Q2 = 2, ...
qidx <- function(year, q, start_year = 1994) (year - start_year) * 4 + q
qtime <- function(idx, start_year = 1994) {
  c(start_year + (idx - 1) %/% 4, (idx - 1) %% 4 + 1)
}
qlabel <- function(year, q) paste0(year, "Q", q)
fmt <- function(x, digits = 1) formatC(x, format = "f", digits = digits, big.mark = ",")
