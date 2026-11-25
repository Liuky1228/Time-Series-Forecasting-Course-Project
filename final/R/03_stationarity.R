# 03_stationarity.R -- ADF and KPSS tests
if (!exists("ROOT")) ROOT <- normalizePath(".")
source(file.path(ROOT, "R", "01_load.R"))

adf_p <- function(x) tryCatch(adf.test(x)$p.value, error = function(e) NA_real_)
kps_p <- function(x) tryCatch(kpss.test(x)$p.value, error = function(e) NA_real_)
adf_s <- function(x) tryCatch(as.numeric(adf.test(x)$statistic), error = function(e) NA_real_)
kps_s <- function(x) tryCatch(as.numeric(kpss.test(x)$statistic), error = function(e) NA_real_)

series <- list(
  "log(retail)"                         = log_r,
  "diff(log), d = 1"                    = diff(log_r, 1),
  "diff(log, 4), D = 1"                 = diff(log_r, 4),
  "diff(diff(log, 1), 4), d = 1, D = 1" = diff(diff(log_r, 1), 4)
)

stat_tab <- data.frame(
  Series   = names(series),
  ADF_stat = round(sapply(series, adf_s), 2),
  ADF_p    = sapply(series, adf_p),
  KPSS_stat = round(sapply(series, kps_s), 2),
  KPSS_p   = sapply(series, kps_p)
)
stat_tab$ADF_p_txt  <- ifelse(stat_tab$ADF_p  <= 0.01, "<0.01", sprintf("%.3f", stat_tab$ADF_p))
stat_tab$KPSS_p_txt <- ifelse(stat_tab$KPSS_p <= 0.01, "<0.01", sprintf("%.3f", stat_tab$KPSS_p))
write_tab(stat_tab[, c("Series", "ADF_stat", "ADF_p_txt", "KPSS_stat", "KPSS_p_txt")],
          "tab_stationarity.csv")

cat("\n== ADF (H0: unit root) / KPSS (H0: level or trend stationarity)\n")
print(stat_tab[, c("Series", "ADF_stat", "ADF_p_txt", "KPSS_stat", "KPSS_p_txt")])
