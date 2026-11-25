# Rscript --vanilla <project>/R/run_all.R can run from any working directory.
if (.Platform$OS.type == "windows" && !l10n_info()[["UTF-8"]]) {
  invisible(Sys.setlocale("LC_CTYPE", ".UTF-8"))
}
script <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
if (length(script) != 1L) stop("Run this entry point with Rscript --vanilla <project>/R/run_all.R")
ROOT <- dirname(dirname(normalizePath(script, winslash = "/", mustWork = TRUE)))
output_dir <- file.path(ROOT, "output")
dir.create(output_dir, showWarnings = FALSE)
status_path <- file.path(output_dir, "analysis_status.txt")
writeLines("RUNNING", status_path)

stages <- c("02_eda.R", "03_stationarity.R", "03_cny.R", "05_rolling_forecast.R",
            "06_diagnostics.R", "07_final_forecast.R", "08_robustness.R", "09_optimization.R")
set.seed(4003)
tryCatch({
  for (stage in stages) source(file.path(ROOT, "R", stage))
  writeLines(capture.output(sessionInfo()), file.path(TABDIR, "sessionInfo.txt"))
}, error = function(e) {
  writeLines(c("FAILED", paste("Stage:", stage), conditionMessage(e)), status_path)
  stop(e)
})
writeLines("COMPLETE", status_path)
cat("\nALL DONE\n")
