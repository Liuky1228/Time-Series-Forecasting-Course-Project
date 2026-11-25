if (!exists("ROOT")) ROOT <- "/Users/keyi/Desktop/STA4003/interim"
source(file.path(ROOT, "R", "01_load.R"))

adf_p <- function(x) tryCatch(adf.test(x)$p.value, error = function(e) NA)
kps_p <- function(x) tryCatch(kpss.test(x)$p.value, error = function(e) NA)
adf_s <- function(x) tryCatch(adf.test(x)$statistic, error = function(e) NA)
kps_s <- function(x) tryCatch(kpss.test(x)$statistic, error = function(e) NA)

series <- list("log(retail)" = log_r,
               "diff(log), d=1" = diff(log_r, 1),
               "diff(log, 4), D=1" = diff(log_r, 4),
               "diff(diff(log,1), 4), d=1 D=1" = diff(diff(log_r, 1), 4))
stat_tab <- data.frame(
  Series = names(series),
  ADF_stat = sprintf("%.2f", sapply(series, adf_s)),
  ADF_p = ifelse(sapply(series, adf_p) <= 0.01, "<0.01",
                 sprintf("%.3f", sapply(series, adf_p))),
  KPSS_stat = sprintf("%.2f", sapply(series, kps_s)),
  KPSS_p = ifelse(sapply(series, kps_p) <= 0.01, "<0.01",
                  sprintf("%.3f", sapply(series, kps_p)))
)
write_tab(stat_tab, "tab_stationarity.csv")
cat("\n== ADF (H0: unit root) / KPSS (H0: level stationarity)\n")
print(stat_tab)

fig5 <- ggAcf(diff(diff(log_r, 1), 4), lag.max = 40) +
  labs(title = "Figure 5: ACF after log + d = 1 + D = 1 differencing")
save_gg(fig5, "fig5_acf_after_diff.png", 7, 3.8)

figA2 <- ggAcf(diff(log_r, 1), lag.max = 40) +
  labs(title = "Appendix Figure A2: ACF of first-differenced log retail (d = 1, D = 0)")
save_gg(figA2, "figA2_acf_first_diff.png", 7, 3.8)
