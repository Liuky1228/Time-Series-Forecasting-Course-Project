if (!exists("ROOT")) ROOT <- "/Users/keyi/Desktop/STA4003/interim"
source(file.path(ROOT, "R", "01_load.R"))

H <- 8
n <- length(val_r)
train_o <- window(val_r, end = c(2024, 2))
test_o  <- window(val_r, start = c(2024, 3))
train_l <- window(log_r, end = c(2024, 2))
stopifnot(length(test_o) == H, length(train_o) == n - H)

mase_scale <- mean(abs(diff(train_o, 4)))
score <- function(fc_o) {
  e <- as.numeric(fc_o) - as.numeric(test_o)
  data.frame(MAE = mean(abs(e)), RMSE = sqrt(mean(e^2)),
             MASE = mean(abs(e)) / mase_scale)
}

fc <- list(
  Mean  = exp(meanf(train_l, h = H)$mean),
  Naive = exp(naive(train_l, h = H)$mean),
  SNaive = exp(snaive(train_l, h = H)$mean)
)

fit_arima <- auto.arima(train_l, seasonal = TRUE, stepwise = FALSE, approximation = FALSE)
fc$ARIMA <- exp(forecast(fit_arima, h = H)$mean)

met <- do.call(rbind, lapply(names(fc), function(nm) {
  data.frame(Model = nm, score(fc[[nm]]))
}))
met$MAE <- round(met$MAE, 1); met$RMSE <- round(met$RMSE, 1); met$MASE <- round(met$MASE, 3)
met <- met[order(met$MAE), ]
write_tab(met, "tab_model_metrics.csv")

lb <- Box.test(residuals(fit_arima), lag = 8, type = "Ljung-Box",
               fitdf = length(coef(fit_arima)))
det_txt <- c(
  paste0("Holdout: ", time(test_o)[1], " .. ", time(test_o)[H],
         " (last ", H, " quarters); MASE scale (seasonal-naive MAE on train) = ",
         round(mase_scale, 1), " (100 million CNY)"),
  paste0("auto.arima order: ", paste(arimaorder(fit_arima), collapse = ",")),
  paste0("Coefficients:\n", paste(capture.output(print(round(coef(fit_arima), 3))), collapse = "\n")),
  paste0("Ljung-Box on residuals (lag=8): Q = ", round(lb$statistic, 2),
         ", p = ", signif(lb$p.value, 3))
)
writeLines(det_txt, file.path(TABDIR, "tab_arima_details.txt"))
cat("\n", paste(det_txt, collapse = "\n"), "\n")
print(met)
