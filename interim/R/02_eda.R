if (!exists("ROOT")) ROOT <- "/Users/keyi/Desktop/STA4003/interim"
source(file.path(ROOT, "R", "01_load.R"))

fig1 <- ggplot(retail, aes(time, log_value)) +
  geom_line(linewidth = 0.6) +
  geom_point(size = 0.7) +
  annotate("rect", xmin = 2020.00, xmax = 2020.25, ymin = min(retail$log_value) - 0.1,
           ymax = max(retail$log_value) + 0.1, alpha = 0.12, fill = "red") +
  annotate("rect", xmin = 2022.25, xmax = 2022.50, ymin = min(retail$log_value) - 0.1,
           ymax = max(retail$log_value) + 0.1, alpha = 0.12, fill = "orange") +
  annotate("text", x = 2020.1, y = max(retail$log_value) + 0.35, label = "2020Q1\n(-19.6% y/y)",
           size = 3.0, hjust = 0) +
  annotate("text", x = 2022.35, y = min(retail$log_value) - 0.45, label = "2022Q2", size = 3.0) +
  scale_x_continuous(breaks = seq(1994, 2026, 4)) +
  labs(x = "Year", y = "log(retail sales, 100 million CNY)",
       title = "Figure 1: Log quarterly retail sales, 1994Q1-2026Q2 (N = 130)")
save_gg(fig1, "fig1_log_ts.png", 7, 4.0)

fig2 <- ggplot(retail, aes(factor(q), log_value)) +
  geom_boxplot(fill = "grey80", outlier.size = 0.8) +
  labs(x = "Quarter", y = "log(retail sales, 100 million CNY)",
       title = "Figure 2: Seasonal distribution of log retail sales by quarter")
save_gg(fig2, "fig2_seasonal_boxplot.png", 6, 4.0)

fig3 <- ggAcf(log_r, lag.max = 40) +
  labs(title = "Figure 3: ACF of log retail sales (levels)")
save_gg(fig3, "fig3_acf_levels.png", 7, 3.8)

fig6 <- ggPacf(log_r, lag.max = 40) +
  labs(title = "Appendix Figure A1: PACF of log retail sales (levels)")
save_gg(fig6, "figA1_pacf_levels.png", 7, 3.8)

cat("\n== EDA summary stats\n")
print(summary(retail$log_value))
cat("Q4 share of year (mean over complete years):\n")
tmp <- merge(aggregate(value_bn ~ year + q, retail, sum), annual, by = "year")
print(round(tapply(tmp$value_bn / tmp$annual_bn, tmp$q, mean), 4))
