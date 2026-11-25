# 03_cny.R -- Chinese New Year evidence: monthly ratio and quarterly share
if (!exists("ROOT")) ROOT <- normalizePath(".")
source(file.path(ROOT, "R", "01_load.R"))

pA <- ggplot(q1_share_cny, aes(x = frac_q1_before_cny, y = 100 * q1_share,
                               shape = factor(cny_month))) +
  geom_point(size = 2) +
  geom_smooth(method = "lm", se = TRUE, linewidth = 0.5, colour = "grey30") +
  scale_shape_manual(values = c(16, 17), name = "CNY month",
                     labels = c("January", "February")) +
  labs(x = "Fraction of Q1 elapsed before CNY",
       y = "Q1 share of annual sales (%)",
       title = "Quarterly total: no clear linear relation") +
  theme(legend.position = "bottom")

pB <- ggplot(mf, aes(x = factor(cny_month), y = ratio)) +
  geom_boxplot(width = 0.45, fill = "grey90", outlier.shape = NA) +
  geom_jitter(width = 0.08, height = 0, size = 1.6, alpha = 0.8) +
  scale_x_discrete(labels = c("January", "February")) +
  labs(x = "CNY month", y = "February / January sales ratio",
       title = "Monthly era, 1994-2011") +
  theme(legend.position = "none")

p4 <- plot_grid(pA, pB, ncol = 2, labels = c("A", "B"), rel_widths = c(1.25, 1))
save_gg(p4, "fig4_cny.png", 10, 4.0)

cat("\n== CNY evidence ==\n")
print(cny_tab)
cat("Pearson r =", round(cor(q1_share_cny$q1_share, q1_share_cny$frac_q1_before_cny), 4),
    " p =", signif(cor.test(q1_share_cny$q1_share, q1_share_cny$frac_q1_before_cny)$p.value, 3), "\n")
