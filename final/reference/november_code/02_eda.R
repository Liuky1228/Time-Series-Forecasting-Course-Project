# 02_eda.R -- exploratory plots
if (!exists("ROOT")) ROOT <- normalizePath(".")
source(file.path(ROOT, "R", "01_load.R"))

covid <- data.frame(
  xmin = c(2020.00, 2022.25),
  xmax = c(2020.25, 2022.50),
  label = c("2020Q1", "2022Q2")
)

p1 <- ggplot(retail, aes(time, log_value)) +
  geom_rect(data = covid, inherit.aes = FALSE,
            aes(xmin = xmin, xmax = xmax, ymin = -Inf, ymax = Inf),
            fill = "red", alpha = 0.08) +
  geom_line(linewidth = 0.6) +
  geom_point(size = 0.7) +
  annotate("text", x = 2020.05, y = max(retail$log_value) + 0.35,
           label = "2020Q1\n(-19.6% y/y)", size = 3, hjust = 0) +
  annotate("text", x = 2022.30, y = min(retail$log_value) - 0.45,
           label = "2022Q2", size = 3) +
  scale_x_continuous(breaks = seq(1994, 2026, 4)) +
  labs(x = "Year", y = "log(retail sales, 100 million CNY)",
       title = "Log quarterly retail sales, 1994Q1-2026Q2 (N = 130)")
save_gg(p1, "fig1_series.png", 7, 4.0)

p2 <- ggplot(retail, aes(factor(q), log_value)) +
  geom_boxplot(fill = "grey85", outlier.size = 0.8) +
  labs(x = "Quarter", y = "log(retail sales, 100 million CNY)",
       title = "Seasonal distribution of log retail sales")
save_gg(p2, "fig2_seasonal.png", 5.5, 4.0)

p12 <- plot_grid(p1, p2, ncol = 2, labels = c("A", "B"),
                 rel_widths = c(1.55, 1))
save_gg(p12, "fig1_eda.png", 10, 4.0)

p3a <- ggAcf(log_r, lag.max = 40) +
  labs(title = "ACF: log levels")
p3b <- ggAcf(diff(diff(log_r, 1), 4), lag.max = 40) +
  labs(title = "ACF: after d = 1, D = 1")
p3 <- plot_grid(p3a, p3b, ncol = 2, labels = c("A", "B"), rel_widths = c(1, 1))
save_gg(p3, "fig3_acf.png", 9.5, 3.8)

pA2 <- ggAcf(diff(log_r, 1), lag.max = 40) +
  labs(title = "ACF: after first differencing only (d = 1, D = 0)")
save_gg(pA2, "figA2_acf_first_diff.png", 7, 3.8)

cat("\n== EDA summary ==\n")
print(summary(retail$log_value))
cat("Mean quarterly share of annual sales:\n")
print(season_tab[, c("q", "Mean_Share_Pct", "Peak_Count", "Trough_Count")])
