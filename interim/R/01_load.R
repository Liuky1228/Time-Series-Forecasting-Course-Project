if (!exists("ROOT")) ROOT <- "/Users/keyi/Desktop/STA4003/interim"
source(file.path(ROOT, "R", "00_setup.R"))

retail <- read.csv(file.path(DATA, "processed", "retail_quarterly.csv"),
                   stringsAsFactors = FALSE)
pmi    <- read.csv(file.path(DATA, "processed", "pmi_quarterly.csv"),
                   stringsAsFactors = FALSE)
cny    <- read.csv(file.path(DATA, "meta", "lunar_new_year.csv"),
                   stringsAsFactors = FALSE)

stopifnot(!anyDuplicated(retail$quarter), !anyNA(retail$value_bn), !anyNA(retail$log_value))
stopifnot(!anyDuplicated(pmi$quarter), !anyNA(pmi$pmi))
stopifnot(nrow(retail) == 130, retail$quarter[1] == "1994Q1",
          retail$quarter[nrow(retail)] == "2026Q2")
stopifnot(nrow(pmi) == 86)

retail$year <- as.integer(substr(retail$quarter, 1, 4))
retail$q    <- as.integer(substr(retail$quarter, 6, 6))
retail$time <- retail$year + (retail$q - 1) / 4
pmi$year    <- as.integer(substr(pmi$quarter, 1, 4))
pmi$q       <- as.integer(substr(pmi$quarter, 6, 6))

log_r  <- ts(retail$log_value, start = c(1994, 1), frequency = 4)
val_r  <- ts(retail$value_bn,  start = c(1994, 1), frequency = 4)
pmi_ts <- ts(pmi$pmi,         start = c(2005, 1), frequency = 4)

qcnt <- table(retail$year)
complete_y <- as.integer(names(qcnt)[qcnt == 4])
annual <- aggregate(value_bn ~ year, retail[retail$year %in% complete_y, ], sum)
names(annual)[2] <- "annual_bn"
share <- merge(retail[retail$q == 1, c("year", "value_bn")], annual, by = "year")
names(share)[2] <- "q1_bn"
share$q1_share <- share$q1_bn / share$annual_bn

tab1 <- data.frame(
  Item = c("Primary series", "Frequency", "Sample span", "Observations",
           "Seasonal cycles", "Range (100 million CNY)", "Auxiliary series",
           "Auxiliary span", "Missing values", "Duplicates"),
  Value = c("Total retail sales of consumer goods, China (NBS)",
            "Quarterly (built from official monthly releases)",
            paste0(retail$quarter[1], " to ", retail$quarter[nrow(retail)]),
            nrow(retail),
            nrow(retail) / 4,
            sprintf("%.1f - %.1f (log %.2f - %.2f)",
                    min(retail$value_bn), max(retail$value_bn),
                    min(retail$log_value), max(retail$log_value)),
            "Manufacturing PMI, quarterly mean",
            paste0(pmi$quarter[1], " to ", pmi$quarter[nrow(pmi)]),
            "0 in quarterly series (30 unseparated Jan-Feb months since 2012 handled at construction)",
            "0")
)
write_tab(tab1, "tab_data_summary.csv")

cat("\n== retail:", nrow(retail), "obs |", retail$quarter[1], "-", retail$quarter[nrow(retail)], "\n")
cat("== pmi:", nrow(pmi), "obs |", pmi$quarter[1], "-", pmi$quarter[nrow(pmi)], "\n")
