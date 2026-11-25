"""Render the equations used in the final report as transparent PNGs.

The report is generated with python-docx, which does not expose a convenient
native equation API.  Rendering mathtext to high-resolution images keeps the
formulas editable in this script and visually consistent with the report.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output", "equations")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "mathtext.fontset": "stix",
    "font.family": "STIXGeneral",
    "font.size": 18,
})


def render(lines, name, fontsize=19, width=9.0):
    n = len(lines)
    fig = plt.figure(figsize=(width, 0.62 * n + 0.15))
    ys = [0.5 + (n - 1 - 2 * i) * 0.16 for i in range(n)]
    for y, line in zip(ys, lines):
        fig.text(0.5, y, line, ha="center", va="center", fontsize=fontsize)
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=300, transparent=True, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print("saved", path)


render([
    r"$\phi(B)\Phi(B^{4})(1-B)^{d}(1-B^{4})^{D}\log y_t"
    r" = \theta(B)\Theta(B^{4})\varepsilon_t$"
], "eq_sarima.png")

render([
    r"$\log y_t = \beta_0 + \beta_1\,\mathrm{CNY}_{Q1,t}"
    r" + \beta_2\,\mathrm{PMI}_{t-2} + \eta_t$",
    r"$\phi(B)\Phi(B^{4})(1-B)^{d}(1-B^{4})^{D}\eta_t"
    r" = \theta(B)\Theta(B^{4})\varepsilon_t$"
], "eq_sarimax.png")

render([
    r"$\hat{y}_{T+h} = \exp\left(\hat{\mu}_{T+h}"
    r" + \frac{1}{2}\hat{\sigma}_{T+h}^{2}\right),"
    r"\qquad \left[\exp(\ell_h),\ \exp(u_h)\right]$"
], "eq_backtransform.png")

render([
    r"$\mathrm{MASE}_h = \frac{1}{N}\sum_{i=1}^{N}"
    r"\frac{\frac{1}{h}\sum_{j=1}^{h}|e_{i,j}|}"
    r"{\frac{1}{T_i-4}\sum_{t=5}^{T_i}|y_t-y_{t-4}|}$"
], "eq_mase.png", width=6.0)

render([
    r"$\Delta y_t = \alpha + \beta t + \gamma y_{t-1}"
    r" + \sum_{i=1}^{p}\delta_i\Delta y_{t-i} + \varepsilon_t$"
], "eq_adf.png")

render([
    r"$Q = n(n+2)\sum_{k=1}^{m}\frac{\hat{\rho}_k^{2}}{n-k}"
    r"\ \sim\ \chi^{2}_{m-p}$"
], "eq_ljungbox.png")

render([
    r"$DM = \frac{\bar{d}}{\sqrt{\widehat{\mathrm{Var}}(\bar{d})}},"
    r"\qquad d_t = e_{1,t}^{2}-e_{2,t}^{2}$"
], "eq_dm.png")
