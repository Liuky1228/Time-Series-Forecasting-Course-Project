ROOT   <- "/Users/keyi/Desktop/STA4003/interim"
DATA   <- "/Users/keyi/Desktop/STA4003/proposal/data"
FIGDIR <- file.path(ROOT, "output", "figures")
TABDIR <- file.path(ROOT, "output", "tables")
for (d in c(FIGDIR, TABDIR)) dir.create(d, showWarnings = FALSE, recursive = TRUE)

suppressPackageStartupMessages({
  library(forecast)
  library(tseries)
  library(ggplot2)
})
theme_set(theme_bw(base_size = 11))

save_gg <- function(p, name, width = 7, height = 4.0) {
  ggsave(file.path(FIGDIR, name), p, width = width, height = height, dpi = 300)
  cat("saved figure:", name, "\n")
}
write_tab <- function(x, name) {
  write.csv(x, file.path(TABDIR, name), row.names = FALSE)
  cat("saved table:", name, "\n")
}
