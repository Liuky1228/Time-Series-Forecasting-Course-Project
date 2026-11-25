"""Regenerate the STA4003 interim report (Word) with data-driven numbers.

Reads proposal/data/processed/*.csv plus interim/output/tables/*.csv,
computes facts cited in the text, and writes InterimReport_gp12_draft.docx.
Formatting per project brief: A4, 1" margins, Times New Roman 12 pt,
1.15 line spacing, 6 pt space after each paragraph; main text <= 6 pages.
"""
import csv, os
from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = "/Users/keyi/Desktop/STA4003/proposal/data"
TAB = os.path.join(HERE, "output", "tables")
FIG = os.path.join(HERE, "output", "figures")


def read_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        r = csv.reader(f)
        hdr = next(r)
        rows = [row for row in r if row]
    return hdr, rows


_, ret_rows = read_csv(os.path.join(DATA, "processed", "retail_quarterly.csv"))
_, pmi_rows = read_csv(os.path.join(DATA, "processed", "pmi_quarterly.csv"))
RET = {r[0]: float(r[1]) for r in ret_rows}
PMI = {r[0]: float(r[1]) for r in pmi_rows}
QKY = sorted(RET)
N, FIRST, LAST = len(QKY), QKY[0], QKY[-1]

annual = {y: sum(RET[f"{y}Q{q}"] for q in range(1, 5))
          for y in range(1994, 2026)}
g2020 = (RET["2020Q1"] / RET["2019Q1"] - 1) * 100

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin = sec.bottom_margin = sec.left_margin = sec.right_margin = Inches(1)
st = doc.styles["Normal"]
st.font.name, st.font.size = "Times New Roman", Pt(12)
st.paragraph_format.line_spacing = 1.15
st.paragraph_format.space_after = Pt(6)


def para(text, bold=False, center=False, size=12, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(6)
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    r.font.name, r.font.size = "Times New Roman", Pt(size)
    return p


def heading(t):
    return para(t, bold=True)


def body(t):
    return para(t)


def add_figure(name, width_in, caption):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(3)
    p.add_run().add_picture(os.path.join(FIG, name), width=Inches(width_in))
    c = para(caption, size=10, italic=True)
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(8)


def add_table(rows, caption, fs=10):
    c = para(caption, size=10)
    c.paragraph_format.space_after = Pt(3)
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.text = ""
            run = cell.paragraphs[0].add_run(str(val))
            run.font.size = Pt(fs)
            run.font.name = "Times New Roman"
            run.bold = (i == 0)
            cell.paragraphs[0].paragraph_format.space_after = Pt(2)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    return t


para("Interim Report: Forecasting China's Quarterly Retail Sales With a Lunar New Year Adjustment",
     bold=True, center=True)
para("Group 12 — ⟨Member 1 Name / Student ID⟩  ⟨Member 2 Name / Student ID⟩  "
     "⟨Member 3 Name / Student ID⟩  ⟨Member 4 Name / Student ID⟩", center=True, size=11)
para("STA4003 Time Series Analysis — Interim report, due 25 October 2026. "
     "Data cut-off: 28 September 2026 (window fixed at 2026Q2).", center=True, size=10, italic=True)

heading("1.  Forecasting question and data (restated)")
body("Can China's quarterly total retail sales of consumer goods be forecast reliably two quarters "
     "(six months) ahead, and does adding a lunar-New-Year position covariate improve on standard "
     "seasonal models? The primary series is the official National Bureau of Statistics (NBS) series "
     f"of total retail sales of consumer goods, aggregated to quarters: {FIRST} to {LAST}, "
     f"N = {N} observations covering 32 complete seasonal cycles. The auxiliary series is the quarterly "
     f"manufacturing PMI ({min(PMI)} to {max(PMI)}, N = {len(PMI)}), retained as a candidate "
     "explanatory variable. The sample window is fixed at 2026Q2: September 2026 retail data were not "
     "yet published at the data cut-off, and a fixed window keeps all models and the proposal "
     "consistent.")

heading("2.  Data construction and cleaning (with justification)")
hdr1, rows1 = read_csv(os.path.join(TAB, "tab_data_summary.csv"))
body("Since 2012 the NBS releases January and February retail sales only as a combined total, so the "
     "monthly series is structurally incomplete for those months (30 unseparated months in the sample) "
     "and the effective season is irregular. We therefore aggregate to quarters: Q1 is the published "
     "January-February total plus March; Q2-Q4 are recovered by differencing the official cumulative "
     "series, which telescopes exactly to the published annual totals (maximum discrepancy 0 over "
     "2000-2025; 1994-1999 use official monthly aggregations). Where the current-month and cumulative "
     "vintages disagree (2005, about 5.2% annually; 2011, about 0.2%), we use the cumulative vintage "
     "because it reproduces the officially published annual totals (e.g. 2025: 50.1 trillion CNY). "
     "Result: no missing quarters, no duplicates, and the quarterly series matches official annual "
     "totals by construction. Chinese New Year dates for 1994-2026 come from the lunar calendar and "
     "were checked against published holiday dates. The observations 2020Q1 "
     f"(y/y {g2020:.1f}%) and 2022Q2 reflect real COVID-19 shocks and are retained, not removed.")
add_table([["Item", "Value"]] + [[r[0], r[1]] for r in rows1],
          "Table 1: Data summary and construction checks.")

heading("3.  Exploratory data analysis")
body("Figure 1 shows the log quarterly series. Retail sales grew from 0.36 trillion CNY in 1994Q1 to "
     "12.10 trillion CNY in 2026Q2, with variance increasing in the level, which motivates the log "
     "transform; the two shaded bands mark 2020Q1 and 2022Q2. Figure 2 shows a strong and highly "
     "stable seasonal pattern: Q4 is the peak quarter in every one of the 32 complete years "
     "(mean share 28.5% of the annual total, versus 23.4% for the lowest quarter, Q2). Figure 3 "
     "shows that the ACF of log retail decays very slowly with large spikes at multiples of 4, "
     "indicating both non-stationarity and strong seasonality; the PACF is in Appendix Figure A1.")
add_figure("fig1_log_ts.png", 5.6,
           "Figure 1: Log quarterly retail sales, 1994Q1-2026Q2 (N = 130); shaded bands mark 2020Q1 and 2022Q2.")
add_figure("fig2_seasonal_boxplot.png", 4.8,
           "Figure 2: Distribution of log retail sales by calendar quarter.")
add_figure("fig3_acf_levels.png", 5.6,
           "Figure 3: ACF of log retail sales in levels (lag 40).")
body("The lunar New Year moves between January and February, so fixed seasonal factors are only "
     "approximate. In the monthly era 1994-2011, when January and February were published separately, "
     "the mean February-to-January sales ratio was 0.909 in the 6 years with CNY in January and 0.949 "
     "in the 12 years with CNY in February. At quarterly resolution (2012-2025), mean Q1 share of "
     "the annual total was 23.4% when CNY fell in January and 23.9% when it fell in February "
     "(Table 2). Figure 4 plots Q1 share against the continuous covariate \"fraction of Q1 elapsed "
     "before CNY\" for the 32 complete years 1994-2025 only (incomplete years, such as 2026 with "
     "two quarters published, are excluded from share calculations). Across these years no linear "
     "association is present (Pearson r = 0.003, p = 0.99): at quarterly resolution the lunar New "
     "Year position explains essentially none of the year-to-year variation in Q1 share, even "
     "though the monthly-era contrast is clear. Whether the covariate nevertheless improves "
     "forecasts must therefore be established by out-of-sample comparison in the final analysis.")
hdrf, rowsf = read_csv(os.path.join(TAB, "tab_cny_febjan.csv"))
hdrq, rowsq = read_csv(os.path.join(TAB, "tab_cny_q1_share.csv"))
qmap = {(r[0], r[1]): (r[2], r[3]) for r in rowsq}
merged = [["Era", "CNY month", "n", "Mean Feb/Jan ratio", "Mean Q1 share (%)"]]
for r in rowsf:
    era_key = r[0].split(" (")[0]
    n2, s2 = qmap.get((era_key, r[1]), ("", ""))
    merged.append([era_key, r[1].replace("CNY in ", ""), r[2], r[3], s2])
for r in rowsq:
    if r[0] == "1994-2025":
        merged.append([r[0], r[1].replace("CNY in ", ""), r[2], "-", r[3]])
add_table(merged, "Table 2: Chinese New Year position and Q1 retail share "
                  "(Feb/Jan ratio only available 1994-2011).")
add_figure("fig4_cny_scatter.png", 5.6,
           "Figure 4: Q1 share of annual retail sales vs. fraction of Q1 elapsed before CNY, 1994-2025.")

heading("4.  Preprocessing decisions")
body("Decisions so far: (i) work on log retail sales, for variance stabilization (Figures 1-2); "
     "(ii) difference both non-seasonally and seasonally, with the choice justified by formal tests. "
     "Table 3 reports ADF (H0: unit root) and KPSS (H0: level stationarity) tests. Log levels are "
     "non-stationary by both tests; first differencing alone leaves borderline evidence and clear "
     "annual spikes in the ACF (Appendix Figure A2); seasonal differencing alone does not remove the "
     "non-seasonal unit root; after log, d = 1 and D = 1 (period 4) both tests indicate stationarity "
     "(ADF p < 0.01, KPSS p = 0.10). Figure 5 shows that the long-run persistence visible in "
     "Figure 3 has disappeared, but lag 1 (-0.33) and lag 4 (-0.49) remain clearly outside the "
     "bounds, i.e. the differenced series is stationary yet not white noise: short-run and seasonal "
     "dependence remains for the model to absorb. This is a property of the differenced series, not "
     "of model residuals (white-noise residuals are required of the fitted model and are checked in "
     "Section 5); a candidate specification with less differencing is left as a comparison for the "
     "final analysis. All candidate models will therefore be built on log sales with d = 1, D = 1, "
     "m = 4 as the starting point.")
h3, rows3 = read_csv(os.path.join(TAB, "tab_stationarity.csv"))
add_table([["Series", "ADF stat", "ADF p", "KPSS stat", "KPSS p"]] +
          [[r[0], r[1], r[2], r[3], r[4]] for r in rows3],
          "Table 3: ADF and KPSS tests on log retail and candidate difference orders.")
add_figure("fig5_acf_after_diff.png", 5.6,
           "Figure 5: ACF after log transform with d = 1 and D = 1 (period 4) differencing.")

heading("5.  Preliminary model comparison (single holdout)")
body("As a first, deliberately simple check, four models are compared on one fixed holdout: the last "
     "8 quarters (2024Q3-2026Q2), with 122 quarters of training data. The historical mean, naive and "
     "seasonal-naive benchmarks and an automatic seasonal ARIMA (full search, AICc) are fitted on log "
     "sales; point forecasts are back-transformed, and accuracy is measured on the original scale. "
     "The selected ARIMA has orders (0,1,1)(0,1,1)[4] with ma1 = -0.361 and sma1 = -0.653. "
     "Table 4 shows that the ARIMA model beats all three benchmarks on this holdout (MASE 0.91 < 1, "
     "i.e. better than the seasonal-naive benchmark used to scale MASE), the seasonal-naive is next, "
     "and the mean benchmark is very poor. A Ljung-Box test on the ARIMA residuals (lag 8) gives "
     "p = 0.78, so no residual autocorrelation is detected at this stage.")
h4, rows4 = read_csv(os.path.join(TAB, "tab_model_metrics.csv"))
add_table([["Model", "MAE (100 mn CNY)", "RMSE (100 mn CNY)", "MASE"]] +
          [[r[0], r[1], r[2], r[3]] for r in rows4],
          "Table 4: Holdout accuracy, 2024Q3-2026Q2 (h = 1..8); MASE scaled by in-sample "
          "seasonal-naive MAE of 4,478 (100 million CNY). Lower is better.")
body("Caveats, to be addressed in the final analysis: a single holdout split; orders selected "
     "automatically rather than from ACF/PACF reasoning; no bias adjustment when back-transforming "
     "log forecasts; and the lunar-New-Year and PMI covariates have not yet been used.")

heading("6.  Current findings, limitations and next steps")
body("Current findings: (i) retail sales are trending, strongly seasonal with a stable Q4 peak, and "
     "heteroskedastic in the level, supporting the log + (1,1,1)[4] specification; (ii) on a single "
     "holdout, a parsimonious SARIMA already outperforms standard benchmarks; (iii) the lunar New "
     "Year position effect is clear monthly but undetectable at quarterly resolution in complete "
     "years, so its value as a forecasting covariate is an open question rather than an "
     "established fact.")
body("Remaining issues and next steps for the final report: (1) estimate dynamic-regression "
     "(ARIMAX) models adding the CNY-position covariate and quarterly PMI (contemporaneous and "
     "one-quarter lag), and test whether they improve on SARIMA; (2) replace the single split with "
     "rolling-origin evaluation at h = 1 and h = 2 on a common window from 2005Q1; (3) compare "
     "additional candidates (ETS or Theta) as a robustness check, together with specifications "
     "using less differencing (smaller d or D), since Figure 5 still shows negative correlation at "
     "lags 1 and 4; (4) apply bias adjustment when "
     "back-transforming and report 80% and 95% prediction intervals for the next two quarters; "
     "(5) final residual diagnostics and interpretation. Modeling and graphic decisions made here "
     "will be revised if the later evidence supports a better choice.")

heading("References")
for r_ in [
    "National Bureau of Statistics of China. National Data (国家数据) — retail sales and purchasing managers index datasets. https://data.stats.gov.cn. Retrieved 28 September 2026.",
    "National Bureau of Statistics of China (2025). 社会消费品零售总额统计指标说明及第五次全国经济普查修订说明 (indicator annotation retrieved from the National Data platform).",
    "National Bureau of Statistics of China. 采购经理指数编制加工说明. http://www.stats.gov.cn.",
    "Hyndman, R. J., & Athanasopoulos, G. (2021). Forecasting: Principles and Practice (3rd ed.). OTexts.",
    "Shumway, R. H., & Stoffer, D. S. (2017). Time Series Analysis and Its Applications (4th ed.). Springer.",
]:
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.first_line_indent = Inches(-0.3)
    run = p.add_run(r_)
    run.font.name, run.font.size = "Times New Roman", Pt(12)

heading("Appendix (not counted toward the page limit)")
add_figure("figA1_pacf_levels.png", 5.6,
           "Figure A1: PACF of log retail sales in levels.")
add_figure("figA2_acf_first_diff.png", 5.6,
           "Figure A2: ACF after first differencing only (d = 1, D = 0); annual spikes remain.")

out = os.path.join(HERE, "InterimReport_gp12_draft.docx")
doc.save(out)
print("saved", out)
