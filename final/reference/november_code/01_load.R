# 01_load.R -- load data, build quarterly series and calendar covariates
if (!exists("ROOT")) ROOT <- normalizePath(".")
source(file.path(ROOT, "R", "00_setup.R"))

retail <- read.csv(file.path(DATA, "processed", "retail_quarterly.csv"),
                   stringsAsFactors = FALSE)
pmi    <- read.csv(file.path(DATA, "processed", "pmi_quarterly.csv"),
                   stringsAsFactors = FALSE)
cny    <- read.csv(file.path(DATA, "meta", "lunar_new_year.csv"),
                   stringsAsFactors = FALSE)

names(retail) <- trimws(names(retail))
names(pmi)    <- trimws(names(pmi))
names(cny)    <- trimws(names(cny))

stopifnot(!anyDuplicated(retail$quarter), !anyNA(retail$value_bn), !anyNA(retail$log_value))
stopifnot(!anyDuplicated(pmi$quarter), !anyNA(pmi$pmi))
stopifnot(nrow(retail) == 130, retail$quarter[1] == "1994Q1",
          retail$quarter[nrow(retail)] == "2026Q2")
stopifnot(nrow(pmi) == 86, pmi$quarter[1] == "2005Q1", pmi$quarter[nrow(pmi)] == "2026Q2")

retail$year <- as.integer(substr(retail$quarter, 1, 4))
retail$q    <- as.integer(substr(retail$quarter, 6, 6))
retail$time <- retail$year + (retail$q - 1) / 4

pmi$year <- as.integer(substr(pmi$quarter, 1, 4))
pmi$q    <- as.integer(substr(pmi$quarter, 6, 6))

log_r <- ts(retail$log_value, start = c(1994, 1), frequency = 4)
val_r <- ts(retail$value_bn,  start = c(1994, 1), frequency = 4)
pmi_ts <- ts(pmi$pmi,        start = c(2005, 1), frequency = 4)

# ---------------- Chinese New Year calendar covariates ----------------
cny$cny_date <- as.Date(cny$cny_date)
cny$doy      <- as.integer(format(cny$cny_date, "%j"))
leap <- function(y) (y %% 4 == 0 & y %% 100 != 0) | y %% 400 == 0
cny$q1_days  <- ifelse(leap(cny$year), 91, 90)
cny$frac_q1_before_cny <- (cny$doy - 1) / cny$q1_days

cny_q1_frac <- numeric(nrow(retail))
cny_jan     <- numeric(nrow(retail))
for (i in seq_len(nrow(retail))) {
  if (retail$q[i] == 1) {
    j <- match(retail$year[i], cny$year)
    cny_q1_frac[i] <- cny$frac_q1_before_cny[j]
    cny_jan[i]     <- as.integer(cny$cny_month[j] == 1)
  }
}

# PMI enters with a two-quarter lag so that h = 2 forecasts use only values
# known at the forecast origin.  pmi_lag2[t] = PMI in quarter t-2.
pmi_vec <- as.numeric(pmi_ts)
pmi_lag1 <- pmi_lag2 <- rep(NA_real_, nrow(retail))
for (i in seq_len(nrow(retail))) {
  # quarter index on the PMI calendar (2005Q1 = 1)
  idx <- (retail$year[i] - 2005) * 4 + retail$q[i]
  if (idx - 2 >= 1 && idx - 2 <= length(pmi_vec)) pmi_lag2[i] <- pmi_vec[idx - 2]
  if (idx - 1 >= 1 && idx - 1 <= length(pmi_vec)) pmi_lag1[i] <- pmi_vec[idx - 1]
}

X_all <- ts(cbind(cny_q1_frac = cny_q1_frac,
                  cny_jan     = cny_jan,
                  pmi_lag1    = pmi_lag1,
                  pmi_lag2    = pmi_lag2),
            start = c(1994, 1), frequency = 4)

# First quarter with a valid two-quarter PMI lag
start_pmi <- c(2005, 3)

# ---------------- Annual totals, seasonal shares, CNY evidence ----------------
qcnt <- table(retail$year)
complete_y <- as.integer(names(qcnt)[qcnt == 4])

annual <- aggregate(value_bn ~ year, retail[retail$year %in% complete_y, ], sum)
names(annual)[2] <- "annual_bn"

share <- merge(retail[retail$q == 1, c("year", "value_bn")], annual, by = "year")
names(share)[2] <- "q1_bn"
share$q1_share <- share$q1_bn / share$annual_bn
share <- share[order(share$year), ]

qshare <- merge(aggregate(value_bn ~ year + q, retail, sum), annual, by = "year")
qshare$share <- qshare$value_bn / qshare$annual_bn
season_tab <- aggregate(share ~ q, qshare, mean)
names(season_tab)[2] <- "Mean_Share"
season_tab$Mean_Share_Pct <- round(100 * season_tab$Mean_Share, 1)

peak <- trough <- integer(4)
for (y in complete_y) {
  b <- retail[retail$year == y, ]
  b <- b[order(b$q), ]
  pq <- b$q[which.max(b$value_bn)]
  tq <- b$q[which.min(b$value_bn)]
  peak[pq]   <- peak[pq] + 1L
  trough[tq] <- trough[tq] + 1L
}
season_tab$Peak_Count   <- peak[season_tab$q]
season_tab$Trough_Count <- trough[season_tab$q]
write_tab(season_tab, "tab_seasonality.csv")

# CNY evidence: monthly Feb/Jan ratio (1994-2011) and Q1 share by era
mon <- read.csv(file.path(DATA, "raw", "retail_sales_monthly.csv"),
                stringsAsFactors = FALSE, strip.white = TRUE, check.names = FALSE)
names(mon) <- trimws(names(mon))
names(mon)[1:2] <- c("yyyymm", "value")
mon$yyyymm <- as.integer(trimws(mon$yyyymm))
mon$value  <- as.numeric(trimws(mon$value))
mon$year <- mon$yyyymm %/% 100
mon$m    <- mon$yyyymm %% 100

jan <- mon[mon$m == 1 & mon$year <= 2011, c("year", "value")]
names(jan)[2] <- "jan"
feb <- mon[mon$m == 2 & mon$year <= 2011, c("year", "value")]
names(feb)[2] <- "feb"
mf <- merge(merge(jan, feb, by = "year"), cny[, c("year", "cny_month")], by = "year")
mf$ratio <- mf$feb / mf$jan

q1_share_cny <- merge(share[, c("year", "q1_share")],
                      cny[, c("year", "cny_date", "cny_month", "doy", "frac_q1_before_cny")],
                      by = "year")

era_rows <- list(
  list(era = "1994-2011", years = 1994:2011, monthly = TRUE),
  list(era = "2012-2025", years = 2012:2025, monthly = FALSE),
  list(era = "1994-2025", years = 1994:2025, monthly = FALSE)
)
cny_tab <- do.call(rbind, lapply(era_rows, function(z) {
  d  <- q1_share_cny[q1_share_cny$year %in% z$years, ]
  m  <- mf[mf$year %in% z$years, ]
  do.call(rbind, lapply(c(1, 2), function(mm) {
    lab <- if (mm == 1) "CNY in Jan" else "CNY in Feb"
    dd  <- d[d$cny_month == mm, ]
    mmf <- m[m$cny_month == mm, ]
    data.frame(Era = z$era, Group = lab, n = nrow(dd),
               Mean_Feb_Jan = if (z$monthly && nrow(mmf) > 0) round(mean(mmf$ratio), 3) else NA_real_,
               Mean_Q1_Share = round(100 * mean(dd$q1_share), 1))
  }))
}))
cny_tab$Era   <- factor(cny_tab$Era, levels = c("1994-2011", "2012-2025", "1994-2025"))
cny_tab$Group <- factor(cny_tab$Group, levels = c("CNY in Jan", "CNY in Feb"))
cny_tab <- cny_tab[order(cny_tab$Era, cny_tab$Group), ]
cny_tab$Era <- as.character(cny_tab$Era); cny_tab$Group <- as.character(cny_tab$Group)
write_tab(cny_tab, "tab_cny_evidence.csv")
write_tab(q1_share_cny[order(q1_share_cny$year), ], "tab_cny_covariates.csv")

# Data summary table
tab1 <- data.frame(
  Item = c("Primary series", "Frequency", "Sample span", "Observations",
           "Complete seasonal cycles", "Range (100 million CNY)", "Auxiliary series",
           "Auxiliary span", "Missing values", "Duplicates"),
  Value = c("Total retail sales of consumer goods, China (NBS)",
            "Quarterly (built from official monthly releases)",
            paste0(retail$quarter[1], " to ", retail$quarter[nrow(retail)]),
            nrow(retail), nrow(retail) / 4,
            sprintf("%.1f - %.1f (log %.2f - %.2f)",
                    min(retail$value_bn), max(retail$value_bn),
                    min(retail$log_value), max(retail$log_value)),
            "Manufacturing PMI, quarterly mean",
            paste0(pmi$quarter[1], " to ", pmi$quarter[nrow(pmi)]),
            "0 in quarterly series (Jan-Feb combined since 2012 handled at construction)",
            "0")
)
write_tab(tab1, "tab_data_summary.csv")

cat("\n== retail:", nrow(retail), "obs |", retail$quarter[1], "-", retail$quarter[nrow(retail)], "\n")
cat("== pmi:", nrow(pmi), "obs |", pmi$quarter[1], "-", pmi$quarter[nrow(pmi)], "\n")
cat("== PMI-lag models start at", paste(start_pmi, collapse = "Q"), "\n")
cat("== CNY r =", round(cor(q1_share_cny$q1_share, q1_share_cny$frac_q1_before_cny), 4),
    " p =", signif(cor.test(q1_share_cny$q1_share, q1_share_cny$frac_q1_before_cny)$p.value, 3), "\n")
