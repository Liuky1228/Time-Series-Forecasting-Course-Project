"""Render the submission PDF from the optimized analysis bundle.

Requires Python 3 and ReportLab. Run after output/optimization_summary.json exists.
"""

import csv
import json
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(__file__).resolve().parents[1]
W, H = 960, 540
LEFT, RIGHT = 58, 902
BG = "#F8F6F0"
WHITE = "#FFFFFF"
INK = "#142930"
MID = "#4A6266"
LIGHT = "#C7D4D0"
TEAL = "#006E67"
LIME = "#D5EC9B"
MUTED_WHITE = "#BBCBC8"
AMBER = "#A95529"
FONT = "Helvetica"
BOLD = "Helvetica-Bold"
INC = "SARIMA_011_110"
PARENT = "SARIMA_011_011"
D0 = "SARIMA_011_101"
PMI = "SARIMAX_PMI"
CNY = "SARIMAX_CNY"
BOTH = "SARIMAX_CNY_PMI"
SNAIVE = "SNaive"
MATCH = "SARIMA_011_011_2005Q3"
MATCH_CNY = "SARIMAX_CNY_2005Q3"
BLEND = "Blend50_Incumbent_SNaive"
WALK = "WalkForward_SARIMA"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def tn(value, digits=2):
    return f"{float(value) / 10000:,.{digits}f}"


def pct(value):
    return f"{100 * float(value):.1f}%"


def mase(score):
    return f"{float(score['MASE']):.3f}"


class Slides:
    def __init__(self, path, summary):
        self.pdf = Canvas(str(path), pagesize=(W, H), invariant=1)
        self.pdf.setTitle("Forecasting China's Quarterly Retail Sales")
        self.pdf.setAuthor("STA4003 Group 12")
        self.summary = summary
        self.scores = summary["metrics"]
        self.quarters = read_csv(ROOT / "data" / "processed" / "retail_quarterly.csv")
        self.page = 0

    def text(self, x, top, value, size=20, color=INK, font=FONT, align="left"):
        x = float(x)
        value = str(value)
        extent = stringWidth(value, font, size)
        start = {"left": x, "right": x - extent, "center": x - extent / 2}[align]
        if start < LEFT - 1 or start + extent > RIGHT + 1 or not 15 < top < H - 9:
            raise ValueError(f"Slide {self.page} text exceeds margins: {value}")
        self.pdf.setFillColor(HexColor(color))
        self.pdf.setFont(font, size)
        {
            "left": self.pdf.drawString,
            "right": self.pdf.drawRightString,
            "center": self.pdf.drawCentredString,
        }[align](x, H - top, value)

    def para(self, x, top, value, width, size=20, leading=27, color=MID, font=FONT):
        line = ""
        for word in value.split():
            proposal = f"{line} {word}".strip()
            if stringWidth(proposal, font, size) > width:
                self.text(x, top, line, size, color, font)
                top += leading
                line = word
            else:
                line = proposal
        self.text(x, top, line, size, color, font)
        return top

    def line(self, x1, y1, x2, y2, color=LIGHT, weight=1, dash=()):
        self.pdf.setStrokeColor(HexColor(color))
        self.pdf.setLineWidth(weight)
        self.pdf.setDash(dash)
        self.pdf.line(x1, H - y1, x2, H - y2)
        self.pdf.setDash()

    def dot(self, x, y, radius=5, color=TEAL):
        self.pdf.setFillColor(HexColor(color))
        self.pdf.circle(x, H - y, radius, fill=1, stroke=0)

    def start(self, title=None, intro=None, dark=False):
        self.page += 1
        background, foreground = (INK, WHITE) if dark else (BG, INK)
        self.pdf.setFillColor(HexColor(background))
        self.pdf.rect(0, 0, W, H, fill=1, stroke=0)
        if title:
            self.text(LEFT, 87, title, 40, foreground, BOLD)
        if intro:
            self.text(LEFT, 123, intro, 19, MUTED_WHITE if dark else MID)

    def end(self, source, dark=False):
        color = MUTED_WHITE if dark else MID
        self.line(LEFT, 489, RIGHT, 489, MID if dark else LIGHT)
        self.text(LEFT, 513, source, 12, color)
        self.text(RIGHT, 513, f"{self.page} / 8", 12, color, align="right")
        self.pdf.showPage()

    def score(self, model, group="all", horizon=2):
        if horizon == 2:
            return self.scores[model][group]
        return self.summary["h1"][model]

    def interval(self, model, nominal, horizon=2, period="All targets"):
        return next(
            row for row in self.summary["intervals"]
            if row["model"] == model and row["h"] == horizon
            and row["nominal"] == nominal / 100 and row["period"] == period
        )

    def cover(self):
        self.start(dark=True)
        self.text(LEFT, 92, "STA4003  /  GROUP 12", 17, LIME, BOLD)
        self.text(LEFT, 190, "Forecasting China's", 68, WHITE, BOLD)
        self.text(LEFT, 265, "quarterly retail sales", 68, WHITE, BOLD)
        self.line(LEFT, 310, 188, 310, LIME, 2)
        self.para(
            LEFT, 369,
            "Does Lunar New Year timing improve forecasts one or two quarters ahead?",
            660, 29, 36, MUTED_WHITE,
        )
        self.end("Time Series Analysis  /  Fall 2026", dark=True)

    def data(self):
        self.start(
            "Growth, seasonality and shocks",
            f"NBS quarterly retail sales  |  {self.quarters[0]['quarter']} to "
            f"{self.quarters[-1]['quarter']}  |  {len(self.quarters)} observations",
        )
        x0, x1, y0, y1 = 111, 570, 423, 198

        def x(i):
            return x0 + i * (x1 - x0) / (len(self.quarters) - 1)

        def y(v):
            return y0 + (y1 - y0) * v / 14

        self.text(LEFT, 173, "Quarterly sales, CNY trillion", 16, MID, BOLD)
        for tick in (0, 4, 8, 12):
            self.line(x0, y(tick), x1, y(tick))
            self.text(100, y(tick) + 5, tick, 13, MID, align="right")
        for year in (1994, 2002, 2010, 2018, 2026):
            self.text(x(4 * (year - 1994)), 451, year, 13, MID, align="center")
        values = [float(row["value_bn"]) / 10000 for row in self.quarters]
        path = self.pdf.beginPath()
        path.moveTo(x(0), H - y(values[0]))
        for i, value in enumerate(values[1:], 1):
            path.lineTo(x(i), H - y(value))
        self.pdf.setStrokeColor(HexColor(TEAL))
        self.pdf.setLineWidth(2)
        self.pdf.drawPath(path, stroke=1)
        for year, quarter in ((2020, 1), (2022, 2)):
            i = 4 * (year - 1994) + quarter - 1
            self.dot(x(i), y(values[i]), 4.5, AMBER)
        self.text(410, 322, "2020Q1 / 2022Q2", 13, AMBER)
        self.line(595, 166, 595, 450)
        full_years = [values[i:i + 4] for i in range(0, len(values) - 3, 4)]
        q4_share = 100 * sum(v[3] / sum(v) for v in full_years) / len(full_years)
        q4_peaks = sum(v[3] == max(v) for v in full_years)
        self.text(625, 222, f"{q4_share:.1f}%", 49, TEAL, BOLD)
        self.para(625, 254, "Mean Q4 share of annual retail sales.", 258, 18, 23)
        self.para(
            625, 319,
            f"Q4 was the peak in {q4_peaks} of {len(full_years)} complete years.", 258, 18, 23,
        )
        self.para(
            625, 386,
            "Since 2012, Q1 uses the published Jan-Feb total plus March.", 258, 18, 23,
        )
        self.end("Source  NBS National Data and Group 12 quarterly reconstruction")

    def design(self):
        self.start(
            "Differencing and forecast design",
            "Quarterly period = 4. Errors are evaluated in original sales units.",
        )
        columns = [
            (LEFT, "Model the log series",
             "Logs reduce scale changes as retail grows. ACF and stationarity tests inform the candidate set.",
             "Compare seasonal differencing with a fixed D = 0 SARIMA that uses seasonal AR and MA terms."),
            (496, "Move the origin forward",
             "Refit each candidate on the expanding history at each origin from 2012Q1 to 2025Q4.",
             "Score the same 56 origins at each horizon. The two-quarter horizon drives the final choice."),
        ]
        for x, heading, first, second in columns:
            self.text(x, 193, heading, 27, TEAL, BOLD)
            self.line(x, 213, x + 404, 213)
            self.para(x, 253, first, 386, 21, 28)
            self.para(x, 348, second, 386, 21, 28)
        self.text(LEFT, 453, "Seasonal naive repeats the same quarter from the previous year.", 18, INK)
        self.end("MASE scales each absolute error by that origin's common training seasonal-naive error")

    def points(self):
        self.start(
            "Two-quarter point accuracy",
            "Expanding-window MASE on the same targets. Lower is better.",
        )
        rows = [
            (INC, "SARIMA(0,1,1)(1,1,0)[4]"),
            (D0, "Fixed D = 0 SARIMA"),
            (PARENT, "SARIMA parent for covariates"),
            ("ETS_AAA", "Damped seasonal ETS"),
            (SNAIVE, "Seasonal naive"),
        ]
        self.text(LEFT, 172, "Fixed candidate", 15, MID, BOLD)
        self.text(428, 172, "h = 1", 15, MID, BOLD, "right")
        self.text(524, 172, "h = 2", 15, MID, BOLD, "right")
        self.line(LEFT, 185, 524, 185, MID)
        best = {
            h: min(rows, key=lambda row: self.score(row[0], horizon=h)["MASE"])[0]
            for h in (1, 2)
        }
        for i, (model, label) in enumerate(rows):
            y = 217 + i * 48
            color = TEAL if model == INC else INK
            weight = BOLD if model == INC else FONT
            self.text(LEFT, y, label, 20, color, weight)
            for h, x in ((1, 428), (2, 524)):
                color = TEAL if model == best[h] else INK
                weight = BOLD if model == best[h] else FONT
                self.text(x, y, mase(self.score(model, horizon=h)), 20, color, weight, "right")
            self.line(LEFT, y + 14, 524, y + 14)
        self.line(558, 163, 558, 448)
        self.text(586, 187, "Why retain the incumbent?", 23, TEAL, BOLD)
        walk = mase(self.score(WALK))
        inc_rmse = tn(self.score(INC)["RMSE"], 4)
        d0_rmse = tn(self.score(D0)["RMSE"], 4)
        self.para(
            586, 224,
            f"Lowest historical h = 2 MASE. Two-step RMSE is {inc_rmse} tn vs {d0_rmse} tn (D=0).",
            316, 18, 23,
        )
        self.para(
            586, 319,
            f"A selector using only realized h = 2 errors scores {walk}. Both comparisons are retrospective.",
            316, 18, 23,
        )
        dm = self.summary["dm"]["h2"]
        self.text(LEFT, 454, f"Incumbent vs seasonal naive  |  Squared-loss DM p = {float(dm):.3f} (h = 2, not significant at 5%)",
                  16, MID)
        self.end("Fixed D = 0  SARIMA(0,1,1)(1,0,1)[4]  |  Covariate parent  SARIMA(0,1,1)(0,1,1)[4]")

    def covariates(self):
        self.start(
            "CNY timing and lagged PMI",
            "Calendar effects can concentrate in Q1. PMI also shortens the usable training history.",
        )
        n_q1 = int(self.score(PARENT, "Q1")["n"])
        self.text(LEFT, 174, "CNY  /  Full-history parent", 23, TEAL, BOLD)
        self.text(498, 174, "PMI  /  Matched 2005Q3 start", 23, TEAL, BOLD)
        self.line(470, 154, 470, 397)
        tables = [
            (LEFT, 436, [
                ("No CNY", self.score(PARENT), self.score(PARENT, "Q1")),
                ("With CNY", self.score(CNY), self.score(CNY, "Q1")),
            ], ("All", f"Q1 (n={n_q1})")),
            (498, RIGHT, [
                ("No CNY", self.score(MATCH), self.score(PMI)),
                ("With CNY", self.score(MATCH_CNY), self.score(BOTH)),
            ], ("No PMI", "With PMI")),
        ]
        for x0, x1, rows, (left_label, right_label) in tables:
            self.text(x1 - 107, 217, left_label, 15, MID, BOLD, "right")
            self.text(x1, 217, right_label, 15, MID, BOLD, "right")
            self.line(x0, 231, x1, 231, MID)
            for i, (label, first, second) in enumerate(rows):
                y = 271 + 52 * i
                self.text(x0, y, label, 21)
                self.text(x1 - 107, y, mase(first), 21, INK, BOLD, "right")
                self.text(x1, y, mase(second), 21, INK, BOLD, "right")
                self.line(x0, y + 15, x1, y + 15)
        self.para(
            LEFT, 379, "On Q1 targets, CNY raises MAE but lowers RMSE in this SARIMA parent.", 385, 18, 24,
        )
        self.para(
            498, 379, "Each pair uses the same SARIMA order, training start and target quarters.", 398, 18, 24,
        )
        self.text(LEFT, 454, "PMI is aligned by quarter index. Historical release dates and data vintages were not reconstructed.", 16)
        self.end("All cells show h = 2 MASE  |  PMI columns use all target quarters")

    def intervals(self):
        self.start(
            "Residual checks and prediction intervals",
            "Observed coverage over 56 targets. The interval labels show nominal levels.",
        )
        headings = [
            (LEFT, "Model"), (312, "Horizon"), (410, "80% PI"), (514, "95% PI"),
            (708, "95% mean width"), (RIGHT, "95% Winkler"),
        ]
        for x, label in headings:
            self.text(x, 175, label, 15, MID, BOLD, "left" if x == LEFT else "right")
        self.line(LEFT, 188, RIGHT, 188, MID)
        rows = [(INC, "Incumbent", 1), (INC, "Incumbent", 2), (SNAIVE, "Seasonal naive", 2)]
        for i, (model, label, h) in enumerate(rows):
            y = 229 + i * 59
            ci80 = self.interval(model, 80, h)
            ci95 = self.interval(model, 95, h)
            color = TEAL if model == INC else INK
            self.text(LEFT, y, label, 23, color, BOLD)
            self.text(312, y, f"h = {h}", 20, color, FONT, "right")
            self.text(410, y, pct(ci80["coverage"]), 22, color, BOLD, "right")
            self.text(514, y, pct(ci95["coverage"]), 22, color, BOLD, "right")
            self.text(708, y, tn(ci95["width"]) + " tn", 20, color, FONT, "right")
            self.text(RIGHT, y, tn(ci95["score"]) + " tn", 20, color, FONT, "right")
            self.line(LEFT, y + 18, RIGHT, y + 18)
        later = self.interval(INC, 95, period="2020-2022")
        observed = round(float(later["coverage"])*int(later["n"]))
        diag = self.summary["diagnostics"]
        self.text(
            LEFT, 422,
            f"All five h = 2 misses of the 95% interval occurred in 2020-2022 ({observed}/{later['n']} covered).",
            17, INK,
        )
        self.text(LEFT, 452, f"Residual checks: Ljung-Box lag 8 p = {float(diag['LB8_p']):.3f}"
                  f"  |  Shapiro-Wilk p = {float(diag['Shapiro_p']):.2e}", 17, MID)
        self.end("Coverage across all targets  |  Width and Winkler score in CNY trillion")

    def forecast(self):
        q3, q4 = sorted(self.summary["forecasts"], key=lambda row: row["quarter"])
        official = self.summary["q3_actual"]
        actual = float(official["actual"])
        relative_error = 100 * (float(q3["point"]) / actual - 1)
        direction = "above" if relative_error >= 0 else "below"
        inside = "inside" if float(q3["lo80"]) <= actual <= float(q3["hi80"]) else "outside"
        self.start(
            "Forecasts at the 2026Q2 cutoff",
            "Historical origin  |  SARIMA(0,1,1)(1,1,0)[4]  |  CNY trillion",
        )
        for x, label in ((LEFT, "Quarter"), (340, "Point forecast"), (600, "80% PI"),
                         (RIGHT, "95% PI")):
            self.text(x, 181, label, 17, MID, BOLD, "left" if x == LEFT else "right")
        self.line(LEFT, 201, RIGHT, 201, MID)
        for i, row in enumerate((q3, q4)):
            y = 263 + i * 83
            self.text(LEFT, y, row["quarter"], 29, INK, BOLD)
            self.text(340, y, tn(row["point"]), 38, TEAL, BOLD, "right")
            self.text(600, y, f"{tn(row['lo80'])} to {tn(row['hi80'])}", 24, INK, FONT, "right")
            self.text(RIGHT, y, f"{tn(row['lo95'])} to {tn(row['hi95'])}", 24, INK, FONT, "right")
            self.line(LEFT, y + 21, RIGHT, y + 21)
        self.text(LEFT, 407, f"Later 2026Q3 actual  {tn(actual, 4)} tn", 24, TEAL, BOLD)
        self.text(LEFT, 450, f"The Q3 forecast was {abs(relative_error):.2f}% {direction} the actual. "
                  f"The actual was {inside} the 80% interval.", 19, INK)
        self.end("Q3 actual  NBS Jan-Sep less Jan-Jun  |  19 Oct 2026 release predates the November archive")

    def conclusion(self):
        blend = mase(self.score(BLEND))
        incumbent = mase(self.score(INC))
        self.start("Conclusions and limits", dark=True)
        rows = [
            ("Forecast choice",
             f"The incumbent scored {incumbent} at h = 2. "
             f"The 50/50 blend with seasonal naive scored {blend}."),
            ("Covariates",
             "No consistent h = 2 gain from CNY in the tested parent. "
             "PMI raises h = 2 MASE in both matched comparisons."),
            ("Evidence limits",
             "Published data revisions and pandemic shocks matter. The retrospective comparisons and one "
             "later Q3 observation leave future performance uncertain."),
        ]
        for i, (label, body) in enumerate(rows):
            y = 166 + i * 107
            self.text(LEFT, y, label, 23, LIME, BOLD)
            self.para(303, y, body, 599, 21, 29, WHITE)
            if i < 2:
                self.line(LEFT, y + 72, RIGHT, y + 72, MID)
        self.end("Primary horizon  Two quarters ahead", dark=True)

    def build(self):
        for render in (
            self.cover, self.data, self.design, self.points, self.covariates,
            self.intervals, self.forecast, self.conclusion,
        ):
            render()
        self.pdf.save()


def main():
    summary_path = ROOT / "output" / "optimization_summary.json"
    with summary_path.open(encoding="utf-8-sig") as handle:
        summary = json.load(handle)
    Slides(ROOT / "Presentation_gp12.pdf", summary).build()


if __name__ == "__main__":
    main()
