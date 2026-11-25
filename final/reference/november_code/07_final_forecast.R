# 07_final_forecast.R -- final two-quarter forecast and longer-run fan chart
if (!exists("ROOT")) ROOT <- normalizePath(".")
source(file.path(ROOT, "R", "04_models.R"))

best <- read.csv(file.path(TABDIR, "tab_best_model.csv"), stringsAsFactors = FALSE)
best_id <- best$model[1]
best_m <- model_by_id(best_id)
cat("Final model:", best_id, "\n")

fit_best <- fit_full(best_m)
h_report <- 2
fc_best <- fc_one(best_m, fit_best, origin = c(2026, 2), h = h_report, level = c(80, 95))

# Only the first two quarters are genuine two-step-ahead forecasts.  For the
# PMI model, h > 2 would require forecasting the PMI itself.
qout <- c("2026Q3", "2026Q4")

final_tab <- data.frame(
  quarter = qout,
  model = best_id,
  point = fc_best$point[1:h_report],
  lo80 = fc_best$lower[1:h_report, 1],
  hi80 = fc_best$upper[1:h_report, 1],
  lo95 = fc_best$lower[1:h_report, 2],
  hi95 = fc_best$upper[1:h_report, 2],
  point_trillion = fc_best$point[1:h_report] / 1e4,
  lo80_trillion = fc_best$lower[1:h_report, 1] / 1e4,
  hi80_trillion = fc_best$upper[1:h_report, 1] / 1e4,
  lo95_trillion = fc_best$lower[1:h_report, 2] / 1e4,
  hi95_trillion = fc_best$upper[1:h_report, 2] / 1e4
)
write_tab(final_tab, "tab_final_forecast.csv")
cat("\n== Final forecast ==\n"); print(final_tab)

# ---------------- Longer-run illustration ----------------
# The selected model can be extrapolated further only if its regressors are
# known in advance.  CNY is a calendar variable; PMI is not, so a PMI model is
# shown only for h = 1, 2.
can_long <- is.null(best_m$xreg) || all(best_m$xreg %in% c("cny_q1_frac", "cny_jan"))
m_long <- if (can_long) best_m else model_by_id("SARIMA_011_011")
fit_long <- fit_full(m_long)
fc_long <- fc_one(m_long, fit_long, origin = c(2026, 2), h = 8, level = c(80, 95))

long_tab <- data.frame(
  quarter = paste0(2026 + (2:9) %/% 4, "Q", ((2:9) %% 4) + 1),
  point = fc_long$point,
  lo80 = fc_long$lower[, 1], hi80 = fc_long$upper[, 1],
  lo95 = fc_long$lower[, 2], hi95 = fc_long$upper[, 2]
)
# fix quarter labels: 2026Q3 ... 2028Q2
long_tab$quarter <- c("2026Q3", "2026Q4", "2027Q1", "2027Q2",
                      "2027Q3", "2027Q4", "2028Q1", "2028Q2")
write_tab(long_tab, "tab_final_forecast_long.csv")

hist_df <- data.frame(
  time = retail$time[retail$year >= 2015],
  value = retail$value_bn[retail$year >= 2015]
)
fc_df <- data.frame(
  time = 2026.5 + (0:7) / 4,
  point = long_tab$point,
  lo80 = long_tab$lo80, hi80 = long_tab$hi80,
  lo95 = long_tab$lo95, hi95 = long_tab$hi95
)

p6 <- ggplot() +
  geom_ribbon(data = fc_df, aes(x = time, ymin = lo95, ymax = hi95, fill = "95%"),
              alpha = 0.18) +
  geom_ribbon(data = fc_df, aes(x = time, ymin = lo80, ymax = hi80, fill = "80%"),
              alpha = 0.28) +
  geom_line(data = hist_df, aes(x = time, y = value), linewidth = 0.65) +
  geom_line(data = fc_df, aes(x = time, y = point), linewidth = 0.7, linetype = "dashed") +
  geom_vline(xintercept = 2026.25, linetype = "dotted", colour = "grey30") +
  scale_fill_manual(values = c("80%" = "steelblue", "95%" = "steelblue"),
                    name = "Interval") +
  scale_y_continuous(labels = label_comma()) +
  labs(x = "Year", y = "Retail sales (100 million CNY)",
       title = paste0("Forecast from ", m_long$label, ", origin 2026Q2")) +
  theme(legend.position = "bottom")
save_gg(p6, "fig6_fanchart.png", 7.2, 4.2)
