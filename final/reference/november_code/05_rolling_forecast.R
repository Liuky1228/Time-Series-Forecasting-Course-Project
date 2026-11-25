# 05_rolling_forecast.R -- expanding-window rolling-origin evaluation, h = 1, 2
if (!exists("ROOT")) ROOT <- normalizePath(".")
source(file.path(ROOT, "R", "04_models.R"))

origins <- expand.grid(year = 2012:2025, q = 1:4)
origins <- origins[order(origins$year, origins$q), ]

records <- list()
failures <- list()
k <- 0L

for (i in seq_len(nrow(origins))) {
  oy <- origins$year[i]; oq <- origins$q[i]
  origin_t <- c(oy, oq)
  idx0 <- qidx(oy, oq)
  actual <- as.numeric(val_r)[(idx0 + 1):(idx0 + 2)]

  # Common MASE scale: seasonal-naive MAE on the full training history.
  train_val_full <- window(val_r, end = origin_t)
  mase_scale <- mean(abs(diff(train_val_full, 4)))

  for (m in MODELS) {
    fit_obj <- tryCatch(fit_one(m, origin_t), error = function(e) NULL)
    if (is.null(fit_obj)) {
      failures[[length(failures) + 1]] <- data.frame(origin = qlabel(oy, oq),
                                                     model = m$id, stage = "fit")
      next
    }
    fc_obj <- tryCatch(fc_one(m, fit_obj, origin_t, h = 2, level = c(80, 95)),
                       error = function(e) NULL)
    if (is.null(fc_obj)) {
      failures[[length(failures) + 1]] <- data.frame(origin = qlabel(oy, oq),
                                                     model = m$id, stage = "forecast")
      next
    }
    for (h in 1:2) {
      k <- k + 1L
      records[[k]] <- data.frame(
        origin_year = oy, origin_q = oq, origin = qlabel(oy, oq),
        model = m$id, label = m$label, family = m$family, h = h,
        actual = actual[h], point = fc_obj$point[h],
        error = fc_obj$point[h] - actual[h],
        mase_scale = mase_scale
      )
    }
  }
}

err <- bind_rows(records)
write_tab(err, "tab_rolling_errors.csv")

acc <- err %>%
  group_by(model, label, family, h) %>%
  summarise(n = n(),
            MAE = mean(abs(error)),
            RMSE = sqrt(mean(error^2)),
            MASE = mean(abs(error) / mase_scale),
            .groups = "drop") %>%
  arrange(h, MASE)
write_tab(acc, "tab_rolling_accuracy.csv")

acc_wide <- acc %>%
  select(model, label, family, h, MAE, RMSE, MASE) %>%
  pivot_wider(names_from = h, values_from = c(MAE, RMSE, MASE),
              names_sep = "_h") %>%
  arrange(MASE_h2)
write_tab(acc_wide, "tab_rolling_accuracy_wide.csv")

best2 <- acc %>% filter(h == 2, n >= 50) %>% arrange(MASE) %>% slice(1)
best1 <- acc %>% filter(h == 1, n >= 50) %>% arrange(MASE) %>% slice(1)
write_tab(best2, "tab_best_model.csv")
write_tab(best1, "tab_best_model_h1.csv")
cat("\nBest h=2 model:\n"); print(best2)
cat("\nBest h=1 model:\n"); print(best1)

# MASE comparison figure.  The mean benchmark is omitted from the plot because
# its MASE is an order of magnitude larger and compresses the informative range.
mean_mase <- acc %>% filter(h == 2, model == "Mean") %>% pull(MASE)
plot_dat <- acc %>% filter(h == 2, MASE < 3)
ord <- plot_dat %>% arrange(MASE) %>% pull(label)
p5 <- plot_dat %>%
  mutate(label = factor(label, levels = rev(ord))) %>%
  ggplot(aes(x = MASE, y = label, colour = family)) +
  geom_point(size = 2.2) +
  geom_vline(xintercept = 1, linetype = "dashed", colour = "grey40") +
  labs(x = "MASE (h = 2, lower is better)", y = NULL,
       title = "Rolling-origin accuracy at the two-quarter horizon",
       subtitle = sprintf("Mean benchmark (MASE = %.1f) omitted for readability", mean_mase)) +
  theme(legend.position = "bottom")
save_gg(p5, "fig5_rolling_mase.png", 7.2, 4.8)

# ---------------- Diebold-Mariano tests ----------------
dm_all <- list()
for (hh in c(1, 2)) {
  err_h <- err %>%
    filter(h == hh) %>%
    select(origin, model, error) %>%
    pivot_wider(names_from = model, values_from = error)

  best_h <- if (hh == 1) best1$model[1] else best2$model[1]
  pairs <- list(
    c("SARIMA_011_110", "SARIMA_011_011"),
    c("SARIMA_011_011", "SNaive"),
    c("SARIMAX_CNY", "SARIMA_011_011"),
    c("SARIMAX_CNY_jan", "SARIMAX_CNY"),
    c("SARIMAX_PMI", "SARIMA_011_011"),
    c("SARIMAX_CNY_PMI", "SARIMA_011_011"),
    c("ETS_AAA", "SARIMA_011_011"),
    c(best_h, "SNaive"),
    c(best_h, "SARIMA_011_011")
  )

  dm_rows <- lapply(pairs, function(pr) {
    a <- pr[1]; b <- pr[2]
    if (a == b) return(NULL)
    if (!all(c(a, b) %in% names(err_h))) return(NULL)
    d <- err_h[, c(a, b)]
    d <- d[complete.cases(d), ]
    if (nrow(d) < 10) return(NULL)
    test <- tryCatch(dm.test(d[[a]], d[[b]], h = hh, power = 2, alternative = "two.sided"),
                     error = function(e) NULL)
    if (is.null(test)) return(NULL)
    data.frame(h = hh,
               Comparison = paste(a, "vs", b),
               DM_stat = round(as.numeric(test$statistic), 3),
               p_value = signif(test$p.value, 3),
               n = nrow(d))
  })
  dm_all[[as.character(hh)]] <- bind_rows(dm_rows)
}
dm <- bind_rows(dm_all)
write_tab(dm, "tab_dm_tests.csv")
cat("\n== Diebold-Mariano tests ==\n"); print(dm)

if (length(failures) > 0) {
  fail <- bind_rows(failures)
  write_tab(fail, "tab_rolling_failures.csv")
  cat("\n== Failed fits/forecasts:", nrow(fail), "==\n")
  print(table(fail$model, fail$stage))
} else {
  write_tab(data.frame(origin = character(), model = character(), stage = character()),
            "tab_rolling_failures.csv")
  cat("\n== No failed fits/forecasts ==\n")
}
