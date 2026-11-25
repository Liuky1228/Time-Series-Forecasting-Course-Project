# 07_final_forecast.R -- final two-quarter forecast and longer-run fan chart
if (!exists("ROOT")) ROOT <- normalizePath(".")
source(file.path(ROOT, "R", "04_models.R"))

incumbent <- model_by_id(INCUMBENT)
origin <- c(2026, 2)
origin_label <- "2026Q2"
archive_path <- file.path(ROOT, "reference", "november_tables")
archive_final <- read.csv(file.path(archive_path, "tab_final_forecast.csv"))
archive_long <- read.csv(file.path(archive_path, "tab_final_forecast_long.csv"))
forecast_cols <- c("point", "lo80", "hi80", "lo95", "hi95")
future_quarters <- vapply(qidx(origin[1], origin[2]) + 1:8, function(i) {
  t <- qtime(i)
  qlabel(t[1], t[2])
}, character(1))
stopifnot(identical(archive_long$quarter, future_quarters),
          identical(archive_final$quarter, future_quarters[1:2]),
          all(archive_final$model == INCUMBENT),
          all(is.finite(as.matrix(archive_long[forecast_cols]))),
          isTRUE(all.equal(archive_final[forecast_cols], archive_long[1:2, forecast_cols])))

fit_incumbent <- if (exists("full_fits")) full_fits[[INCUMBENT]] else fit_full(incumbent)
rerun <- capture_model_step(fc_one(incumbent, fit_incumbent, origin, h = 8, level = c(80, 95)),
                            origin_label, INCUMBENT, "forecast")
write_tab(rerun$events, "tab_final_forecast_events.csv")
if (!is.null(rerun$error)) stop(rerun$error)

fc <- rerun$value
rerun_long <- data.frame(quarter = future_quarters, point = fc$point,
                         lo80 = fc$lower[, 1], hi80 = fc$upper[, 1],
                         lo95 = fc$lower[, 2], hi95 = fc$upper[, 2])
stopifnot(all(is.finite(as.matrix(rerun_long[forecast_cols]))),
          with(rerun_long, all(lo95 <= lo80 & lo80 <= hi80 & hi80 <= hi95)))
rerun_final <- data.frame(quarter = future_quarters[1:2], model = INCUMBENT,
                          rerun_long[1:2, forecast_cols])
for (field in forecast_cols) rerun_final[[paste0(field, "_trillion")]] <- rerun_final[[field]] / 1e4
archive_final <- mutate(archive_final, origin = origin_label, status = "archived primary")
archive_long <- mutate(archive_long, origin = origin_label, status = "archived illustration")
rerun_final <- mutate(rerun_final, origin = origin_label, status = "clean R rerun", fit_status = fit_incumbent$status)
rerun_long <- mutate(rerun_long, origin = origin_label, status = "clean R rerun", fit_status = fit_incumbent$status)
write_tab(archive_final, "tab_final_forecast.csv")
write_tab(archive_long, "tab_final_forecast_long.csv")
write_tab(rerun_final, "tab_final_forecast_rerun.csv")
write_tab(rerun_long, "tab_final_forecast_long_rerun.csv")

final_reconciliation <- archive_final %>%
  select(quarter, all_of(forecast_cols)) %>%
  pivot_longer(all_of(forecast_cols), names_to = "quantity", values_to = "archived") %>%
  inner_join(rerun_final %>% select(quarter, all_of(forecast_cols)) %>%
               pivot_longer(all_of(forecast_cols), names_to = "quantity", values_to = "rerun"),
             by = c("quarter", "quantity")) %>%
  mutate(delta = rerun - archived,
         same_at_0.01_trillion = round(rerun / 1e4, 2) == round(archived / 1e4, 2))
write_tab(final_reconciliation, "tab_final_forecast_reconciliation.csv")
cat("\n== Archived primary forecast and clean rerun deltas ==\n"); print(final_reconciliation)

hist_df <- data.frame(
  time = retail$time[retail$year >= 2015],
  value = retail$value_bn[retail$year >= 2015]
)
fc_df <- data.frame(
  time = 2026.5 + (0:7) / 4,
  point = archive_long$point,
  lo80 = archive_long$lo80, hi80 = archive_long$hi80,
  lo95 = archive_long$lo95, hi95 = archive_long$hi95
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
       title = paste0("Archived forecast from ", incumbent$label, ", origin 2026Q2")) +
  theme(legend.position = "bottom")
save_gg(p6, "fig6_fanchart.png", 7.2, 4.2)
