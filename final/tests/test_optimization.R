if (.Platform$OS.type == "windows" && !l10n_info()[["UTF-8"]]) {
  invisible(Sys.setlocale("LC_CTYPE", ".UTF-8"))
}
script <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
root <- dirname(dirname(normalizePath(script, winslash = "/", mustWork = TRUE)))
helpers <- file.path(root, "R", "09_evaluation_helpers.R")
stopifnot("optimization evaluation must be available" = file.exists(helpers))
source(helpers)

expect_error <- function(expr, pattern) {
  result <- tryCatch(force(expr), error = conditionMessage)
  stopifnot(is.character(result), grepl(pattern, result, fixed = TRUE))
}

# Extreme yet unrealized h=2 losses and all h=1 losses must not affect selection.
scores <- data.frame(
  model = rep(c("incumbent", "other"), each = 5),
  origin_idx = rep(c(1, 2, 3, 4, 4), 2),
  target_idx = rep(c(3, 4, 5, 6, 5), 2),
  h = rep(c(2, 2, 2, 2, 1), 2),
  target = rep(c("2000Q3", "2000Q4", "2001Q1", "2001Q2", "2001Q1"), 2),
  error = c(20, 20, 5, 1, 1, 5, 5, 20, 1e6, 1e6),
  mase_scale = 10
)
prior <- choose_sarima(scores, 3, c("incumbent", "other"), min_realized = 2L)
active <- choose_sarima(scores, 5, c("incumbent", "other"), min_realized = 2L)
stopifnot(prior$model == "incumbent", prior$n_realized == 1L,
          active$model == "other", active$n_realized == 3L,
          active$latest_realized_target == "2001Q1")
tie <- transform(scores, error = 10)
stopifnot(choose_sarima(tie, 5, c("incumbent", "other"), 2L)$model == "incumbent")
expect_error(choose_sarima(scores[-2, ], 5, c("incumbent", "other"), 2L),
             "Unpaired realized h=2 losses")

band <- score_interval(actual = c(4, 5, 10, 12), lower = 5, upper = 10, level = 80)
stopifnot(identical(band$covered, c(FALSE, TRUE, TRUE, FALSE)),
          identical(band$miss_side, c("below", "", "", "above")),
          all(band$width == 5), isTRUE(all.equal(band$Winkler, c(15, 5, 5, 25))))
expect_error(score_interval(5, 10, 5, 80), "Invalid interval")
expect_error(score_interval(NA_real_, 5, 10, 80), "Invalid interval")

panel <- expand.grid(origin_idx = 10:11, model = c("incumbent", "other"), h = 1:2,
                     stringsAsFactors = FALSE)
panel <- transform(panel, target_idx = origin_idx + h, actual = 20, point = 21,
                   error = 1, mase_scale = 10, lo80 = 17, hi80 = 23, lo95 = 16, hi95 = 24)
validate_rolling_panel(panel, 10:11, c("incumbent", "other"))
expect_error(validate_rolling_panel(panel[-1, ], 10:11, c("incumbent", "other")), "Incomplete rolling panel")
expect_error(validate_rolling_panel(panel[c(1, 1, 3:8), ], 10:11, c("incumbent", "other")), "Incomplete rolling panel")
expect_error(validate_rolling_panel(transform(panel, hi95 = 22), 10:11, c("incumbent", "other")), "Invalid rolling forecasts")
panel$mase_scale[1] <- 12
expect_error(validate_rolling_panel(panel, 10:11, c("incumbent", "other")), "Common MASE scale")

cat("Focused R evaluation tests passed\n")
