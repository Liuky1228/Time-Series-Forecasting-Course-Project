# 08_robustness.R -- accuracy with and without COVID-affected target quarters
if (!exists("ROOT")) ROOT <- normalizePath(".")
source(file.path(ROOT, "R", "00_setup.R"))

err <- read.csv(file.path(TABDIR, "tab_rolling_errors.csv"), stringsAsFactors = FALSE)

err$target_year <- NA_integer_
err$target_q <- NA_integer_
for (i in seq_len(nrow(err))) {
  tt <- qtime(qidx(err$origin_year[i], err$origin_q[i]) + err$h[i])
  err$target_year[i] <- tt[1]
  err$target_q[i] <- tt[2]
}
err$target <- paste0(err$target_year, "Q", err$target_q)

covid_targets <- c("2020Q1", "2020Q2", "2022Q2")
err$scenario <- ifelse(err$target %in% covid_targets, "COVID target", "Non-COVID target")

rob <- err %>%
  group_by(scenario, model, family, h) %>%
  summarise(n = n(),
            MAE = mean(abs(error)),
            RMSE = sqrt(mean(error^2)),
            MASE = mean(abs(error) / mase_scale),
            .groups = "drop") %>%
  arrange(h, model, scenario)

# Add baseline (all targets) rows
base <- err %>%
  mutate(scenario = "All targets") %>%
  group_by(scenario, model, family, h) %>%
  summarise(n = n(),
            MAE = mean(abs(error)),
            RMSE = sqrt(mean(error^2)),
            MASE = mean(abs(error) / mase_scale),
            .groups = "drop")

rob <- bind_rows(base, rob) %>%
  arrange(h, model, factor(scenario, levels = c("All targets", "Non-COVID target", "COVID target")))
write_tab(rob, "tab_robustness.csv")

# Compact comparison for h = 2: all targets vs excluding COVID targets
cmp <- rob %>%
  filter(h == 2, scenario %in% c("All targets", "Non-COVID target")) %>%
  select(model, scenario, MASE) %>%
  pivot_wider(names_from = scenario, values_from = MASE) %>%
  arrange(`Non-COVID target`)
write_tab(cmp, "tab_robustness_h2.csv")
cat("\n== Robustness, h = 2 ==\n"); print(cmp)

p8 <- rob %>%
  filter(h == 2, scenario %in% c("All targets", "Non-COVID target")) %>%
  mutate(model = factor(model, levels = rev(cmp$model))) %>%
  ggplot(aes(x = MASE, y = model, colour = scenario, shape = scenario)) +
  geom_point(size = 2.2, position = position_dodge(width = 0.5)) +
  geom_vline(xintercept = 1, linetype = "dashed", colour = "grey40") +
  labs(x = "MASE (h = 2)", y = NULL, colour = NULL, shape = NULL,
       title = "Sensitivity to COVID-affected target quarters") +
  theme(legend.position = "bottom")
save_gg(p8, "fig8_robustness.png", 7.2, 4.4)
