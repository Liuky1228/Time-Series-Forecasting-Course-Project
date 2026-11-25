# run_all.R -- run the complete final analysis from the final/ directory
ROOT <- normalizePath(".")
source(file.path(ROOT, "R", "01_load.R"))
source(file.path(ROOT, "R", "02_eda.R"))
source(file.path(ROOT, "R", "03_stationarity.R"))
source(file.path(ROOT, "R", "03_cny.R"))
source(file.path(ROOT, "R", "04_models.R"))
source(file.path(ROOT, "R", "05_rolling_forecast.R"))
source(file.path(ROOT, "R", "06_diagnostics.R"))
source(file.path(ROOT, "R", "07_final_forecast.R"))
source(file.path(ROOT, "R", "08_robustness.R"))

writeLines(capture.output(sessionInfo()),
           file.path(ROOT, "output", "tables", "sessionInfo.txt"))
cat("\nALL DONE\n")
