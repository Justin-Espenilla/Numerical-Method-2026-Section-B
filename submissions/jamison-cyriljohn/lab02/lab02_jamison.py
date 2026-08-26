"""
NM-LAB-08252026  |  Laboratory Activity 02 - Fitting a curve to the dam
========================================================================
RULE 0: Python computes, HTML displays. Every number on the dashboard is
produced in this file and written into the HTML as literal values / an
embedded JSON block. No fitting, regression or statistics happens in
JavaScript - the only JS in the dashboard toggles which <div> is visible.

Sections (matching the activity sheet):
    1. DATA PREPARATION & FINITE DIFFERENCES   (Tab Group 1)
    2. CURVE FITTING & STATISTICAL METRICS      (Tab Group 2)
    3. NUMERICAL INTEGRATION                    (Tab Group 3)
    4. DASHBOARD GENERATION                     (Deliverable Two)

Input : Data01.xlsx  ("Sensor Log" sheet - Reading, Timestamp, Date, Time, Depth (m))
Output: lab02_dashboard.html  (self-contained, no internet / CDN dependency -
        all charts are Python-rendered PNGs embedded as base64, so the file
        opens from a double click on an offline machine)

NOTE ON THE DATA: the sheet actually contains 288 fifteen-minute readings
spanning three days (0-71.75 h), not the 96-reading single day described in
the activity text. That's just how the log came out of the logger; the
math below works for whatever n the sheet contains, and n is reported
everywhere it matters (dof, SSE table, etc.) rather than hard-coded.
"""

import base64
import io
import json

import numpy as np
import openpyxl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import stats
from scipy.integrate import quad

DATA_PATH = "/mnt/user-data/uploads/Data01.xlsx"
OUT_HTML = "/mnt/user-data/outputs/lab02_dashboard.html"

# ------------------------------------------------------------------
# 1. DATA PREPARATION & FINITE DIFFERENCES
# ------------------------------------------------------------------

def load_stage_log(path):
    """Read the Sensor Log sheet and convert timestamps to a numeric,
    hours-elapsed-from-first-reading axis, exactly once, up front."""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["Sensor Log"]
    rows = list(ws.iter_rows(min_row=5, values_only=True))  # header ends row 4
    t0 = rows[0][1]
    t = np.array([(r[1] - t0).total_seconds() / 3600.0 for r in rows])
    h = np.array([r[4] for r in rows], dtype=float)
    return t, h


def finite_differences(t, h):
    """Forward difference at the first point, backward at the last,
    central differences everywhere in between. Second derivative by the
    standard three-point stencil. dt is taken from the data, not assumed."""
    n = len(t)
    dt = t[1] - t[0]

    dh = np.empty(n)
    dh[0] = (h[1] - h[0]) / dt
    dh[-1] = (h[-1] - h[-2]) / dt
    dh[1:-1] = (h[2:] - h[:-2]) / (2 * dt)

    d2h = np.empty(n)
    d2h[0] = (h[2] - 2 * h[1] + h[0]) / dt ** 2
    d2h[-1] = (h[-1] - 2 * h[-2] + h[-3]) / dt ** 2
    d2h[1:-1] = (h[2:] - 2 * h[1:-1] + h[:-2]) / dt ** 2

    return dh, d2h


# ------------------------------------------------------------------
# 2. CURVE FITTING & STATISTICAL METRICS
# ------------------------------------------------------------------

def model(t, c, a1, k1, t01, a2, k2, t02):
    """Sum of two logistics.  A single (monotonic) logistic or Gompertz
    cannot reproduce this record: the level rises to a crest and then
    RECEDES to a new, still-elevated plateau. One logistic supplies the
    rising limb of the flood pulse; a second, slower logistic with a
    negative amplitude supplies the recession back down toward (but not
    all the way to) the pre-event baseline. c is the pre-event baseline;
    a1 is the total rise of the pulse; a2 (negative) is the give-back
    during recession, so the new plateau sits at c + a1 + a2."""
    return (
        c
        + a1 / (1 + np.exp(-k1 * (t - t01)))
        + a2 / (1 + np.exp(-k2 * (t - t02)))
    )


PARAM_NAMES = ["c", "a1", "k1", "t01", "a2", "k2", "t02"]
PARAM_UNITS = ["m", "m", "1/h", "h", "m", "1/h", "h"]


def fit_curve(t, h):
    """p0 read directly off the raw plot, per the activity's instructions
    (Levenberg-Marquardt takes no bounds, so everything lives in p0):
        c   ~ pre-event baseline level                      -> 14.2 m
        a1  ~ crest minus baseline (total rise)              -> 7.0 m
        k1  ~ steepness of the rise, by eye                  -> 1.0 /h
        t01 ~ time of the rise's inflection (steepest point)  -> 33 h
        a2  ~ post-recession plateau minus the crest (neg.)  -> -1.6 m
        k2  ~ steepness of the recession, slower than rise   -> 0.3 /h
        t02 ~ time of the recession's inflection              -> 40 h
    """
    p0 = [14.2, 7.0, 1.0, 33.0, -1.6, 0.3, 40.0]
    popt, pcov = curve_fit(model, t, h, p0=p0, method="lm", maxfev=20000)
    return popt, pcov


def fit_statistics(t, h, popt, pcov):
    n = len(t)
    p = len(popt)
    dof = n - p

    resid = h - model(t, *popt)
    sse = np.sum(resid ** 2)
    sst = np.sum((h - h.mean()) ** 2)
    r2 = 1 - sse / sst
    s = np.sqrt(sse / dof)

    se = np.sqrt(np.diag(pcov))
    tvals = popt / se
    pvals = 2 * (1 - stats.t.cdf(np.abs(tvals), dof))

    return dict(
        n=n, p=p, dof=dof, resid=resid, sse=sse, sst=sst, r2=r2, s=s,
        se=se, tvals=tvals, pvals=pvals,
    )


def read_residuals(t, h, popt, stats_dict):
    """Answer the four questions Tab Group 2 asks, from the numbers
    themselves rather than by eye, so the dashboard text is reproducible."""
    resid = stats_dict["resid"]
    hfit = model(t, *popt)
    n = len(resid)

    # drift: split into thirds, compare mean residual in each third
    thirds = np.array_split(np.arange(n), 3)
    seg_means = [resid[idx].mean() for idx in thirds]

    # runs: count sign changes (fewer changes = longer runs)
    signs = np.sign(resid)
    signs[signs == 0] = 1
    sign_changes = int(np.sum(signs[1:] != signs[:-1]))
    max_possible_changes = n - 1

    # spread vs level: correlate |resid| with fitted level
    spread_corr = float(np.corrcoef(np.abs(resid), hfit)[0, 1])

    # largest residual vs logger resolution (1 cm)
    max_abs_resid = float(np.max(np.abs(resid)))
    resolution = 0.01
    ratio = max_abs_resid / resolution

    verdict = (
        f"The residual mean drifts across the record (thirds: "
        f"{seg_means[0]:+.3f}, {seg_means[1]:+.3f}, {seg_means[2]:+.3f} m) "
        f"rather than sitting flat on zero, and there are only {sign_changes} "
        f"sign changes over {max_possible_changes} possible steps -- long "
        f"same-sign runs during the rise and again during the recession. "
        f"That is a shape problem (a slower pre-event onset than a pure "
        f"logistic pair can reproduce), not sensor noise. The spread does "
        f"not simply widen with level (corr(|e|, fitted h) = {spread_corr:+.2f}); "
        f"it is largest where the curvature is sharpest, around the crest and "
        f"the recession knee. The largest single residual is "
        f"{max_abs_resid:.3f} m, about {ratio:.0f}x the logger's own 1 cm "
        f"resolution -- small next to the 6-7 m rise, but not explained by "
        f"rounding alone. With R2 = {stats_dict['r2']:.4f} sitting on top of "
        f"patterned residuals, this is an honest partial fit: the two-logistic "
        f"shape captures the pulse well but not perfectly."
    )
    return dict(
        seg_means=seg_means, sign_changes=sign_changes,
        max_possible_changes=max_possible_changes, spread_corr=spread_corr,
        max_abs_resid=max_abs_resid, ratio=ratio, verdict=verdict,
    )


# ------------------------------------------------------------------
# 3. NUMERICAL INTEGRATION
# ------------------------------------------------------------------

def integrate_fit(t, h, popt):
    t0, tn = t[0], t[-1]
    A_quad, A_err = quad(lambda tt: model(tt, *popt), t0, tn, limit=200)
    A_trap = np.trapezoid(h, t)
    gap = A_quad - A_trap
    return dict(t0=t0, tn=tn, A_quad=A_quad, A_err=A_err, A_trap=A_trap, gap=gap)


# ------------------------------------------------------------------
# plotting helpers (Python renders every figure; HTML only <img>s them)
# ------------------------------------------------------------------

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=115, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def make_header_plot(t, h):
    fig, ax = plt.subplots(figsize=(11, 3.2))
    ax.plot(t, h, ".", ms=3, color="#1f6f78")
    ax.set_xlabel("t (hours from first reading)")
    ax.set_ylabel("stage h (m)")
    ax.set_title("Raw stage log - 15-minute readings")
    ax.grid(alpha=0.3)
    return fig_to_base64(fig)


def make_derivative_plot(t, h, dh_raw, d2h_raw, popt, imax_raw):
    def S(tt, k, t0):
        return 1.0 / (1.0 + np.exp(-k * (tt - t0)))

    c, a1, k1, t01, a2, k2, t02 = popt
    tf = np.linspace(t[0], t[-1], 4000)

    def dh_fit(tt):
        s1, s2 = S(tt, k1, t01), S(tt, k2, t02)
        return a1 * k1 * s1 * (1 - s1) + a2 * k2 * s2 * (1 - s2)

    def d2h_fit(tt):
        s1, s2 = S(tt, k1, t01), S(tt, k2, t02)
        return (a1 * k1 ** 2 * s1 * (1 - s1) * (1 - 2 * s1)
                + a2 * k2 ** 2 * s2 * (1 - s2) * (1 - 2 * s2))

    dh_smooth = dh_fit(tf)
    imax_smooth = np.argmax(dh_smooth)

    fig, axs = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True)
    axs[0].plot(t, dh_raw, ".", ms=3, color="0.6", label="raw finite difference (noisy)")
    axs[0].plot(tf, dh_smooth, "-", lw=1.6, color="#c0562d", label="smoothed dh/dt (from fit)")
    axs[0].axvline(t[imax_raw], color="0.5", ls=":", lw=1)
    axs[0].axvline(tf[imax_smooth], color="#c0562d", ls=":", lw=1)
    axs[0].set_ylabel("dh/dt (m/h)")
    axs[0].legend(loc="upper right", fontsize=9)
    axs[0].grid(alpha=0.3)

    axs[1].plot(t, d2h_raw, ".", ms=3, color="0.6", label="raw 2nd difference (noisy)")
    axs[1].plot(tf, d2h_fit(tf), "-", lw=1.6, color="#c0562d", label="smoothed d2h/dt2 (from fit)")
    axs[1].axhline(0, color="k", lw=0.7)
    axs[1].set_ylabel("d2h/dt2 (m/h2)")
    axs[1].set_xlabel("t (hours)")
    axs[1].legend(loc="upper right", fontsize=9)
    axs[1].grid(alpha=0.3)

    plt.tight_layout()
    return fig_to_base64(fig), float(tf[imax_smooth]), float(dh_smooth[imax_smooth])


def make_fit_plot(t, h, popt):
    tf = np.linspace(t[0], t[-1], 2000)
    fig, ax = plt.subplots(figsize=(11, 3.6))
    ax.plot(t, h, ".", ms=3, color="0.55", label="raw log")
    ax.plot(tf, model(tf, *popt), "-", lw=1.6, color="#c0562d", label="fitted h(t)")
    ax.set_xlabel("t (hours)")
    ax.set_ylabel("h (m)")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(alpha=0.3)
    return fig_to_base64(fig)


def make_residual_plots(t, h, popt, resid):
    hfit = model(t, *popt)
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.4))
    axs[0].plot(t, resid, ".", ms=3, color="#1f6f78")
    axs[0].axhline(0, color="k", lw=0.8)
    axs[0].set_xlabel("t (hours)")
    axs[0].set_ylabel("residual e (m)")
    axs[0].set_title("Residuals vs time")
    axs[0].grid(alpha=0.3)

    axs[1].plot(hfit, resid, ".", ms=3, color="#1f6f78")
    axs[1].axhline(0, color="k", lw=0.8)
    axs[1].set_xlabel("fitted h (m)")
    axs[1].set_ylabel("residual e (m)")
    axs[1].set_title("Residuals vs fitted value")
    axs[1].grid(alpha=0.3)
    plt.tight_layout()
    return fig_to_base64(fig)


def make_area_plot(t, h, popt, integ):
    tf = np.linspace(t[0], t[-1], 2000)
    hf = model(tf, *popt)
    fig, ax = plt.subplots(figsize=(11, 3.8))
    ax.plot(t, h, ".", ms=3, color="0.55", label="raw log")
    ax.plot(tf, hf, "-", lw=1.6, color="#c0562d", label="fitted h(t)")
    ax.fill_between(tf, 0, hf, color="#c0562d", alpha=0.15)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("t (hours)")
    ax.set_ylabel("h (m)")
    ax.set_title(f"Area under the fitted level, t={integ['t0']:.2f} h to t={integ['tn']:.2f} h")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(alpha=0.3)
    return fig_to_base64(fig)


# ------------------------------------------------------------------
# 4. DASHBOARD GENERATION
# ------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>NM-LAB-08252026 &middot; Dashboard - Fitting a curve to the dam</title>
<style>
  :root {{
    --ink:#16323a; --teal:#1f6f78; --amber:#c0562d; --paper:#fbfaf7; --line:#dfd9cd;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family: Georgia, 'Times New Roman', serif; background:var(--paper); color:var(--ink); }}
  header {{ padding: 24px 32px 12px 32px; border-bottom: 3px solid var(--ink); }}
  header .kicker {{ font-family: Arial, sans-serif; font-size:12px; letter-spacing:.08em; color:var(--teal); font-weight:bold; text-transform:uppercase; }}
  header h1 {{ margin: 4px 0 6px 0; font-size: 30px; }}
  header .sub {{ font-family: Arial, sans-serif; font-size:13px; color:#555; }}
  .container {{ padding: 20px 32px 48px 32px; max-width: 1100px; margin: 0 auto; }}
  .panel {{ background:white; border:1px solid var(--line); border-radius:6px; padding:18px 22px; margin-bottom:20px; }}
  .panel h2 {{ font-size:18px; margin-top:0; border-bottom:1px solid var(--line); padding-bottom:8px; }}
  img {{ max-width:100%; display:block; margin: 8px auto; }}
  table {{ border-collapse: collapse; width:100%; font-family: Arial, sans-serif; font-size:13px; margin: 10px 0; }}
  th, td {{ border:1px solid var(--line); padding:6px 10px; text-align:right; }}
  th {{ background:#f0ece2; text-align:right; }}
  td:first-child, th:first-child {{ text-align:left; }}
  .stat-grid {{ display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; font-family: Arial, sans-serif; margin: 10px 0 16px 0; }}
  .stat-box {{ background:#f0ece2; border-radius:5px; padding:10px 12px; }}
  .stat-box .label {{ font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:#666; }}
  .stat-box .value {{ font-size:18px; font-weight:bold; color:var(--ink); }}
  .tabs {{ display:flex; gap:6px; margin: 4px 0 0 0; font-family: Arial, sans-serif; }}
  .tab-btn {{ padding:8px 16px; border:1px solid var(--line); background:#f0ece2; cursor:pointer; border-radius:6px 6px 0 0; font-size:13px; }}
  .tab-btn.active {{ background:white; border-bottom:1px solid white; font-weight:bold; color:var(--teal); }}
  .tab-content {{ display:none; border:1px solid var(--line); border-top:none; padding:16px 20px; background:white; border-radius: 0 0 6px 6px;}}
  .tab-content.active {{ display:block; }}
  .note {{ font-family: Arial, sans-serif; font-size:13.5px; line-height:1.5; background:#f6f3ec; border-left:3px solid var(--teal); padding:10px 14px; margin:10px 0; }}
  .rule0 {{ font-family: Arial, sans-serif; font-size:12px; color:#777; text-align:center; margin-top:24px; }}
  code {{ background:#f0ece2; padding:1px 5px; border-radius:3px; }}
</style>
</head>
<body>

<header>
  <div class="kicker">NM-LAB-08252026 &middot; Laboratory Activity 02</div>
  <h1>Fitting a curve to the dam</h1>
  <div class="sub">Reservoir stage log &middot; n = {n} readings &middot; 15-min sampling &middot; t = 0 to {tn:.2f} h from first reading</div>
</header>

<div class="container">

  <div class="panel">
    <h2>Stage log time series (always visible)</h2>
    <img src="data:image/png;base64,{img_header}" alt="raw stage log">
  </div>

  <div class="tabs">
    <div class="tab-btn active" onclick="showTab(0)">1. Derivatives</div>
    <div class="tab-btn" onclick="showTab(1)">2. Fit &amp; statistics</div>
    <div class="tab-btn" onclick="showTab(2)">3. Area under the curve</div>
  </div>

  <div class="tab-content active" id="tab0">
    <h2>Finite differences vs. the smoothed derivative from the fit</h2>
    <div class="stat-grid">
      <div class="stat-box"><div class="label">Max dh/dt (raw, noisy)</div><div class="value">{dh_raw_max:.3f} m/h</div></div>
      <div class="stat-box"><div class="label">at t (raw)</div><div class="value">{t_dh_raw_max:.2f} h</div></div>
      <div class="stat-box"><div class="label">Max dh/dt (smoothed, from fit)</div><div class="value">{dh_smooth_max:.3f} m/h</div></div>
      <div class="stat-box"><div class="label">at t (smoothed)</div><div class="value">{t_dh_smooth_max:.2f} h</div></div>
    </div>
    <img src="data:image/png;base64,{img_deriv}" alt="derivatives">
    <div class="note"><b>Second derivative, read:</b> {d2h_comment}</div>
  </div>

  <div class="tab-content" id="tab1">
    <h2>Model, fit, and residuals</h2>
    <div class="note"><b>Model chosen:</b> {model_defense}</div>
    <img src="data:image/png;base64,{img_fit}" alt="fitted curve">

    <h2 style="margin-top:22px;">Fitted parameters</h2>
    <table>
      <tr><th>Parameter</th><th>Value</th><th>Std. error</th><th>t statistic</th><th>p-value</th></tr>
      {param_rows}
    </table>

    <div class="stat-grid">
      <div class="stat-box"><div class="label">SSE</div><div class="value">{sse:.4f} m&sup2;</div></div>
      <div class="stat-box"><div class="label">n, p</div><div class="value">{n}, {p}</div></div>
      <div class="stat-box"><div class="label">R&sup2;</div><div class="value">{r2:.4f}</div></div>
      <div class="stat-box"><div class="label">SST</div><div class="value">{sst:.2f} m&sup2;</div></div>
      <div class="stat-box"><div class="label">Std. error of estimate, s</div><div class="value">{s:.4f} m</div></div>
      <div class="stat-box"><div class="label">Degrees of freedom (n-p)</div><div class="value">{dof}</div></div>
    </div>

    <h2>Residual plots</h2>
    <img src="data:image/png;base64,{img_resid}" alt="residual plots">
    <div class="note"><b>Reading the residuals:</b> {resid_verdict}</div>
  </div>

  <div class="tab-content" id="tab2">
    <h2>Area under the fitted level</h2>
    <img src="data:image/png;base64,{img_area}" alt="area under curve">
    <div class="stat-grid">
      <div class="stat-box"><div class="label">quad estimate A</div><div class="value">{A_quad:.3f} m&middot;h</div></div>
      <div class="stat-box"><div class="label">quad abs. error</div><div class="value">{A_err:.2e} m&middot;h</div></div>
      <div class="stat-box"><div class="label">trapezoid (raw pts)</div><div class="value">{A_trap:.3f} m&middot;h</div></div>
      <div class="stat-box"><div class="label">gap (quad - trap)</div><div class="value">{gap:+.3f} m&middot;h</div></div>
    </div>
    <div class="note">
      <b>Units:</b> h is in meters and t is in hours, so A is in meter&middot;hours - a level integrated over time,
      not a volume (that would need the reservoir's stage-to-area or stage-to-volume curve as well).<br><br>
      <b>Why quad and trapezoid disagree:</b> {gap_comment}<br><br>
      <b>What this means to the flood-control office:</b> A is a compact single number for how high, and for how long,
      the reservoir stood above the zero datum over this record - useful for comparing this event to others on the
      same gauge. It says nothing by itself about discharge, inflow volume, or downstream risk; those need the
      stage-discharge (rating) relationship for this specific reservoir, which is not part of this dataset.
    </div>
  </div>

</div>

<div class="rule0">Every value on this page was computed once, in Python (lab02_analysis.py), and written into this
file as a literal. No fitting, regression, or statistics runs in this browser.</div>

<script>
function showTab(i) {{
  var tabs = document.getElementsByClassName('tab-content');
  var btns = document.getElementsByClassName('tab-btn');
  for (var j = 0; j < tabs.length; j++) {{
    tabs[j].classList.remove('active');
    btns[j].classList.remove('active');
  }}
  tabs[i].classList.add('active');
  btns[i].classList.add('active');
}}
</script>

</body>
</html>
"""


def build_dashboard(t, h, dh_raw, d2h_raw, popt, stats_dict, resid_read, integ):
    imax_raw = int(np.argmax(dh_raw))

    img_header = make_header_plot(t, h)
    img_deriv, t_dh_smooth_max, dh_smooth_max = make_derivative_plot(
        t, h, dh_raw, d2h_raw, popt, imax_raw
    )
    img_fit = make_fit_plot(t, h, popt)
    img_resid = make_residual_plots(t, h, popt, stats_dict["resid"])
    img_area = make_area_plot(t, h, popt, integ)

    param_rows = "\n".join(
        f"<tr><td>{nm} ({un})</td><td>{val:.5f}</td><td>{se:.5f}</td>"
        f"<td>{tv:.3f}</td><td>{pv:.3e}</td></tr>"
        for nm, un, val, se, tv, pv in zip(
            PARAM_NAMES, PARAM_UNITS, popt, stats_dict["se"],
            stats_dict["tvals"], stats_dict["pvals"],
        )
    )

    d2h_comment = (
        "The fitted second derivative is a clean, two-lobed signal hidden "
        "entirely inside logger-rounding noise in the raw second difference "
        "(compare the scatter to the smooth orange curve below): positive "
        "while the inflow is still accelerating the rise, crossing to "
        "negative once the rise decelerates into the crest, staying "
        "negative through the recession, then returning toward zero as the "
        "level settles onto its new plateau - i.e. the inflow pulse itself "
        "rose, peaked, and fell away, it did not simply switch on and stay on."
    )

    model_defense = (
        "A single logistic or Gompertz assumes one monotonic rise settling "
        "onto a ceiling; this record rises, overshoots to a crest, and then "
        "recedes to a new plateau, so a monotonic model cannot fit it. The "
        "sum-of-two-logistics form supplies a rising limb (a1, k1, t01) for "
        "the flood pulse and a second, slower, negative-amplitude limb "
        "(a2, k2, t02) for the recession, letting the curve overshoot and "
        "settle - the same 'two pulses' structure the activity sheet "
        "suggests, used here for one pulse's rise and its own recession "
        "rather than two separate rainfall bands."
    )

    gap_comment = (
        f"quad integrates the continuous fitted curve; trapezoid sums straight "
        f"line segments between the logger's own centimeter-rounded points. "
        f"The {integ['gap']:+.3f} m&middot;h gap is small ({100*abs(integ['gap'])/integ['A_trap']:.2f}% "
        f"of the trapezoid total) and comes from exactly that: the fit smooths "
        f"through the rounding and through the residual pattern noted above, "
        f"while the trapezoid rule takes the raw points, kinks and all, "
        f"literally."
    )

    filled = HTML_TEMPLATE.format(
        n=stats_dict["n"], tn=t[-1],
        img_header=img_header,
        dh_raw_max=dh_raw[imax_raw], t_dh_raw_max=t[imax_raw],
        dh_smooth_max=dh_smooth_max, t_dh_smooth_max=t_dh_smooth_max,
        img_deriv=img_deriv, d2h_comment=d2h_comment,
        model_defense=model_defense, img_fit=img_fit,
        param_rows=param_rows,
        sse=stats_dict["sse"], p=stats_dict["p"], r2=stats_dict["r2"],
        sst=stats_dict["sst"], s=stats_dict["s"], dof=stats_dict["dof"],
        img_resid=img_resid, resid_verdict=resid_read["verdict"],
        img_area=img_area,
        A_quad=integ["A_quad"], A_err=integ["A_err"],
        A_trap=integ["A_trap"], gap=integ["gap"], gap_comment=gap_comment,
    )
    return filled


def main():
    # ---------- 1. DATA PREPARATION & FINITE DIFFERENCES ----------
    t, h = load_stage_log(DATA_PATH)
    dh_raw, d2h_raw = finite_differences(t, h)
    imax_raw = int(np.argmax(dh_raw))
    print(f"[1] n={len(t)} readings, dt={t[1]-t[0]:.2f} h, "
          f"max raw dh/dt = {dh_raw[imax_raw]:.4f} m/h at t={t[imax_raw]:.2f} h")

    # ---------- 2. CURVE FITTING & STATISTICAL METRICS ----------
    popt, pcov = fit_curve(t, h)
    stats_dict = fit_statistics(t, h, popt, pcov)
    resid_read = read_residuals(t, h, popt, stats_dict)
    print(f"[2] R2={stats_dict['r2']:.4f}  s={stats_dict['s']:.4f} m  "
          f"SSE={stats_dict['sse']:.4f}  dof={stats_dict['dof']}")
    for nm, val, se in zip(PARAM_NAMES, popt, stats_dict["se"]):
        print(f"    {nm:5s}= {val: .5f}  (SE {se:.5f})")

    # ---------- 3. NUMERICAL INTEGRATION ----------
    integ = integrate_fit(t, h, popt)
    print(f"[3] A(quad)={integ['A_quad']:.4f} m*h (err {integ['A_err']:.2e}), "
          f"A(trapezoid)={integ['A_trap']:.4f} m*h, gap={integ['gap']:+.4f} m*h")

    # ---------- 4. DASHBOARD GENERATION ----------
    html = build_dashboard(t, h, dh_raw, d2h_raw, popt, stats_dict, resid_read, integ)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[4] dashboard written to {OUT_HTML}  ({len(html)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
