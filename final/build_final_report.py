"""Build FinalReport_gp12.docx from the R output tables and figures.

Run from the final/ directory:
    /Users/keyi/Desktop/STA4003/.venv/bin/python build_final_report.py

Formatting follows the STA4003 brief: A4, 1-inch margins, Times New Roman
12 pt, 1.15 line spacing, 6 pt after each paragraph.  Equations are rendered
as high-resolution PNGs by make_equations.py.
"""
import csv
import os
from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
TAB = os.path.join(HERE, "output", "tables")
FIG = os.path.join(HERE, "output", "figures")
EQ = os.path.join(HERE, "output", "equations")
DATA = os.path.join(HERE, "data", "processed")


def read_csv(name):
    with open(os.path.join(TAB, name), newline="", encoding="utf-8-sig") as f:
        return [row for row in csv.DictReader(f) if row]


def read_data_csv(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8-sig") as f:
        return [row for row in csv.DictReader(f) if row]


def fnum(x, d=0):
    return f"{float(x):,.{d}f}"


def fpct(x, d=1):
    return f"{100 * float(x):.{d}f}%"


def pfmt(p):
    p = float(p)
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


def get(rows, **kwargs):
    for r in rows:
        if all(str(r.get(k, "")) == str(v) for k, v in kwargs.items()):
            return r
    raise KeyError(kwargs)


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
acc = read_csv("tab_rolling_accuracy_wide.csv")
acc = sorted(acc, key=lambda r: float(r["MASE_h2"]))
best2 = read_csv("tab_best_model.csv")[0]
best1 = read_csv("tab_best_model_h1.csv")[0]
diag = read_csv("tab_diagnostics.csv")[0]
coefs = read_csv("tab_coefficients.csv")
cov = read_csv("tab_covariate_models.csv")
dm = read_csv("tab_dm_tests.csv")
final = read_csv("tab_final_forecast.csv")
sel = read_csv("tab_model_selection.csv")
rob = read_csv("tab_robustness_h2.csv")
cny_tab = read_csv("tab_cny_evidence.csv")
season = read_csv("tab_seasonality.csv")
stat = read_csv("tab_stationarity.csv")
data_summary = read_csv("tab_data_summary.csv")
errors = read_csv("tab_rolling_errors.csv")

retail = {r["quarter"]: float(r["value_bn"]) for r in read_data_csv("retail_quarterly.csv")}
origins = sorted({r["origin"] for r in errors})
n_origins = len(origins)
n_models = len({r["model"] for r in errors})

q3 = final[0]
q4 = final[1]
yoy_q3 = (float(q3["point"]) / retail["2025Q3"] - 1) * 100
yoy_q4 = (float(q4["point"]) / retail["2025Q4"] - 1) * 100
annual_2025 = sum(retail[f"2025Q{q}"] for q in range(1, 5))
annual_2026 = (retail["2026Q1"] + retail["2026Q2"]
               + float(q3["point"]) + float(q4["point"]))
yoy_annual = (annual_2026 / annual_2025 - 1) * 100

acc_by_id = {r["model"]: r for r in acc}
dm_lookup = {(r["h"], r["Comparison"]): r for r in dm}
cov_by = {(r["model"], r["term"]): r for r in cov}

# ---------------------------------------------------------------------------
# Document setup
# ---------------------------------------------------------------------------
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin = sec.bottom_margin = Inches(1)
sec.left_margin = sec.right_margin = Inches(1)

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(12)
normal.paragraph_format.line_spacing = 1.15
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.space_before = Pt(0)
rpr = normal.element.get_or_add_rPr()
rfonts = rpr.find(qn("w:rFonts"))
if rfonts is None:
    rfonts = OxmlElement("w:rFonts")
    rpr.append(rfonts)
rfonts.set(qn("w:eastAsia"), "Times New Roman")


def para(text="", bold=False, italic=False, size=12, center=False,
         space_before=0, space_after=6, first_indent=None):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if first_indent is not None:
        p.paragraph_format.first_line_indent = Inches(first_indent)
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    r.font.name, r.font.size = "Times New Roman", Pt(size)
    return p


def heading(text):
    p = para(text, bold=True, size=12, space_before=10, space_after=4)
    p.paragraph_format.keep_with_next = True
    return p


def caption(text):
    p = para(text, size=9.5, italic=False, space_before=2, space_after=3)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return p


def note(text):
    p = para(text, size=8.5, italic=True, space_before=0, space_after=8)
    return p


def add_figure(name, cap, width=6.2):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(os.path.join(FIG, name), width=Inches(width))
    c = caption(cap)
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return c


def add_equation(name, width=5.2):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(5)
    p.add_run().add_picture(os.path.join(EQ, name), width=Inches(width))


def add_table(rows, cap, col_widths=None, font_size=9, header_rows=1):
    if cap:
        c = caption(cap)
        c.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.0
            if i < len(rows) - 1:
                p.paragraph_format.keep_with_next = True
            r = p.add_run(str(val))
            r.font.name = "Times New Roman"
            r.font.size = Pt(font_size)
            r.bold = i < header_rows
            if j > 0 and i >= header_rows:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if isinstance(val, (int, float)) else WD_ALIGN_PARAGRAPH.LEFT
        trPr = t.rows[i]._tr.get_or_add_trPr()
        cantSplit = OxmlElement("w:cantSplit")
        trPr.append(cantSplit)
        if i < header_rows:
            tblHeader = OxmlElement("w:tblHeader")
            tblHeader.set(qn("w:val"), "true")
            trPr.append(tblHeader)
    if col_widths:
        for j, w in enumerate(col_widths):
            for cell in t.columns[j].cells:
                cell.width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def add_page_number(paragraph):
    run = paragraph.add_run()
    fld1 = OxmlElement("w:fldChar"); fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = "PAGE"
    fld2 = OxmlElement("w:fldChar"); fld2.set(qn("w:fldCharType"), "end")
    run._r.append(fld1); run._r.append(instr); run._r.append(fld2)
    run.font.name = "Times New Roman"
    run.font.size = Pt(9)


footer_p = sec.footer.paragraphs[0]
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_page_number(footer_p)

# ---------------------------------------------------------------------------
# Title and summary
# ---------------------------------------------------------------------------
para("Forecasting China's Quarterly Retail Sales: "
     "Does a Lunar New Year Adjustment Help?",
     bold=True, size=15, center=True, space_after=4)
para("Group 12  —  傅敖 124090117  刘可熠 124090374  公硕 124090138  "
     "颜廷宇 124090831  罗祥旭 124020304",
     size=10.0, center=True, space_after=2)
para("STA4003 Time Series Analysis  ·  Final report  ·  30 November 2026  ·  "
     "Data cut-off: 2026Q2",
     size=9.5, italic=True, center=True, space_after=10)

heading("Summary")
para(
    "This report forecasts China's quarterly total retail sales two quarters ahead and asks "
    "whether explicitly accounting for the moving lunar New Year (CNY) improves out-of-sample "
    "accuracy relative to a standard seasonal model. We construct a 130-quarter series "
    "(1994Q1–2026Q2) from official National Bureau of Statistics (NBS) releases, work on logs, "
    "and compare 14 models by expanding-window rolling origin from 2012Q1 to 2025Q4. "
    f"A parsimonious SARIMA(0,1,1)(1,1,0)[4] has the lowest two-step MASE "
    f"({float(best2['MASE']):.3f}), about {(1-float(best2['MASE'])/float(acc_by_id['SNaive']['MASE_h2']))*100:.0f}% "
    f"below the seasonal-naive benchmark ({float(acc_by_id['SNaive']['MASE_h2']):.3f}). "
    "The improvement is statistically significant at the one-quarter horizon (Diebold–Mariano "
    "p = 0.007) and directionally strong but not significant at the two-quarter horizon "
    "(p = 0.097). We find no evidence that adding CNY or PMI improves two-step accuracy. The final forecasts are "
    f"{fnum(q3['point'])} (80% interval {fnum(q3['lo80'])}–{fnum(q3['hi80'])}) for 2026Q3 and "
    f"{fnum(q4['point'])} (80% interval {fnum(q4['lo80'])}–{fnum(q4['hi80'])}) for 2026Q4, "
    "in 100 million CNY."
)

# ---------------------------------------------------------------------------
# 1 Introduction
# ---------------------------------------------------------------------------
heading("1.  Forecasting question and motivation")
para(
    "Total retail sales of consumer goods is a headline indicator of household consumption in "
    "China. Accurate six-month-ahead forecasts are useful for retailers' inventory and staffing "
    "decisions, for assessing the momentum of consumption policy, and for short-term demand "
    "analysis. The forecasting question is therefore practical rather than descriptive: can the "
    "quarterly series be forecast reliably two quarters ahead, and does a calendar adjustment for "
    "the moving lunar New Year improve out-of-sample accuracy?"
)
para(
    "The CNY question is economically interesting because the holiday moves between late January "
    "and mid-February. At monthly frequency this shifts sales between January and February. At "
    "quarterly frequency, however, a pure timing shift may leave the Q1 total roughly unchanged. "
    "Whether the covariate nevertheless improves forecasts is an empirical question, and we answer "
    "it with a rolling-origin comparison rather than with in-sample significance."
)
para(
    "The paper makes three contributions. First, we build a transparent quarterly series from "
    "official NBS monthly releases, including the post-2012 Jan–Feb combined release. Second, we "
    "evaluate a wide set of benchmarks, SARIMA specifications, dynamic regressions with CNY and "
    "PMI, and an ETS competitor on a common rolling-origin window. Third, we report the result "
    "that is most useful for practice: a simple seasonal ARIMA is hard to beat at the two-quarter "
    "horizon, and the CNY adjustment does not deliver a robust gain at quarterly resolution."
)

# ---------------------------------------------------------------------------
# 2 Data
# ---------------------------------------------------------------------------
heading("2.  Data")
para(
    "The primary series is national total retail sales of consumer goods from the NBS National "
    "Data platform (retrieved 28 September 2026). Since 2012 the NBS has published January and "
    "February only as a combined Jan–Feb total. We therefore aggregate to quarters: Q1 is the "
    "published Jan–Feb total plus March; Q2–Q4 are recovered by differencing the official "
    "cumulative series. The constructed quarterly series matches the published annual totals "
    "exactly over 2000–2025 (maximum discrepancy zero); 1994–1999 use official monthly "
    "aggregations. The resulting sample is 1994Q1–2026Q2, N = 130, with 32 complete years plus "
    "two quarters and no missing quarters or duplicates."
)
para(
    "Quarterly manufacturing PMI is available from 2005Q1 to 2026Q2 (N = 86) and is used as a "
    "candidate leading indicator. Lunar New Year dates for 1994–2026 come from the lunar calendar "
    "and were cross-checked against official holiday schedules. The target is a nominal aggregate: "
    "movements reflect both prices and quantities. The analysis is therefore a sales-forecasting "
    "exercise, not a causal analysis of real consumption."
)

rows = [["Item", "Value"]] + [[r["Item"], r["Value"]] for r in data_summary]
add_table(rows, "Table 1. Data summary and construction checks.",
          col_widths=[1.85, 4.25], font_size=8.8)

para(
    "Three data-quality issues matter. First, the current-month and cumulative vintages disagree "
    "in 2005 (about 5.2% annually) and 2011 (about 0.2%); we use the cumulative vintage because it "
    "reproduces the official annual totals. Second, 2020Q1 and 2022Q2 are genuine COVID-19 shocks "
    "and are retained; removing them would understate forecast uncertainty. Third, the series was "
    "revised under the Fifth National Economic Census, so growth rates from 2025 onward are on a "
    "comparable basis. None of these issues requires imputation."
)

# ---------------------------------------------------------------------------
# 3 EDA
# ---------------------------------------------------------------------------
heading("3.  Exploratory analysis")
add_figure("fig1_eda.png",
           "Figure 1. (A) Log quarterly retail sales, 1994Q1–2026Q2 (N = 130); shaded bands mark "
           "2020Q1 and 2022Q2. (B) Distribution of log sales by calendar quarter.", width=6.0)
para(
    "Figure 1 shows retail sales growing from 0.36 trillion CNY in 1994Q1 to 12.10 trillion CNY in 2026Q2. The "
    "variance rises with the level, which motivates the log transformation used throughout. The "
    "two COVID-19 observations are visible as sharp drops. Seasonality is strong and stable: Q4 is "
    "the peak quarter in all 32 complete years, with a mean share of 28.5% of annual sales, while "
    "Q2 is the lowest quarter on average (23.4%) and the trough in 22 of 32 years. Q1 is 23.7% "
    "and Q3 is 24.4%."
)

add_figure("fig3_acf.png",
           "Figure 2. (A) ACF of log retail sales in levels. (B) ACF after first and seasonal "
           "differencing (d = 1, D = 1, period 4).", width=6.0)
para(
    "The ACF in levels decays very slowly, indicating non-stationarity and trend dominance "
    "(Figure 2A); seasonal spikes at lags 4, 8 and 12 appear after first differencing "
    "(Appendix Figure A2). After d = 1 and D = 1, the long-run "
    "persistence disappears, but lag 1 (−0.33) and lag 4 (−0.49) remain outside the ±0.175 "
    "approximate 95% bands. The differenced series is therefore stationary but not white noise: "
    "short-run and seasonal dependence remains for the model to absorb. The strong negative "
    "correlation at lag 4 also motivates comparing specifications with less seasonal differencing "
    "and with seasonal AR or MA terms."
)

para(
    "The CNY evidence is more subtle than the headline “holiday effect” suggests. In the monthly "
    "era 1994–2011, when January and February were published separately, the mean February-to-"
    "January sales ratio was 0.909 in the six years with CNY in January and 0.949 in the twelve "
    "years with CNY in February (Table 2). At quarterly resolution, however, the Q1 share is "
    "23.4% when CNY falls in January and 23.9% when it falls in February, a difference of only "
    "0.5 percentage points. Across the 32 complete years, the correlation between the Q1 share and "
    "the fraction of Q1 elapsed before CNY is 0.003 (p = 0.99). Figure 3 makes the contrast "
    "visible: the holiday shifts sales within Q1, but it does not move the Q1 total in a "
    "detectable linear way."
)

rows = [["Era", "CNY month", "n", "Mean Feb/Jan ratio", "Mean Q1 share"]]
for r in cny_tab:
    rows.append([r["Era"], r["Group"].replace("CNY in ", ""), r["n"],
                 "–" if r["Mean_Feb_Jan"] == "" else f"{float(r['Mean_Feb_Jan']):.3f}",
                 fpct(float(r["Mean_Q1_Share"]) / 100, 1)])
add_table(rows, "Table 2. Chinese New Year position and Q1 retail share (Feb/Jan ratio available "
                "only for 1994–2011; Q1 shares use complete years 1994–2025).",
          col_widths=[1.2, 1.0, 0.55, 1.55, 1.45], font_size=9)

add_figure("fig4_cny.png",
           "Figure 3. (A) Q1 share of annual sales against the fraction of Q1 elapsed before CNY, "
           "1994–2025. (B) February/January sales ratio by CNY month, 1994–2011.", width=6.0)

# ---------------------------------------------------------------------------
# 4 Preprocessing and stationarity
# ---------------------------------------------------------------------------
heading("4.  Preprocessing and stationarity")
para(
    "We work with the natural logarithm of retail sales, y_t = log(retail_t). The log stabilises "
    "the variance and makes multiplicative growth approximately linear. To choose the difference "
    "orders we use the augmented Dickey–Fuller (ADF) test, whose regression is"
)
add_equation("eq_adf.png", width=4.6)
para(
    "where the null hypothesis is a unit root, and the KPSS test, whose null is stationarity. The "
    "two tests have different nulls and deterministic specifications, so they need not agree "
    "exactly. Table 3 reports both."
)

rows = [["Series", "ADF stat", "ADF p", "KPSS stat", "KPSS p"]]
for r in stat:
    rows.append([r["Series"], r["ADF_stat"], r["ADF_p_txt"], r["KPSS_stat"], r["KPSS_p_txt"]])
add_table(rows, "Table 3. ADF and KPSS tests on log retail sales and candidate difference orders.",
          col_widths=[2.35, 0.95, 0.8, 0.95, 0.8], font_size=9)
note("Note: ADF H0 = unit root; KPSS H0 = stationarity. ADF includes a constant and trend; KPSS "
     "tests level stationarity. Values below 0.01 are reported as “<0.01”.")

para(
    "Log levels are non-stationary by both tests. First differencing alone gives a borderline "
    "result (ADF p = 0.020, KPSS p = 0.045) and leaves clear annual spikes in the ACF. Seasonal "
    "differencing alone leaves the non-seasonal unit root (ADF p = 0.214). After d = 1 and D = 1, "
    "both tests support stationarity (ADF p < 0.01, KPSS p = 0.100), so this is our baseline "
    "transformation. Because the differenced ACF still shows negative dependence at lags 1 and 4, "
    "we also estimate specifications with D = 0 and with seasonal AR or MA terms, and let the "
    "rolling-origin comparison decide."
)
para(
    "The general multiplicative SARIMA(p,d,q)(P,D,Q)[4] model used below is"
)
add_equation("eq_sarima.png", width=5.4)
para(
    "where B is the backshift operator, φ and θ are the non-seasonal AR and MA polynomials, Φ and "
    "Θ are their seasonal counterparts, and ε_t is white noise. For the covariate models we add "
    "the CNY and PMI terms described in Section 5."
)

# ---------------------------------------------------------------------------
# 5 Models and evaluation design
# ---------------------------------------------------------------------------
heading("5.  Models and evaluation design")
para(
    "We compare three benchmarks, six SARIMA specifications, four dynamic regressions with "
    "covariates, and one exponential smoothing model (Table 4). The benchmarks are the historical "
    "mean, the naive forecast, and the seasonal naive forecast. The SARIMA specifications vary the "
    "non-seasonal and seasonal orders to reflect the ACF evidence: the interim specification "
    "(0,1,1)(0,1,1), an AR(1) extension, a seasonal AR variant (1,1,0), a variant with both "
    "seasonal AR and MA terms (1,1,1), and two D = 0 specifications with and without drift. "
    "The dynamic regressions keep the parsimonious (0,1,1)(0,1,1) order fixed and add either the "
    "CNY position, a January dummy, the two-quarter-lagged PMI, or both covariates. Keeping the "
    "ARMA order fixed means that any change in accuracy can be attributed to the covariate rather "
    "than to a different short-run structure."
)
para(
    "The CNY covariate is the fraction of Q1 elapsed before CNY in Q1 and zero in Q2–Q4. It is "
    "known in advance for any forecast origin, so it is a legitimate real-time predictor. The PMI "
    "covariate enters with a two-quarter lag:"
)
add_equation("eq_sarimax.png", width=5.4)
para(
    "The lag is deliberate. At a forecast origin at the end of quarter T, a two-step forecast for "
    "T+2 can use PMI in T, but not PMI in T+1. Using the contemporaneous PMI would therefore "
    "require a PMI forecast and would overstate the information available in real time."
)

rows = [["Family", "Specification", "Role"]]
rows += [
    ["Benchmark", "Mean", "Simple benchmark"],
    ["Benchmark", "Naive", "Simple benchmark"],
    ["Benchmark", "Seasonal naive", "Simple benchmark"],
    ["SARIMA", "SARIMA(0,1,1)(0,1,1)[4]", "Interim specification"],
    ["SARIMA", "SARIMA(1,1,1)(0,1,1)[4]", "AR extension"],
    ["SARIMA", "SARIMA(0,1,1)(1,1,0)[4]", "Seasonal AR"],
    ["SARIMA", "SARIMA(0,1,1)(1,1,1)[4]", "Seasonal AR + MA"],
    ["SARIMA", "SARIMA(0,1,1)(0,0,1)[4]", "Less seasonal differencing"],
    ["SARIMA", "SARIMA(0,1,1)(0,0,1)[4] + drift", "Less differencing + drift"],
    ["SARIMAX", "SARIMAX + CNY", "CNY position"],
    ["SARIMAX", "SARIMAX + CNY (Jan dummy)", "Alternative CNY coding"],
    ["SARIMAX", "SARIMAX + PMI(−2)", "Lagged PMI"],
    ["SARIMAX", "SARIMAX + CNY + PMI(−2)", "Both covariates"],
    ["ETS", "ETS(A,A,A), damped", "Robustness comparison"],
]
add_table(rows, "Table 4. Candidate models.",
          col_widths=[0.9, 2.85, 2.35], font_size=8.6)

para(
    f"We evaluate all models on an expanding window with origins from 2012Q1 to 2025Q4 "
    f"({n_origins} origins). The start date is chosen because the post-2012 data are constructed "
    "under the combined Jan–Feb regime and because the PMI models need a reasonable training "
    "history after the two-quarter lag (the first usable PMI observation is 2005Q3). At each "
    "origin the model is re-estimated and forecasts are made for h = 1 and h = 2. We report mean "
    "absolute error (MAE), root mean squared error (RMSE), and the mean absolute scaled error "
    "(MASE):"
)
add_equation("eq_mase.png", width=4.4)
para(
    "The scaling denominator is the seasonal-naive MAE on the full training history at each "
    "origin, held common across models so that MASE values are comparable. MASE < 1 means better "
    "than the seasonal-naive benchmark. Point forecasts from log "
    "models are back-transformed with the log-normal bias adjustment"
)
add_equation("eq_backtransform.png", width=5.2)
para(
    "where μ̂ and σ̂ are the log-scale forecast mean and standard error; the reported intervals are "
    "the exponentials of the log-scale quantiles, which is exact under log-normality. Finally, we "
    "use the Diebold–Mariano test to compare loss differences:"
)
add_equation("eq_dm.png", width=3.6)

# ---------------------------------------------------------------------------
# 6 Rolling-origin results
# ---------------------------------------------------------------------------
heading("6.  Rolling-origin results")
para(
    "Table 5 and Figure 4 report accuracy for all 14 models. The best two-step model is "
    f"{best2['label']}, with MAE {fnum(best2['MAE'])}, RMSE {fnum(best2['RMSE'])}, and MASE "
    f"{float(best2['MASE']):.3f}. The seasonal-naive benchmark has MASE "
    f"{float(acc_by_id['SNaive']['MASE_h2']):.3f}, and the naive benchmark is much worse "
    f"({float(acc_by_id['Naive']['MASE_h2']):.3f}). The mean benchmark is uninformative for a "
    "trending series (MASE > 16). At h = 1 the ranking is similar but the errors are smaller: the "
    f"best one-step model is {best1['label']}, with MASE {float(best1['MASE']):.3f}."
)

rows = [["Model", "MAE h=1", "RMSE h=1", "MASE h=1", "MAE h=2", "RMSE h=2", "MASE h=2"]]
for r in acc:
    rows.append([r["label"], fnum(r["MAE_h1"]), fnum(r["RMSE_h1"]), f"{float(r['MASE_h1']):.3f}",
                 fnum(r["MAE_h2"]), fnum(r["RMSE_h2"]), f"{float(r['MASE_h2']):.3f}"])
add_table(rows, "Table 5. Rolling-origin accuracy, 2012Q1–2025Q4 (56 origins). Errors are in "
                "100 million CNY; MASE is scaled by the seasonal-naive MAE on the full training "
                "history at each origin (common across models). Lower is better.",
          col_widths=[2.0, 0.72, 0.82, 0.72, 0.72, 0.82, 0.72], font_size=8.2)

add_figure("fig5_rolling_mase.png",
           "Figure 4. MASE at the two-quarter horizon. The mean benchmark (MASE = 16.7) is omitted "
           "for readability; the dashed line marks MASE = 1.", width=5.8)

para(
    "Three results stand out. First, the best model is a parsimonious seasonal AR specification, "
    "SARIMA(0,1,1)(1,1,0)[4], not the interim (0,1,1)(0,1,1) model. The two are close: the "
    f"two-step MASE is {float(acc_by_id['SARIMA_011_110']['MASE_h2']):.3f} versus "
    f"{float(acc_by_id['SARIMA_011_011']['MASE_h2']):.3f}. Full-sample AICc favors the "
    "interim specification (−409.2 vs −403.0), so we select on rolling MASE rather than in-sample "
    "fit. Second, models with less seasonal differencing (D = 0) are clearly worse "
    "(MASE 1.63–1.77), which supports keeping D = 1. "
    "Third, ETS is competitive but does not beat the SARIMA family "
    f"(MASE {float(acc_by_id['ETS_AAA']['MASE_h2']):.3f})."
)
para(
    "The Diebold–Mariano tests in Table 6 clarify the statistical strength of these differences. "
    "At h = 1, the interim SARIMA and the CNY-augmented model beat seasonal naive (p = 0.007 and "
    "p = 0.010), and the final (1,1,0) specification also does so at p = 0.015. At h = 2, the best "
    "SARIMA has a lower MASE than seasonal naive, but the difference is "
    "only marginally significant (p = 0.097) because two-step forecast errors are volatile and "
    "the 56 origins overlap. The best model is not significantly different from the interim "
    "SARIMA (p = 0.722), so the gain from the seasonal AR term is modest. This is an honest "
    "feature of the data, not a reason to prefer a more complicated model."
)

sel_dm = [
    ("1", "SARIMA_011_011 vs SNaive", "SARIMA(0,1,1)(0,1,1) vs seasonal naive"),
    ("1", "SARIMAX_CNY vs SNaive", "SARIMAX + CNY vs seasonal naive"),
    ("1", "SARIMAX_CNY vs SARIMA_011_011", "SARIMAX + CNY vs SARIMA(0,1,1)(0,1,1)"),
    ("2", "SARIMA_011_110 vs SNaive", "SARIMA(0,1,1)(1,1,0) vs seasonal naive"),
    ("2", "SARIMA_011_011 vs SNaive", "SARIMA(0,1,1)(0,1,1) vs seasonal naive"),
    ("2", "SARIMAX_CNY vs SARIMA_011_011", "SARIMAX + CNY vs SARIMA(0,1,1)(0,1,1)"),
    ("2", "SARIMAX_PMI vs SARIMA_011_011", "SARIMAX + PMI(−2) vs SARIMA(0,1,1)(0,1,1)"),
    ("2", "SARIMA_011_110 vs SARIMA_011_011", "SARIMA(0,1,1)(1,1,0) vs SARIMA(0,1,1)(0,1,1)"),
]
rows = [["h", "Comparison", "DM statistic", "p-value"]]
for h, key, label in sel_dm:
    r = dm_lookup.get((h, key))
    if r:
        rows.append([h, label, f"{float(r['DM_stat']):.3f}", pfmt(r["p_value"])])
    else:
        rows.append([h, label, "–", "–"])
add_table(rows, "Table 6. Selected Diebold–Mariano tests (H0 = equal expected loss; two-sided "
                "test with squared-error loss; full set in Appendix Table A2).",
          col_widths=[0.4, 3.55, 1.1, 1.0], font_size=8.8)

# ---------------------------------------------------------------------------
# 7 CNY and PMI
# ---------------------------------------------------------------------------
heading("7.  Do CNY and PMI improve forecasts?")
para(
    "Table 7 reports the covariate coefficients. They tell a familiar story: a covariate can be marginally significant "
    "without being useful for forecasting. In the SARIMAX + CNY model the CNY coefficient is "
    f"{float(cov_by[('SARIMAX_CNY', 'cny_q1_frac')]['estimate']):.3f} "
    f"(s.e. {float(cov_by[('SARIMAX_CNY', 'cny_q1_frac')]['std_error']):.3f}, "
    f"p = {pfmt(cov_by[('SARIMAX_CNY', 'cny_q1_frac')]['p_value'])}), and in the combined model it "
    f"rises to {float(cov_by[('SARIMAX_CNY_PMI', 'cny_q1_frac')]['estimate']):.3f} "
    f"(p = {pfmt(cov_by[('SARIMAX_CNY_PMI', 'cny_q1_frac')]['p_value'])}). The PMI coefficient is "
    f"small and insignificant in the PMI-only model "
    f"({float(cov_by[('SARIMAX_PMI', 'pmi_lag2')]['estimate']):.4f}, "
    f"p = {pfmt(cov_by[('SARIMAX_PMI', 'pmi_lag2')]['p_value'])}) and even smaller in the "
    f"combined model ({float(cov_by[('SARIMAX_CNY_PMI', 'pmi_lag2')]['estimate']):.4f}, "
    f"p = {pfmt(cov_by[('SARIMAX_CNY_PMI', 'pmi_lag2')]['p_value'])}). The residual Ljung–Box "
    "tests do not indicate remaining autocorrelation in these specifications."
)

model_label = {"SARIMAX_CNY": "SARIMAX + CNY",
               "SARIMAX_PMI": "SARIMAX + PMI(−2)",
               "SARIMAX_CNY_PMI": "SARIMAX + CNY + PMI(−2)",
               "SARIMAX_CNY_2005Q3": "SARIMAX + CNY, 2005Q3 start",
               "SARIMA_011_011_2005Q3": "SARIMA(0,1,1)(0,1,1), 2005Q3 start"}
term_label = {"cny_q1_frac": "CNY position", "pmi_lag2": "PMI(−2)"}
rows = [["Model", "Term", "Estimate", "S.E.", "p-value", "Ljung–Box p", "AICc"]]
for r in cov:
    if r["term"] not in term_label:
        continue
    rows.append([model_label.get(r["model"], r["model"]), term_label[r["term"]],
                 f"{float(r['estimate']):.4f}", f"{float(r['std_error']):.4f}",
                 pfmt(r["p_value"]), pfmt(r["LB8_p"]), f"{float(r['AICc']):.1f}"])
add_table(rows, "Table 7. Covariate models: coefficients and diagnostics.",
          col_widths=[1.55, 0.9, 0.8, 0.7, 0.7, 0.95, 0.7], font_size=8.2)
note("Note: estimated on the full sample. PMI models start in 2005Q3 because of the two-quarter "
     "lag; their AICc is therefore not comparable with the 1994-start models. The full coefficient "
     "table, including the ARMA terms, is in Appendix Table A4.")

para(
    "Out of sample, the covariates do not provide a robust improvement at the two-quarter horizon. The CNY model has MASE "
    f"{float(acc_by_id['SARIMAX_CNY']['MASE_h2']):.3f} versus "
    f"{float(acc_by_id['SARIMA_011_011']['MASE_h2']):.3f} for the interim SARIMA, and the "
    f"Diebold–Mariano p-value is {pfmt(dm_lookup[('2', 'SARIMAX_CNY vs SARIMA_011_011')]['p_value'])}. "
    f"The PMI model has MASE {float(acc_by_id['SARIMAX_PMI']['MASE_h2']):.3f} "
    f"(p = {pfmt(dm_lookup[('2', 'SARIMAX_PMI vs SARIMA_011_011')]['p_value'])}), and the combined "
    f"model has MASE {float(acc_by_id['SARIMAX_CNY_PMI']['MASE_h2']):.3f}. The January-dummy "
    "coding of CNY gives essentially the same result as the continuous coding. The answer to the "
    "central question is therefore negative but informative: at quarterly resolution, the CNY "
    "position changes the composition of Q1 sales without improving the Q1 total forecast enough "
    "to matter out of sample."
)
para(
    "The PMI result is also consistent with the economics. PMI is a diffusion index of "
    "manufacturing activity, while the target is a nominal retail aggregate; the two are related "
    "but not tightly linked at a two-quarter lead. The two-quarter lag is necessary for real-time "
    "feasibility, and it removes the contemporaneous correlation that might otherwise flatter the "
    "model. We therefore prefer the simpler SARIMA for the final forecast."
)

# ---------------------------------------------------------------------------
# 8 Diagnostics and final forecast
# ---------------------------------------------------------------------------
heading("8.  Diagnostics and final forecasts")
para(
    f"Figure 5 shows the residual diagnostics. The selected model is {best2['label']} estimated on 1994Q1–2026Q2. Its coefficients are "
    f"MA(1) = {float(coefs[0]['estimate']):.3f} (s.e. {float(coefs[0]['std_error']):.3f}) and "
    f"seasonal AR(1) = {float(coefs[1]['estimate']):.3f} "
    f"(s.e. {float(coefs[1]['std_error']):.3f}); both are highly significant. The residual "
    "Ljung–Box statistic is"
)
add_equation("eq_ljungbox.png", width=3.6)
para(
    f"with p = {pfmt(diag['LB8_p'])} at lag 8 and p = {pfmt(diag['LB12_p'])} at lag 12, so there "
    "is no evidence of remaining autocorrelation. A Ljung–Box test on squared residuals gives "
    f"p = {pfmt(diag['LB2_p'])}, which is borderline evidence of conditional heteroskedasticity, "
    f"and the Shapiro–Wilk test rejects normality (p < 0.001). The point forecasts are therefore "
    "well specified in the mean, but the prediction intervals should be read as approximate."
)

add_figure("fig7_residuals.png",
           "Figure 5. Residual diagnostics for SARIMA(0,1,1)(1,1,0)[4]: (A) residuals over time, "
           "(B) residual ACF, (C) residual distribution.", width=5.2)

para(
    "The final two-quarter forecast is reported in Table 8 and Figure 6. For 2026Q3 the point "
    f"forecast is {fnum(q3['point'])} (12.28 trillion CNY), with an 80% interval of "
    f"{fnum(q3['lo80'])}–{fnum(q3['hi80'])} and a 95% interval of "
    f"{fnum(q3['lo95'])}–{fnum(q3['hi95'])}. For 2026Q4 the point forecast is "
    f"{fnum(q4['point'])} (13.92 trillion CNY), with an 80% interval of "
    f"{fnum(q4['lo80'])}–{fnum(q4['hi80'])}. These imply year-on-year growth of "
    f"{yoy_q3:.1f}% and {yoy_q4:.1f}%, and a 2026 annual total of about "
    f"{annual_2026/1e4:.2f} trillion CNY ({yoy_annual:+.1f}% versus 2025)."
)

rows = [["Quarter", "Point", "80% interval", "95% interval", "y/y growth"]]
rows.append(["2026Q3", fnum(q3["point"]), f"{fnum(q3['lo80'])}–{fnum(q3['hi80'])}",
             f"{fnum(q3['lo95'])}–{fnum(q3['hi95'])}", f"{yoy_q3:+.1f}%"])
rows.append(["2026Q4", fnum(q4["point"]), f"{fnum(q4['lo80'])}–{fnum(q4['hi80'])}",
             f"{fnum(q4['lo95'])}–{fnum(q4['hi95'])}", f"{yoy_q4:+.1f}%"])
add_table(rows, "Table 8. Final forecasts from SARIMA(0,1,1)(1,1,0)[4], origin 2026Q2.",
          col_widths=[0.85, 1.15, 1.55, 1.55, 1.0], font_size=9)
note("Note: 100 million CNY. Intervals are log-normal prediction intervals with bias-adjusted "
     "point forecasts. y/y growth is relative to the same quarter of 2025.")

add_figure("fig6_fanchart.png",
           "Figure 6. Final forecast and 80%/95% intervals, 2026Q3–2028Q2, from "
           "SARIMA(0,1,1)(1,1,0)[4]. The vertical dotted line marks the forecast origin 2026Q2.",
           width=4.4)

para(
    "The fan chart shows the expected seasonal shape: Q4 is the peak, Q3 is weaker, and the "
    "intervals widen quickly beyond the two-quarter horizon. The two-quarter interval is "
    "informative enough for planning but not narrow: the 80% interval for 2026Q4 spans roughly "
    "1.9 trillion CNY. This is the appropriate message for practice. The model gives a useful "
    "central path, but users should plan around a band, not a point."
)

# ---------------------------------------------------------------------------
# 9 Discussion
# ---------------------------------------------------------------------------
heading("9.  Discussion and limitations")
para(
    "The main message is that a simple seasonal ARIMA is a credible benchmark for China's "
    "quarterly retail sales. At h = 1 it beats seasonal naive by a statistically significant "
    "margin; at h = 2 the point forecast is better but not significantly so. The rolling design "
    "matters: a single holdout can easily look better or worse, especially with COVID-19 shocks."
)
para(
    "The CNY result is a useful negative result. The monthly evidence is clear, but at quarterly "
    "resolution the holiday mainly shifts sales between January and February. A covariate that "
    "captures the timing of the holiday therefore has little room to improve the Q1 total, and it "
    "does not improve two-step forecasts. This does not mean the holiday is economically "
    "irrelevant; it means the relevant margin is within-quarter composition, not the quarterly "
    "aggregate. A monthly model with a CNY covariate would be the natural place to look for a "
    "larger effect."
)
para(
    "Several limitations remain: the target is nominal, so the forecasts mix price and quantity "
    "effects; the NBS series is revised and the 2025 census creates a comparability break; the "
    "post-2012 window has 56 origins and two COVID-19 shocks, so the Diebold–Mariano tests have "
    "limited power; residuals are non-normal with borderline ARCH, so intervals are approximate; "
    "and the model is univariate. The conclusions are for one country and one aggregate."
)
para(
    "For practice, use a parsimonious seasonal ARIMA as the baseline, update it quarterly, and "
    "communicate an interval rather than a single number; add covariates only if they survive a "
    "rolling-origin test."
)

# ---------------------------------------------------------------------------
# 10 AI use and reflection
# ---------------------------------------------------------------------------
heading("10.  AI use and reflection")
para(
    "We used AI tools for coding, debugging, data-quality checks, model comparison, and editing. "
    "It helped build the quarterly construction and rolling-origin loop, and an audit of the "
    "interim report caught three concrete problems: an incomplete-year observation in the CNY "
    "share calculation, a ten-fold unit mismatch between “亿元” and “billion”, and an incorrect "
    "description of the differenced series as white noise. We verified each correction against "
    "the raw data and reran the pipeline. We did not accept suggestions uncritically: an early "
    "draft emphasized the clear monthly CNY effect, but the rolling results did not support a "
    "quarterly gain, so we report the negative result; the AI also suggested contemporaneous PMI, "
    "which would leak future information at h = 2, and we used a two-quarter lag instead. We "
    "agreed with the bias-adjusted log-normal forecasts and the h = 1/h = 2 evaluation, and "
    "checked all final choices and numbers against the code output."
)

# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------
doc.add_page_break()
heading("References")
refs = [
    "Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. Journal of Business "
    "& Economic Statistics, 13(3), 253–263.",
    "Hyndman, R. J., & Athanasopoulos, G. (2021). Forecasting: Principles and Practice (3rd ed.). "
    "OTexts.",
    "Ljung, G. M., & Box, G. E. P. (1978). On a measure of lack of fit in time series models. "
    "Biometrika, 65(2), 297–303.",
    "National Bureau of Statistics of China. National Data — retail sales and purchasing managers "
    "index datasets. https://data.stats.gov.cn. Retrieved 28 September 2026.",
    "National Bureau of Statistics of China. (2025). Explanation of total retail sales of consumer "
    "goods and revision notes from the Fifth National Economic Census. National Data platform.",
    "Shumway, R. H., & Stoffer, D. S. (2017). Time Series Analysis and Its Applications (4th ed.). "
    "Springer.",
]
for ref in refs:
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.first_line_indent = Inches(-0.3)
    r = p.add_run(ref)
    r.font.name, r.font.size = "Times New Roman", Pt(10)

# ---------------------------------------------------------------------------
# Appendix
# ---------------------------------------------------------------------------
doc.add_page_break()
heading("Appendix: additional results")
para(
    "The appendix reports the full model-selection table, the full Diebold–Mariano set, and the "
    "robustness check that excludes COVID-affected target quarters.", size=10.5
)

rows = [["Model", "Family", "Sample start", "k", "AICc"]]
for r in sorted(sel, key=lambda x: (x["family"], x["model"])):
    rows.append([r["label"], r["family"], r["sample_start"], r["k"],
                 "–" if r["AICc"] == "" else f"{float(r['AICc']):.1f}"])
add_table(rows, "Table A1. Information criteria on the full sample.",
          col_widths=[2.6, 0.95, 0.9, 0.35, 0.8], font_size=8.4)
note("Note: AICc is computed as AIC + 2k(k+1)/(n−k−1). Benchmarks do not have a likelihood and "
     "are omitted. PMI models start in 2005Q3 and are not comparable with the 1994-start models.")

rows = [["h", "Comparison", "DM statistic", "p-value", "n"]]
for r in dm:
    rows.append([r["h"], r["Comparison"], f"{float(r['DM_stat']):.3f}",
                 pfmt(r["p_value"]), r["n"]])
add_table(rows, "Table A2. Full Diebold–Mariano tests.",
          col_widths=[0.35, 3.7, 1.0, 0.8, 0.45], font_size=8.2)

add_figure("fig8_robustness.png",
           "Figure A1. MASE at h = 2 with all target quarters and excluding COVID-affected "
           "targets (2020Q1, 2020Q2, 2022Q2).", width=6.2)

add_figure("figA2_acf_first_diff.png",
           "Figure A2. ACF after first differencing only (d = 1, D = 0). The annual spikes at "
           "lags 4, 8 and 12 remain, indicating strong seasonality.", width=5.8)

rows = [["Model", "All targets", "Non-COVID targets"]]
for r in rob:
    rows.append([r["model"], f"{float(r['All targets']):.3f}", f"{float(r['Non-COVID target']):.3f}"])
add_table(rows, "Table A3. Robustness of h = 2 MASE to COVID-affected target quarters.",
          col_widths=[2.6, 1.4, 1.4], font_size=8.6)

rows = [["Model", "Term", "Estimate", "S.E.", "t value", "p-value", "AICc"]]
for r in cov:
    rows.append([r["model"], r["term"], f"{float(r['estimate']):.4f}",
                 f"{float(r['std_error']):.4f}", f"{float(r['t_value']):.3f}",
                 pfmt(r["p_value"]), f"{float(r['AICc']):.1f}"])
add_table(rows, "Table A4. Full coefficient table for the covariate models.",
          col_widths=[1.3, 0.95, 0.8, 0.7, 0.7, 0.7, 0.7], font_size=8.2)

out = os.path.join(HERE, "FinalReport_gp12.docx")
doc.save(out)
print("saved", out)
