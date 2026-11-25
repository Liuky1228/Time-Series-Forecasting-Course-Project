# Evaluation contracts that can be checked without fitting a model.
covid_targets <- c("2020Q1", "2020Q2", "2022Q2")

validate_rolling_panel <- function(err, origin_ids, model_ids) {
  expected <- expand.grid(origin_idx = origin_ids, model = model_ids, h = 1:2)
  key <- function(d) paste(d$origin_idx, d$model, d$h)
  if (nrow(err) != nrow(expected) || anyDuplicated(key(err)) ||
      !setequal(key(err), key(expected))) {
    stop("Incomplete rolling panel: expected one forecast per origin, model and horizon")
  }
  numbers <- c("actual", "point", "error", "mase_scale", "lo80", "hi80", "lo95", "hi95")
  if (any(!is.finite(as.matrix(err[numbers]))) ||
      any(err$target_idx != err$origin_idx + err$h) ||
      any(err$error != err$point - err$actual) || any(err$mase_scale <= 0) ||
      any(err$lo95 > err$lo80 | err$lo80 > err$hi80 | err$hi80 > err$hi95)) {
    stop("Invalid rolling forecasts, actuals, scales or intervals")
  }
  if (any(vapply(split(err$mase_scale, err$origin_idx), function(x) any(x != x[1]), logical(1)))) {
    stop("Common MASE scale must be identical across forecast cases at an origin")
  }
  if (any(vapply(split(err$actual, err$target_idx), function(x) any(x != x[1]), logical(1)))) {
    stop("Actuals must be identical across forecasts for each target")
  }
  invisible(err)
}

# Candidate order supplies the prior default and the deterministic tie-break.
choose_sarima <- function(err, origin_idx, candidates, min_realized = 8L) {
  past <- err[err$h == 2L & err$target_idx <= origin_idx & err$model %in% candidates, ]
  realized <- sort(unique(past$target_idx))
  n <- length(realized)
  if (nrow(past) != n * length(candidates) || anyDuplicated(past[c("model", "target_idx")])) {
    stop("Unpaired realized h=2 losses in chronological selection")
  }
  latest <- if (n > 0L) past$target[match(max(realized), past$target_idx)] else NA_character_
  if (n < min_realized) {
    return(data.frame(model = candidates[1], n_realized = n,
                      latest_realized_target = latest, reason = "prior default"))
  }
  mean_loss <- tapply(abs(past$error) / past$mase_scale, past$model, mean)[candidates]
  if (any(!is.finite(mean_loss))) stop("Invalid realized losses in chronological selection")
  data.frame(model = candidates[which.min(mean_loss)], n_realized = n,
             latest_realized_target = latest, reason = "minimum realized h=2 MASE")
}

score_interval <- function(actual, lower, upper, level) {
  if (length(level) != 1L || !is.finite(level) || level <= 0 || level >= 100 ||
      any(!is.finite(c(actual, lower, upper))) || any(lower > upper)) {
    stop("Invalid interval bounds, actual or level")
  }
  alpha <- (100 - level) / 100
  width <- upper - lower
  below <- actual < lower
  above <- actual > upper
  data.frame(covered = !(below | above), width = width,
             Winkler = width + (2 / alpha) * (pmax(lower - actual, 0) + pmax(actual - upper, 0)),
             miss_side = ifelse(below, "below", ifelse(above, "above", "")))
}

point_accuracy <- function(data, ...) {
  data |>
    dplyr::group_by(...) |>
    dplyr::summarise(n = dplyr::n(), MAE = mean(abs(error)), RMSE = sqrt(mean(error^2)),
                     MASE = mean(abs(error) / mase_scale), .groups = "drop")
}
