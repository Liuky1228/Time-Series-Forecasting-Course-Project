# 04_models.R -- model registry, fitting and forecasting helpers
if (!exists("ROOT")) ROOT <- normalizePath(".")
source(file.path(ROOT, "R", "01_load.R"))
INCUMBENT <- "SARIMA_011_110"

# The SARIMA order (0,1,1)(0,1,1)[4] is the parsimonious specification selected
# in the interim analysis.  Covariate models keep this order fixed so that any
# change in forecast accuracy can be attributed to the added covariate rather
# than to a different ARMA structure.
MODELS <- list(
  list(id = "Mean", label = "Mean", family = "Benchmark", type = "bench", fun = "mean", start = c(1994, 1)),
  list(id = "Naive", label = "Naive", family = "Benchmark", type = "bench", fun = "naive", start = c(1994, 1)),
  list(id = "SNaive", label = "Seasonal naive", family = "Benchmark", type = "bench", fun = "snaive", start = c(1994, 1)),

  list(id = "SARIMA_011_011", label = "SARIMA(0,1,1)(0,1,1)", family = "SARIMA",
       type = "arima", order = c(0, 1, 1), seasonal = c(0, 1, 1),
       include.drift = FALSE, xreg = NULL, start = c(1994, 1)),
  list(id = "SARIMA_111_011", label = "SARIMA(1,1,1)(0,1,1)", family = "SARIMA",
       type = "arima", order = c(1, 1, 1), seasonal = c(0, 1, 1),
       include.drift = FALSE, xreg = NULL, start = c(1994, 1)),
  list(id = "SARIMA_011_001_drift", label = "SARIMA(0,1,1)(0,0,1) + drift", family = "SARIMA",
       type = "arima", order = c(0, 1, 1), seasonal = c(0, 0, 1),
       include.drift = TRUE, xreg = NULL, start = c(1994, 1)),
  list(id = "SARIMA_011_001", label = "SARIMA(0,1,1)(0,0,1)", family = "SARIMA",
       type = "arima", order = c(0, 1, 1), seasonal = c(0, 0, 1),
       include.drift = FALSE, xreg = NULL, start = c(1994, 1)),
  list(id = "SARIMA_011_110", label = "SARIMA(0,1,1)(1,1,0)", family = "SARIMA",
       type = "arima", order = c(0, 1, 1), seasonal = c(1, 1, 0),
       include.drift = FALSE, xreg = NULL, start = c(1994, 1)),
  list(id = "SARIMA_011_111", label = "SARIMA(0,1,1)(1,1,1)", family = "SARIMA",
       type = "arima", order = c(0, 1, 1), seasonal = c(1, 1, 1),
       include.drift = FALSE, xreg = NULL, start = c(1994, 1)),

  list(id = "SARIMAX_CNY", label = "SARIMAX + CNY", family = "SARIMAX",
       type = "arima", order = c(0, 1, 1), seasonal = c(0, 1, 1),
       include.drift = FALSE, xreg = "cny_q1_frac", start = c(1994, 1)),
  list(id = "SARIMAX_CNY_jan", label = "SARIMAX + CNY (Jan dummy)", family = "SARIMAX",
       type = "arima", order = c(0, 1, 1), seasonal = c(0, 1, 1),
       include.drift = FALSE, xreg = "cny_jan", start = c(1994, 1)),
  list(id = "SARIMAX_PMI", label = "SARIMAX + PMI(-2)", family = "SARIMAX",
       type = "arima", order = c(0, 1, 1), seasonal = c(0, 1, 1),
       include.drift = FALSE, xreg = "pmi_lag2", start = start_pmi),
  list(id = "SARIMAX_CNY_PMI", label = "SARIMAX + CNY + PMI(-2)", family = "SARIMAX",
       type = "arima", order = c(0, 1, 1), seasonal = c(0, 1, 1),
       include.drift = FALSE, xreg = c("cny_q1_frac", "pmi_lag2"), start = start_pmi),

  list(id = "ETS_AAA", label = "ETS(A,A,A)", family = "ETS",
       type = "ets", model = "AAA", damped = TRUE, start = c(1994, 1))
)

ORIGINAL_MODEL_IDS <- vapply(MODELS, `[[`, character(1), "id")
MODELS <- c(MODELS, list(
  list(id = "SARIMA_011_101", label = "SARIMA(0,1,1)(1,0,1)", family = "SARIMA",
       type = "arima", order = c(0, 1, 1), seasonal = c(1, 0, 1),
       include.drift = FALSE, xreg = NULL, start = c(1994, 1)),
  list(id = "SARIMA_011_011_2005Q3", label = "SARIMA(0,1,1)(0,1,1), 2005Q3 start", family = "SARIMA",
       type = "arima", order = c(0, 1, 1), seasonal = c(0, 1, 1),
       include.drift = FALSE, xreg = NULL, start = start_pmi),
  list(id = "SARIMAX_CNY_2005Q3", label = "SARIMAX + CNY, 2005Q3 start", family = "SARIMAX",
       type = "arima", order = c(0, 1, 1), seasonal = c(0, 1, 1),
       include.drift = FALSE, xreg = "cny_q1_frac", start = start_pmi)
))

model_by_id <- function(id) {
  for (m in MODELS) if (m$id == id) return(m)
  stop("Unknown model: ", id)
}

model_start <- function(m) {
  if (is.null(m$start)) c(1994, 1) else m$start
}

get_train_val <- function(m, origin) {
  window(val_r, start = model_start(m), end = origin)
}

get_train_log <- function(m, origin) {
  window(log_r, start = model_start(m), end = origin)
}

get_train_xreg <- function(m, origin) {
  if (is.null(m$xreg)) return(NULL)
  window(X_all[, m$xreg, drop = FALSE], start = model_start(m), end = origin)
}

future_xreg <- function(m, origin, h = 2) {
  if (is.null(m$xreg)) return(NULL)
  idx0 <- qidx(origin[1], origin[2])
  out <- matrix(NA_real_, nrow = h, ncol = length(m$xreg),
                dimnames = list(NULL, m$xreg))
  for (i in seq_len(h)) {
    ti <- idx0 + i
    tq <- qtime(ti)
    ty <- tq[1]; tquarter <- tq[2]

    if ("cny_q1_frac" %in% m$xreg) {
      out[i, "cny_q1_frac"] <- if (tquarter == 1) {
        cny$frac_q1_before_cny[match(ty, cny$year)]
      } else 0
    }
    if ("cny_jan" %in% m$xreg) {
      out[i, "cny_jan"] <- if (tquarter == 1) {
        as.integer(cny$cny_month[match(ty, cny$year)] == 1)
      } else 0
    }
    if ("pmi_lag1" %in% m$xreg) {
      j <- (ty - 2005) * 4 + tquarter - 1
      if (ti - 1 <= idx0 && j >= 1 && j <= length(pmi_vec)) out[i, "pmi_lag1"] <- pmi_vec[j]
    }
    if ("pmi_lag2" %in% m$xreg) {
      j <- (ty - 2005) * 4 + tquarter - 2
      if (ti - 2 <= idx0 && j >= 1 && j <= length(pmi_vec)) out[i, "pmi_lag2"] <- pmi_vec[j]
    }
  }
  if (any(!is.finite(out))) stop("Required future xreg is missing or unavailable at origin")
  out
}

capture_attempt <- function(expr) {
  warnings <- character()
  error <- NULL
  value <- tryCatch(withCallingHandlers(force(expr), warning = function(w) {
    warnings <<- c(warnings, conditionMessage(w))
    invokeRestart("muffleWarning")
  }), error = function(e) {
    error <<- e
    NULL
  })
  list(value = value, warnings = warnings, error = error)
}

attempt_events <- function(result, attempt) {
  out <- data.frame(attempt = character(), status = character(), message = character())
  if (length(result$warnings)) {
    out <- rbind(out, data.frame(attempt = attempt, status = "warning", message = result$warnings))
  }
  if (!is.null(result$error)) {
    out <- rbind(out, data.frame(attempt = attempt, status = "error", message = conditionMessage(result$error)))
  }
  out
}

capture_model_step <- function(expr, origin, model, stage) {
  result <- capture_attempt(expr)
  events <- attempt_events(result, stage)
  if (stage == "fit") {
    details <- if (is.null(result$error)) result$value$events else attr(result$error, "events")
    events <- rbind(details, events)
  }
  result$events <- data.frame(origin = rep(origin, nrow(events)), model = rep(model, nrow(events)),
                              stage = rep(stage, nrow(events)), events)
  result
}

fit_one <- function(m, origin) {
  tv <- get_train_val(m, origin)
  tl <- get_train_log(m, origin)
  if (m$type == "bench") {
    return(list(fit = NULL, train_val = tv, train_log = tl, status = "default"))
  }
  xr <- NULL
  if (m$type == "arima") {
    xr <- get_train_xreg(m, origin)
    if (any(!is.finite(xr))) stop("Training xreg has missing or non-finite values")
    fit_arima <- function(control = list()) {
      # Keep xreg omitted when the specification has no covariates.
      fit <- if (is.null(xr)) {
        Arima(tl, order = m$order, seasonal = m$seasonal,
              include.drift = m$include.drift, method = "ML", optim.control = control)
      } else {
        Arima(tl, order = m$order, seasonal = m$seasonal,
              include.drift = m$include.drift, xreg = xr, method = "ML", optim.control = control)
      }
      if (!identical(as.integer(fit$code), 0L)) {
        stop("ARIMA optimizer did not converge (code ", paste(fit$code, collapse = ", "), ")")
      }
      if (any(!is.finite(coef(fit))) || !is.finite(fit$sigma2) || fit$sigma2 <= 0) {
        stop("Invalid ARIMA coefficients or residual variance")
      }
      fit
    }
    result <- capture_attempt(fit_arima())
    retry <- function() fit_arima(list(maxit = 2000))
    retry_status <- "retried_ml"
  } else if (m$type == "ets") {
    result <- capture_attempt(ets(tl, model = m$model, damped = m$damped))
    retry <- function() ets(tl, model = "ZZZ", restrict = TRUE)
    retry_status <- "fallback_auto_ets"
  } else {
    stop("Unknown model type: ", m$type)
  }
  status <- "default"
  events <- attempt_events(result, status)
  if (!is.null(result$error)) {
    status <- retry_status
    result <- capture_attempt(retry())
    events <- rbind(events, attempt_events(result, status))
    if (!is.null(result$error)) {
      stop(structure(result$error, events = events))
    }
    events <- rbind(events, data.frame(attempt = status, status = "usable", message = ""))
  }
  list(fit = result$value, train_val = tv, train_log = tl, xreg = xr, status = status, events = events)
}

# Forecast on the log scale, then back-transform with a log-normal bias
# adjustment for the point forecast.  Quantiles are exp() of the log-scale
# quantiles, which is exact for a log-normal predictive distribution.
fc_one <- function(m, fit_obj, origin, h = 2, level = c(80, 95)) {
  if (m$type == "bench") {
    fc <- switch(m$fun,
      mean   = meanf(fit_obj$train_val, h = h, level = level),
      naive  = naive(fit_obj$train_val, h = h, level = level),
      snaive = snaive(fit_obj$train_val, h = h, level = level)
    )
    return(list(fc = fc, point = as.numeric(fc$mean),
                lower = fc$lower, upper = fc$upper,
                mean_log = NULL, se = NULL))
  }

  fx <- if (m$type == "arima") future_xreg(m, origin, h = h) else NULL
  fc <- forecast(fit_obj$fit, h = h, xreg = fx, level = level)
  mu <- as.numeric(fc$mean)
  # Recover the log-scale standard deviation from the highest requested upper quantile.
  j <- which.max(fc$level)
  se <- (as.numeric(fc$upper[, j]) - mu) / qnorm((1 + fc$level[j] / 100) / 2)
  point <- exp(mu + 0.5 * se^2)
  lower <- exp(fc$lower)
  upper <- exp(fc$upper)
  list(fc = fc, point = point, lower = lower, upper = upper,
       mean_log = mu, se = se)
}

fit_full <- function(m) fit_one(m, origin = c(2026, 2))

my_aicc <- function(fit) {
  ll <- logLik(fit)
  k  <- attr(ll, "df")
  n  <- nobs(fit)
  if (is.null(k) || is.null(n) || n - k - 1 <= 0) return(NA_real_)
  as.numeric(AIC(fit) + 2 * k * (k + 1) / (n - k - 1))
}

aicc_full <- function(m) {
  fit <- tryCatch(fit_full(m)$fit, error = function(e) NULL)
  if (is.null(fit)) return(NA_real_)
  tryCatch(my_aicc(fit), error = function(e) NA_real_)
}
