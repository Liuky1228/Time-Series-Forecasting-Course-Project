if (.Platform$OS.type == "windows" && !l10n_info()[["UTF-8"]]) {
  invisible(Sys.setlocale("LC_CTYPE", ".UTF-8"))
}
script <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
ROOT <- dirname(dirname(normalizePath(script, winslash = "/", mustWork = TRUE)))
stopifnot(identical(readLines(file.path(ROOT, "output", "analysis_status.txt")), "COMPLETE"))
read_table <- function(name) read.csv(file.path(ROOT, "output", "tables", paste0("tab_", name, ".csv")))
read_archive <- function(name) read.csv(file.path(ROOT, "reference", "november_tables", paste0("tab_", name, ".csv")))

err <- read_table("rolling_errors")
archived <- read_archive("rolling_errors")
stopifnot(nrow(err) == 17L * 56L * 2L, all(table(err$model, err$h) == 56L),
          identical(sort(unique(err$origin)), paste0(rep(2012:2025, each = 4L), "Q", 1:4)),
          identical(sort(setdiff(unique(err$model), unique(archived$model))),
                    c("SARIMA_011_011_2005Q3", "SARIMA_011_101", "SARIMAX_CNY_2005Q3")),
          max(abs(err$point - err$actual - err$error)) < 1e-7)
same_columns <- read_table("archive_reconciliation_detail")
stopifnot(nrow(same_columns) == nrow(archived), all(table(same_columns$model, same_columns$h) == 56L))

acc <- read_table("optimization_accuracy")
point_row <- subset(acc, model == "SARIMA_011_110" & h == 2)
stopifnot(subset(point_row, period == "Q1 targets")$n == 14L,
          subset(point_row, period == "2012-2019")$n == 30L,
          subset(point_row, period == "2020-2026Q2")$n == 26L)
sel <- read_table("model_selection")
short <- c("SARIMA_011_011_2005Q3", "SARIMAX_CNY_2005Q3", "SARIMAX_PMI", "SARIMAX_CNY_PMI")
stopifnot(all(subset(sel, model %in% short)$sample_start == "2005Q3"))

supplement <- read_table("supplemental_predictions")
blend <- subset(supplement, model == "Blend50_Incumbent_SNaive")
walk <- subset(supplement, model == "WalkForward_SARIMA")
inc <- subset(err, model == "SARIMA_011_110")
sn <- subset(err, model == "SNaive")
stopifnot(nrow(blend) == 112L, nrow(walk) == 112L,
          identical(inc[c("origin", "h")], sn[c("origin", "h")]) ||
            identical(inc$origin, sn$origin) && identical(inc$h, sn$h),
          max(abs(blend$point - (inc$point + sn$point) / 2)) < 1e-7,
          all(is.na(as.matrix(blend[c("lo80", "hi80", "lo95", "hi95")]))))
choices <- read_table("walk_forward_choices")
stopifnot(nrow(choices) == 56L, all(choices$n_realized == pmax(seq_len(56L) - 2L, 0L)),
          all(choices$model[choices$n_realized < 8L] == "SARIMA_011_110"),
          all(choices$latest_realized_target[choices$n_realized > 0L] == choices$origin[choices$n_realized > 0L]))
sources <- subset(err, model %in% unique(choices$model))
indices <- match(paste(walk$origin, walk$h, choices$model[match(walk$origin, choices$origin)]),
                 paste(sources$origin, sources$h, sources$model))
stopifnot(all(walk$point == sources$point[indices]))

interval <- subset(read_table("interval_accuracy"), period == "All targets")
misses <- read_table("interval_misses")
stopifnot(nrow(interval) == 18L * 2L * 2L, all(interval$n == 56L),
          sum(interval$n - interval$covered) == nrow(misses),
          all(misses$actual < misses$lower | misses$actual > misses$upper))
cov_test <- subset(interval, model == "SARIMA_011_110" & h == 2 & level == 80)
two <- subset(inc, h == 2)
stopifnot(cov_test$covered == sum(two$actual >= two$lo80 & two$actual <= two$hi80),
          abs(cov_test$width - mean(two$hi80 - two$lo80)) < 1e-7)

final <- read_table("final_forecast")
rerun <- read_table("final_forecast_rerun")
reference <- read_archive("final_forecast")
stopifnot(identical(final[names(reference)], reference), all(final$origin == "2026Q2"),
          all(final$status == "archived primary"), all(rerun$status == "clean R rerun"),
          nrow(read_table("final_forecast_reconciliation")) == 10L)
cat("Integrated outputs passed: 17 cases, 56 origins, 2 horizons, selection, intervals and archive\n")
