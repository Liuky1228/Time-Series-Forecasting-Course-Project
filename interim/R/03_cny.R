if (!exists("ROOT")) ROOT <- "/Users/keyi/Desktop/STA4003/interim"
source(file.path(ROOT, "R", "01_load.R"))

cny$cny_date <- as.Date(cny$cny_date)
cny$doy      <- as.integer(format(cny$cny_date, "%j"))
leap <- function(y) (y %% 4 == 0 & y %% 100 != 0) | y %% 400 == 0
cny$q1_days  <- ifelse(leap(cny$year), 91, 90)
cny$frac_q1_before_cny <- (cny$doy - 1) / cny$q1_days

covar <- merge(share[, c("year", "q1_share")], cny[, c("year", "cny_date", "cny_month",
              "doy", "frac_q1_before_cny")], by = "year")
covar <- covar[order(covar$year), ]
write_tab(covar, "tab_cny_covariates.csv")

era <- covar[covar$year <= 2011, ]; era2 <- covar[covar$year >= 2012 & covar$year <= 2025, ]
era_all <- covar[covar$year <= 2025, ]
summ <- do.call(rbind, lapply(list(
  list("1994-2011", era), list("2012-2025", era2), list("1994-2025", era_all)), function(z) {
  d <- z[[2]]
  rbind(
    data.frame(Era = z[[1]], Group = "CNY in Jan", n = sum(d$cny_month == 1),
               Mean_Q1_share = mean(d$q1_share[d$cny_month == 1])),
    data.frame(Era = z[[1]], Group = "CNY in Feb", n = sum(d$cny_month == 2),
               Mean_Q1_share = mean(d$q1_share[d$cny_month == 2]))
  )
}))
summ$Mean_Q1_share <- round(100 * summ$Mean_Q1_share, 1)
write_tab(summ, "tab_cny_q1_share.csv")

fig4 <- ggplot(covar, aes(frac_q1_before_cny, 100 * q1_share)) +
  geom_point(aes(shape = factor(cny_month)), size = 2) +
  geom_smooth(method = "lm", se = TRUE, linewidth = 0.5) +
  scale_shape_manual(values = c(16, 17), name = "CNY month",
                     labels = c("January", "February")) +
  labs(x = "Fraction of Q1 elapsed before Chinese New Year",
       y = "Q1 share of annual retail sales (%)",
       title = "Figure 4: Q1 retail share vs. lunar new year position, 1994-2025") +
  theme(legend.position = "bottom")
save_gg(fig4, "fig4_cny_scatter.png", 7, 4.2)

mon <- read.csv(file.path(DATA, "raw", "retail_sales_monthly.csv"),
                stringsAsFactors = FALSE)
names(mon) <- trimws(names(mon))
names(mon)[1:2] <- c("yyyym", "value")
mon$yyyym <- as.integer(trimws(mon$yyyym))
mon$value <- as.numeric(trimws(mon$value))
mon$year <- mon$yyyym %/% 100; mon$m <- mon$yyyym %% 100
jan <- mon[mon$m == 1 & mon$year <= 2011, c("year", "value")]; names(jan)[2] <- "jan"
feb <- mon[mon$m == 2 & mon$year <= 2011, c("year", "value")]; names(feb)[2] <- "feb"
mf <- merge(jan, feb, by = "year")
mf <- merge(mf, cny[, c("year", "cny_month")], by = "year")
mf$ratio <- mf$feb / mf$jan
febjan <- data.frame(
  Era = "1994-2011 (monthly Jan/Feb published)",
  Group = c("CNY in Jan", "CNY in Feb"),
  n = c(sum(mf$cny_month == 1), sum(mf$cny_month == 2)),
  Mean_Feb_Jan_ratio = round(c(mean(mf$ratio[mf$cny_month == 1]),
                               mean(mf$ratio[mf$cny_month == 2])), 3)
)
write_tab(febjan, "tab_cny_febjan.csv")
cat("\n== Feb/Jan ratio (1994-2011):\n"); print(febjan)
cat("== Q1 share by CNY month:\n"); print(summ)
cat("== cor(Q1 share, frac of Q1 before CNY) =", round(cor(covar$q1_share, covar$frac_q1_before_cny), 3),
    " p =", signif(cor.test(covar$q1_share, covar$frac_q1_before_cny)$p.value, 3), "\n")
