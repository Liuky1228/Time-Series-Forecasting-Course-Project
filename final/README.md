# Final project: Forecasting China's quarterly retail sales

Group 12 — STA4003 Time Series Analysis, 2026 Fall.

This folder contains the complete reproducible analysis and the final report for
the project "Forecasting China's Quarterly Retail Sales: Does a Lunar New Year
Adjustment Help?".

## What is in this folder

```
final/
  FinalReport_gp12.docx / .pdf        final written report
  Project_Explained_From_Scratch.md    from-zero Chinese guide to the project
  R/                                  analysis code (single entry point: R/run_all.R)
  scripts/                            Python helpers: summary, clean-run verifier,
                                      packaging, optional slide builder
  tests/                              R checks for the rolling panel and the
                                      supplementary analyses
  build_final_report.py               builds the Word report from R output
  make_equations.py                   renders the equations used in the report
  fetch_nbs_data.py                   re-downloads the raw NBS monthly data
  build_quarterly.py                  raw monthly data -> quarterly series
  requirements-report.txt             Python packages for the report build
  data/
    raw/                              NBS monthly retail, cumulative, PMI, y/y
    processed/                        quarterly retail and PMI, verification
    meta/                             lunar New Year dates
  reference/
    november_code/                    archived 13 Nov R scripts (frozen run)
    november_tables/                  archived 13 Nov result tables (frozen run)
    nbs_q3_releases.csv                NBS releases behind the 2026Q3 check
  output/
    figures/                          report figures
    tables/                           report tables (model, diagnostic, interval)
    equations/                        equation images
    optimization_summary.json         single verified summary used by slides
    verification/                     clean-run and delivery receipts
```

## Data

Source: National Bureau of Statistics of China (NBS), National Data platform,
`https://data.stats.gov.cn`, national aggregate. Raw data retrieved 28 September
2026. The primary series is quarterly total retail sales of consumer goods,
1994Q1–2026Q2 (N = 130). Quarterly manufacturing PMI covers 2005Q1–2026Q2
(N = 86). Lunar New Year dates cover 1994–2026.

The quarterly series is built from official monthly releases. Since 2012 the NBS
publishes January and February only as a combined Jan–Feb total, so Q1 is the
published Jan–Feb total plus March, and Q2–Q4 are recovered by differencing the
official cumulative series. The constructed series matches the published annual
totals exactly over 2000–2025. See `data/processed/VERIFICATION.txt`.

## Reproduce

Run everything from this `final/` directory. R 4.5 was used, with packages
`forecast`, `tseries`, `ggplot2`, `lmtest`, `zoo`, `scales`, `cowplot`, `dplyr`,
and `tidyr`. Python 3.13 was used, with `python-docx` and `matplotlib`.

```bash
# 1. Optional: re-download the raw NBS files (needs internet)
python3 fetch_nbs_data.py

# 2. Rebuild the quarterly series and verification report
python3 build_quarterly.py

# 3. Run the complete R analysis: EDA, stationarity, models,
#    rolling-origin evaluation, diagnostics, final forecasts, robustness,
#    interval scoring and supplementary analyses
Rscript R/run_all.R

# 4. Independent checks on the computed outputs
Rscript tests/test_outputs.R
Rscript tests/test_optimization.R
python3 scripts/summarize_results.py

# 5. Render the equations and build the report
python3 make_equations.py
python3 build_final_report.py

# 6. Optional: fresh-directory re-run receipt and packaging
python3 scripts/verify_clean_run.py --rscript /usr/local/bin/Rscript
python3 scripts/package_submission.py ../FinalProject_gp12.zip
```

`Rscript R/run_all.R` writes all figures to `output/figures/`, all tables to
`output/tables/`, `output/optimization_summary.json` and
`output/tables/sessionInfo.txt`. The report builder reads those tables and
figures, so the numbers in the report are generated from the code rather than
typed by hand.

## Analysis design in one paragraph

We work on log quarterly retail sales and compare **17 models**: three
benchmarks (mean, naive, seasonal naive), seven SARIMA specifications, six
dynamic regressions with CNY and/or two-quarter-lagged PMI (including two arms
that start in 2005Q3 so that the covariate can be compared with matched
controls), and a damped ETS(A,A,A). Models are evaluated by expanding-window
rolling origin from 2012Q1 to 2025Q4 (56 origins) at horizons h = 1 and h = 2,
using MAE, RMSE and MASE with a training-derived seasonal-naive scale shared by
all models at an origin. Point forecasts from log models are bias-adjusted
log-normal means; intervals are log-normal prediction intervals. The selected
model is SARIMA(0,1,1)(1,1,0)[4]. CNY and PMI do not improve two-step accuracy.

## Provenance

`reference/november_tables/` and `reference/november_code/` hold the archived
13 November run that produced the frozen forecast. The current pipeline
reproduces those archived numbers (identical for the selected model, the final
forecast and the diagnostic table; the archived Diebold-Mariano rows are all
retained alongside the new matched-control comparisons), and
`output/tables/tab_final_forecast_reconciliation.csv` records the
archived-versus-rerun differences row by row.

## Notes

- Units are 100 million CNY (亿元) throughout, except where trillion CNY is
  explicitly stated.
- `data/README.md` documents the raw and processed files in more detail.
- `output/tables/sessionInfo.txt` records the R session used for the final run.
- The presentation slides (`Presentation_gp12.pdf`) are prepared separately and
  are not part of this analysis folder yet.
