# Supplemental retrospective evaluation; the original rolling horizons stay paired.
if (!exists("ROOT")) ROOT <- normalizePath(".")
if (!exists("MODELS")) source(file.path(ROOT, "R", "04_models.R"))
source(file.path(ROOT, "R", "09_evaluation_helpers.R"))

err <- read.csv(file.path(TABDIR, "tab_rolling_errors.csv"))
err$error <- err$point - err$actual
origin_grid <- err %>% distinct(origin, origin_idx) %>% arrange(origin_idx)
model_ids <- vapply(MODELS, `[[`, character(1), "id")
validate_rolling_panel(err, qidx(2012, 1):qidx(2025, 4), model_ids)

blend <- err %>% filter(model == INCUMBENT) %>%
  inner_join(err %>% filter(model == "SNaive") %>% select(origin_idx, h, seasonal_naive = point),
             by = c("origin_idx", "h")) %>%
  mutate(model = "Blend50_Incumbent_SNaive", label = "50:50 incumbent and seasonal naive",
         family = "Point sensitivity", point = 0.5 * point + 0.5 * seasonal_naive,
         error = point - actual, lo80 = NA_real_, hi80 = NA_real_, lo95 = NA_real_, hi95 = NA_real_) %>%
  select(-seasonal_naive)

selection_candidates <- c(INCUMBENT, "SARIMA_011_011", "SARIMA_011_101")
choices <- bind_rows(lapply(origin_grid$origin_idx, function(i) choose_sarima(err, i, selection_candidates)))
choices <- bind_cols(origin_grid, choices)
write_tab(choices, "tab_walk_forward_choices.csv")
walk <- err %>% inner_join(choices %>% select(origin_idx, model), by = c("origin_idx", "model")) %>%
  mutate(model = "WalkForward_SARIMA", label = "Chronological SARIMA selection", family = "Adaptive sensitivity")
stopifnot(nrow(blend) == nrow(origin_grid) * 2L, nrow(walk) == nrow(origin_grid) * 2L)
write_tab(bind_rows(blend, walk), "tab_supplemental_predictions.csv")

by_period <- function(d) {
  bind_rows(mutate(d, period = "All targets"),
            filter(d, target_q == 1) %>% mutate(period = "Q1 targets"),
            filter(d, target_year <= 2019) %>% mutate(period = "2012-2019"),
            filter(d, target_year >= 2020) %>% mutate(period = "2020-2026Q2"),
            filter(d, between(target_year, 2020, 2022)) %>% mutate(period = "2020-2022"),
            filter(d, target_year >= 2023) %>% mutate(period = "2023-2026Q2"),
            filter(d, target %in% covid_targets) %>% mutate(period = "COVID target"),
            filter(d, !target %in% covid_targets) %>% mutate(period = "Non-COVID target"))
}

err_all <- bind_rows(err, blend, walk)
accuracy <- point_accuracy(by_period(err_all), period, model, label, family, h) %>%
  arrange(period, h, MASE)
write_tab(accuracy, "tab_optimization_accuracy.csv")
cat("\n== Supplemental point metrics, all origins and Q1 ==\n")
print(filter(accuracy, period %in% c("All targets", "Q1 targets"),
             model %in% c(INCUMBENT, "SARIMA_011_101", "SARIMA_011_011_2005Q3",
                          "SARIMAX_CNY_2005Q3", "Blend50_Incumbent_SNaive", "WalkForward_SARIMA")),
      n = Inf, width = Inf)

interval_predictions <- bind_rows(err, walk)
interval_scores <- bind_rows(lapply(c(80L, 95L), function(level) {
  lower <- interval_predictions[[paste0("lo", level)]]
  upper <- interval_predictions[[paste0("hi", level)]]
  d <- interval_predictions %>%
    select(origin, target, target_year, target_q, model, h, actual) %>%
    mutate(level = level, lower = lower, upper = upper)
  bind_cols(d, score_interval(d$actual, d$lower, d$upper, level))
}))
int_summary <- by_period(interval_scores) %>%
  group_by(period, model, h, level) %>%
  summarise(n = n(), covered = sum(covered), coverage = covered / n,
            width = mean(width), Winkler = mean(Winkler), .groups = "drop")
write_tab(int_summary, "tab_interval_accuracy.csv")
write_tab(filter(interval_scores, !covered), "tab_interval_misses.csv")

# Rows are always candidate minus control, so lower losses give negative differences.
pairs <- data.frame(
  comparison = c("D0 vs incumbent", "Long-window CNY effect", "Long-window CNY January indicator effect",
                 "2005Q3 CNY effect", "2005Q3 PMI effect", "2005Q3 PMI incremental to CNY",
                 "2005Q3 CNY incremental to PMI", "No-xreg training window effect", "CNY training window effect",
                 "Equal-weight blend vs incumbent", "Chronological rule vs incumbent"),
  candidate = c("SARIMA_011_101", "SARIMAX_CNY", "SARIMAX_CNY_jan", "SARIMAX_CNY_2005Q3",
                "SARIMAX_PMI", "SARIMAX_CNY_PMI", "SARIMAX_CNY_PMI", "SARIMA_011_011_2005Q3",
                "SARIMAX_CNY_2005Q3", "Blend50_Incumbent_SNaive", "WalkForward_SARIMA"),
  control = c(INCUMBENT, "SARIMA_011_011", "SARIMA_011_011", "SARIMA_011_011_2005Q3",
              "SARIMA_011_011_2005Q3", "SARIMAX_CNY_2005Q3", "SARIMAX_PMI", "SARIMA_011_011",
              "SARIMAX_CNY", INCUMBENT, INCUMBENT)
)

paired <- bind_rows(lapply(seq_len(nrow(pairs)), function(i) {
  pair <- pairs[i, ]
  left <- err_all %>% filter(model == pair$candidate) %>%
    select(origin, origin_idx, target, target_year, target_q, h, actual, mase_scale,
           candidate_point = point, candidate_error = error)
  right <- err_all %>% filter(model == pair$control) %>% select(origin_idx, h, control_point = point, control_error = error)
  d <- inner_join(left, right, by = c("origin_idx", "h"), relationship = "one-to-one")
  stopifnot(nrow(d) == nrow(origin_grid) * 2L)
  d %>% mutate(comparison = pair$comparison, candidate = pair$candidate, control = pair$control,
               delta_abs = abs(candidate_error) - abs(control_error),
               delta_sq = candidate_error^2 - control_error^2, delta_scaled_abs = delta_abs / mase_scale,
               .before = 1)
}))
write_tab(paired, "tab_paired_losses.csv")
paired_summary <- by_period(paired) %>%
  group_by(period, comparison, candidate, control, h) %>%
  summarise(n = n(), wins = sum(delta_abs < 0), ties = sum(delta_abs == 0),
            delta_MAE = mean(delta_abs),
            delta_RMSE = sqrt(mean(candidate_error^2)) - sqrt(mean(control_error^2)),
            delta_MASE = mean(delta_scaled_abs), .groups = "drop")
write_tab(paired_summary, "tab_paired_summary.csv")

# The original archive contains point predictions but no rolling interval bounds.
archive_err <- read.csv(file.path(ROOT, "reference", "november_tables", "tab_rolling_errors.csv"))
rerun_err <- err %>% filter(model %in% ORIGINAL_MODEL_IDS)
rec <- inner_join(archive_err %>% select(origin, model, h, actual, mase_scale, archived_point = point),
                  rerun_err %>% select(origin, model, h, target, rerun_actual = actual,
                                      rerun_scale = mase_scale, rerun_point = point, fit_status),
                  by = c("origin", "model", "h"), relationship = "one-to-one")
stopifnot(nrow(rec) == 14L * 56L * 2L, nrow(rec) == nrow(archive_err), nrow(rec) == nrow(rerun_err),
          identical(rec$actual, rec$rerun_actual),
          isTRUE(all.equal(rec$mase_scale, rec$rerun_scale, tolerance = 1e-12)))
rec <- rec %>% select(-rerun_actual, -rerun_scale) %>%
  mutate(delta_point = rerun_point - archived_point,
         archived_scaled_abs = abs(archived_point - actual) / mase_scale,
         rerun_scaled_abs = abs(rerun_point - actual) / mase_scale)
write_tab(rec, "tab_archive_reconciliation_detail.csv")
rec_summary <- rec %>% group_by(model, h) %>%
  summarise(n = n(), mean_abs_delta = mean(abs(delta_point)), max_abs_delta = max(abs(delta_point)),
            archived_MASE = mean(archived_scaled_abs), rerun_MASE = mean(rerun_scaled_abs),
            delta_MASE = rerun_MASE - archived_MASE, .groups = "drop")
write_tab(rec_summary, "tab_archive_reconciliation.csv")
