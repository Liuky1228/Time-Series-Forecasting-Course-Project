# 06_diagnostics.R -- model selection table and residual diagnostics
if (!exists("ROOT")) ROOT <- normalizePath(".")
source(file.path(ROOT, "R", "04_models.R"))

best <- read.csv(file.path(TABDIR, "tab_best_model.csv"), stringsAsFactors = FALSE)
best_id <- best$model[1]
best_m <- model_by_id(best_id)
cat("Best h=2 model:", best_id, "\n")

# ---------------- AICc table for all candidate models ----------------
sel_rows <- lapply(MODELS, function(m) {
  fit <- tryCatch(fit_full(m)$fit, error = function(e) NULL)
  if (is.null(fit)) {
    return(data.frame(model = m$id, label = m$label, family = m$family,
                      sample_start = paste(model_start(m), collapse = "Q"),
                      k = NA_integer_, AICc = NA_real_))
  }
  kk <- tryCatch(length(coef(fit)), error = function(e) NA_integer_)
  data.frame(model = m$id, label = m$label, family = m$family,
             sample_start = paste(model_start(m), collapse = "Q"),
             k = kk,
             AICc = tryCatch(my_aicc(fit), error = function(e) NA_real_))
})
sel <- bind_rows(sel_rows)
write_tab(sel, "tab_model_selection.csv")

# ---------------- Residual diagnostics for the selected model ----------------
fit_best <- fit_full(best_m)$fit
res <- residuals(fit_best)
res_num <- as.numeric(res)
fitdf <- tryCatch(length(coef(fit_best)), error = function(e) 0)
fitdf <- min(fitdf, 7)

lb8  <- Box.test(res_num, lag = 8,  type = "Ljung-Box", fitdf = fitdf)
lb12 <- Box.test(res_num, lag = 12, type = "Ljung-Box", fitdf = fitdf)
lb2  <- Box.test(res_num^2, lag = 8, type = "Ljung-Box")
sw   <- tryCatch(shapiro.test(res_num), error = function(e) NULL)

diag_tab <- data.frame(
  model = best_id,
  n = length(res_num),
  sigma2 = tryCatch(as.numeric(fit_best$sigma2), error = function(e) NA_real_),
  LB8_stat = round(as.numeric(lb8$statistic), 2),
  LB8_p = signif(lb8$p.value, 3),
  LB12_stat = round(as.numeric(lb12$statistic), 2),
  LB12_p = signif(lb12$p.value, 3),
  LB2_stat = round(as.numeric(lb2$statistic), 2),
  LB2_p = signif(lb2$p.value, 3),
  Shapiro_p = if (is.null(sw)) NA_real_ else signif(sw$p.value, 3)
)
write_tab(diag_tab, "tab_diagnostics.csv")
cat("\n== Residual diagnostics ==\n"); print(diag_tab)

# ---------------- Coefficient table ----------------
extract_coef <- function(fit, id) {
  if (inherits(fit, "Arima")) {
    est <- coef(fit)
    se  <- tryCatch(sqrt(diag(fit$var.coef)), error = function(e) rep(NA_real_, length(est)))
    tv  <- est / se
    pv  <- 2 * pt(-abs(tv), df = max(1, nobs(fit) - length(est)))
    data.frame(model = id, term = names(est),
               estimate = as.numeric(est), std_error = as.numeric(se),
               t_value = as.numeric(tv), p_value = as.numeric(pv))
  } else {
    data.frame(model = id, term = names(fit$par),
               estimate = as.numeric(fit$par),
               std_error = NA_real_, t_value = NA_real_, p_value = NA_real_)
  }
}

coef_tab <- tryCatch(extract_coef(fit_best, best_id), error = function(e) {
  data.frame(model = best_id, term = NA_character_, estimate = NA_real_,
             std_error = NA_real_, t_value = NA_real_, p_value = NA_real_)
})
write_tab(coef_tab, "tab_coefficients.csv")
cat("\n== Coefficients ==\n"); print(coef_tab)

# Covariate models: coefficients and residual Ljung-Box p-values
cov_ids <- c("SARIMAX_CNY", "SARIMAX_PMI", "SARIMAX_CNY_PMI")
cov_tab <- bind_rows(lapply(cov_ids, function(id) {
  fit <- tryCatch(fit_full(model_by_id(id))$fit, error = function(e) NULL)
  if (is.null(fit)) return(NULL)
  out <- extract_coef(fit, id)
  lb <- Box.test(as.numeric(residuals(fit)), lag = 8, type = "Ljung-Box",
                 fitdf = min(length(coef(fit)), 7))
  out$LB8_p <- signif(lb$p.value, 3)
  out$AICc <- my_aicc(fit)
  out
}))
write_tab(cov_tab, "tab_covariate_models.csv")
cat("\n== Covariate models ==\n"); print(cov_tab)

# ---------------- Residual figures ----------------
p_acf <- ggAcf(res, lag.max = 24) +
  labs(title = "Residual ACF")
p_hist <- ggplot(data.frame(res = res_num), aes(x = res)) +
  geom_histogram(aes(y = after_stat(density)), bins = 20,
                 fill = "grey85", colour = "white") +
  geom_density(linewidth = 0.5) +
  labs(x = "Residual", y = "Density", title = "Residual distribution")
p_time <- ggplot(data.frame(time = as.numeric(time(res)), res = res_num),
                 aes(x = time, y = res)) +
  geom_line(linewidth = 0.45) +
  geom_hline(yintercept = 0, linetype = "dashed", colour = "grey40") +
  labs(x = "Year", y = "Residual", title = "Residuals over time")
p7 <- plot_grid(p_time, p_acf, p_hist, ncol = 3, labels = c("A", "B", "C"),
                rel_widths = c(1.2, 1, 1))
save_gg(p7, "fig7_residuals.png", 11, 3.6)
