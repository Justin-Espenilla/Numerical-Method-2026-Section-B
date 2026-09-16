"""
series1.py -- Series1 PDF Laboratory Exercises 1-3 (Combined Figures)
Author: Espenilla
Source: python-3/Series1.pdf  page 1 (exercises) + page 2 (expected figures)
Output: 3 images only -> python-3/figures/series1_figure1.png, series1_figure2.png, series1_figure3.png
          Each exercise's sub-plots are combined into ONE figure window (1 figure per exercise).

Exercise 1: (1 + 1/n)^n -> e  up to nanosecond  (365 days/year)
Exercise 2: (a^h - 1)/h -> ln(a)  for a=2,e,3  as h shrinks  (Tolerance 1e-6)
Exercise 3: e^x = sum_{n=0}^{inf} x^n/n!  up to 10,000 terms  (primary x=1)

Each figure includes a histogram/bar panel per "Draw a Histogram in Matplotlib" requirement.
Run:  py python-3/series1.py  or  py -m python-3.series1
"""

import math
import os
import matplotlib.pyplot as plt
import numpy as np

# --- 0. Paths ---
BASE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

FIG1_OUT = os.path.join(FIG_DIR, "series1_figure1.png")
FIG2_OUT = os.path.join(FIG_DIR, "series1_figure2.png")
FIG3_OUT = os.path.join(FIG_DIR, "series1_figure3.png")

plt.rcParams.update({"font.size": 9})

# ==============================================================
# FIGURE 1 : Exercise 1  (1+1/n)^n  -> e
# ==============================================================
print("=" * 78)
print("FIGURE 1 / Exercise 1: (1 + 1/n)^n -> e  up to nanosecond")
print("=" * 78)

freq = [
    ("yearly", 1),
    ("twice a year", 2),
    ("quarterly", 4),
    ("monthly", 12),
    ("weekly", 52),
    ("daily", 365),
    ("hourly", 365 * 24),
    ("every minute", 365 * 24 * 60),
    ("every second", 365 * 24 * 60 * 60),
    ("every millisecond", 365 * 24 * 60 * 60 * 1000),
    ("every microsecond", 365 * 24 * 60 * 60 * 1000 * 1000),
    ("every nanosecond", 365 * 24 * 60 * 60 * 1000 * 1000 * 1000),
]
labels1, n_vals = zip(*freq)
n_vals = list(n_vals)
e_true = math.e
print(f"True e = {e_true:.15f}")

# stable computation exp(n*log1p(1/n)) avoids (1+1/n)==1.0 for huge n
values = [math.exp(n * math.log1p(1.0 / n)) for n in n_vals]
# also naive for table comparison
values_naive = [(1 + 1.0 / n) ** n for n in n_vals]

# print table (matches PDF anchors)
print(f"{'How often':<18} | {'n':>22} | {'(1+1/n)^n':>14} | {'|err|':>12}")
print("-" * 78)
for lab, n, v in zip(labels1, n_vals, values):
    err = abs(v - e_true)
    print(f"{lab:<18} | {n:>22,} | {v:>14.6f} | {err:>12.2e}")
print("-" * 78)
print("PDF anchor: yearly 2.000000, twice 2.250000, quarterly 2.441406 ->",
      f"{values[0]:.6f}, {values[1]:.6f}, {values[2]:.6f}")
print()

errors1 = [abs(v - e_true) for v in values]

# --- Single Combined Figure 1 (1 figure, 2 panels side-by-side) ---
# Left: Value per compounding period (bar/histogram) | Right: Error (log bar)
fig1 = plt.figure(1, figsize=(12, 5))
fig1.suptitle("Exercise 1: Convergence of (1 + 1/n)^n to e", fontsize=11, fontweight="bold")
gs1 = fig1.add_gridspec(1, 2, wspace=0.28)

# (0,0) Value per compounding period
ax1a = fig1.add_subplot(gs1[0, 0])
bars1 = ax1a.bar(range(len(labels1)), values, color="#1f77b4", edgecolor="white", linewidth=0.6)
ax1a.axhline(e_true, color="red", linestyle="--", linewidth=1.4, label=f"e = {e_true:.5f}")
ax1a.set_xticks(range(len(labels1)))
ax1a.set_xticklabels(labels1, rotation=38, ha="right", fontsize=7)
ax1a.set_ylabel("$(1+1/n)^n$")
ax1a.set_title("Value per compounding period", fontsize=10)
ax1a.set_ylim(1.9, 2.85)
ax1a.grid(True, axis="y", linestyle="--", alpha=0.5)
ax1a.legend(fontsize=7, loc="lower right")
# annotate bar values (like p2 fig)
for bar, v in zip(bars1, values):
    ax1a.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
              f"{v:.4f}", ha="center", va="bottom", fontsize=5.5, rotation=90, color="#333333")

# (0,1) Error shrinks like e/(2n) (log scale) - histogram/bar of errors
ax1b = fig1.add_subplot(gs1[0, 1])
# use bar with log y
ax1b.bar(range(len(labels1)), errors1, color="orange", edgecolor="white", linewidth=0.6)
ax1b.set_yscale("log")
ax1b.set_xticks(range(len(labels1)))
ax1b.set_xticklabels(labels1, rotation=38, ha="right", fontsize=7)
ax1b.set_ylabel("$|(1+1/n)^n - e|$  (log scale)")
ax1b.set_title("Error shrinks like e/(2n)", fontsize=10)
ax1b.grid(True, which="both", linestyle="--", alpha=0.5)

fig1.tight_layout(rect=[0, 0, 1, 0.94])
fig1.savefig(FIG1_OUT, dpi=300, bbox_inches="tight")
print(f"Saved FIGURE 1 -> {FIG1_OUT}")

# ==============================================================
# FIGURE 2 : Exercise 2  (a^h - 1)/h -> ln(a)
# ==============================================================
print()
print("=" * 78)
print("FIGURE 2 / Exercise 2: (a^h - 1)/h -> ln(a)  (Tolerance 1e-6)")
print("=" * 78)

bases = {"a=2": 2.0, "a=e": math.e, "a=3": 3.0}
ln_vals = {k: math.log(v) for k, v in bases.items()}
h_values = [0.1, 0.01, 0.001, 0.0001, 1e-05, 1e-06, 1e-07]
h_labels = ["0.1", "0.01", "0.001", "0.0001", "1e-05", "1e-06", "1e-07"]

def calc_ah(a, h):
    return math.expm1(h * math.log(a)) / h

table2 = {label: [calc_ah(a, h) for h in h_values] for label, a in bases.items()}

# print table matching PDF
print(f"{'h':>10} | {'a=2':>10} | {'a=e':>10} | {'a=3':>10}")
print("-" * 52)
pdf_anchor = {
    0.1: (0.7177, 1.0517, 1.1612),
    0.01: (0.6956, 1.0050, 1.1047),
    0.001: (0.6934, 1.0005, 1.0992),
    0.0001: (0.6932, 1.00005, 1.0987),
}
for i, h in enumerate(h_values[:4]):
    v2, ve, v3 = table2["a=2"][i], table2["a=e"][i], table2["a=3"][i]
    pa, pe, p3 = pdf_anchor[h]
    print(f"{h:>10g} | {v2:>10.4f} | {ve:>10.4f} | {v3:>10.4f}  (PDF {pa:.4f}/{pe:.4f}/{p3:.4f})")
print(f"{'settles at':>10} | {ln_vals['a=2']:>10.4f} | {ln_vals['a=e']:>10.4f} | {ln_vals['a=3']:>10.4f}  (ln a)")
print("-" * 52)
print("Tolerance x 1e-6: smallest h with |val - ln(a)| < 1e-6")
for label in bases:
    for h, v in zip(h_values, table2[label]):
        if abs(v - ln_vals[label]) < 1e-6:
            print(f"  {label} reaches 1e-6 at h={h:g}  (val {v:.7f} vs ln {ln_vals[label]:.7f})")
            break
print()

# --- Single Combined Figure 2 (1 figure, grouped bars + histogram) ---
# One figure window; two representations inside to honor "histogram" requirement
fig2 = plt.figure(2, figsize=(12, 5.5))
fig2.suptitle("Exercise 2: (a^h - 1)/h settling to ln(a)", fontsize=11, fontweight="bold")
gs2 = fig2.add_gridspec(1, 2, wspace=0.30)

# (0,0) Grouped bars per h
ax2a = fig2.add_subplot(gs2[0, 0])
n_h = len(h_values)
x = np.arange(n_h)
w = 0.22
colors2 = {"a=2": "#1f77b4", "a=e": "#2ca02c", "a=3": "#d62728"}
for idx, (label, a) in enumerate(bases.items()):
    offset = (idx - 1) * w
    vals = table2[label]
    bars = ax2a.bar(x + offset, vals, width=w, color=colors2[label], edgecolor="white", linewidth=0.6, label=f"{label} (ln={ln_vals[label]:.4f})")
# dashed ln(a) lines
for label in bases:
    ax2a.axhline(ln_vals[label], color=colors2[label], linestyle="--", linewidth=1.2, alpha=0.9)
ax2a.set_xticks(x)
ax2a.set_xticklabels(h_labels, fontsize=8)
ax2a.set_xlabel("h")
ax2a.set_ylabel("$(a^h - 1)/h$")
ax2a.set_title("Bars: difference quotient per h. Dashed: ln(a)", fontsize=9)
ax2a.set_ylim(0.6, 1.25)
ax2a.grid(True, axis="y", linestyle="--", alpha=0.5)
ax2a.legend(fontsize=7)

# (0,1) Histogram view of pooled values
ax2b = fig2.add_subplot(gs2[0, 1])
all_vals = []
for label in bases:
    all_vals.extend(table2[label])
bins = np.linspace(0.65, 1.20, 14)
ax2b.hist(all_vals, bins=bins, color="#D5D8DC", edgecolor="white", alpha=0.95, label="pooled")
for label in bases:
    ax2b.hist(table2[label], bins=bins, histtype="step", color=colors2[label], linewidth=2, label=label)
for label in bases:
    ax2b.axvline(ln_vals[label], color=colors2[label], linestyle="--", linewidth=1.4)
ax2b.set_xlabel("$(a^h - 1)/h$ value")
ax2b.set_ylabel("Frequency")
ax2b.set_title("Histogram of values (pooled + per-a)", fontsize=9)
ax2b.grid(True, axis="y", linestyle="--", alpha=0.5)
ax2b.legend(fontsize=7)

fig2.tight_layout(rect=[0, 0, 1, 0.93])
fig2.savefig(FIG2_OUT, dpi=300, bbox_inches="tight")
print(f"Saved FIGURE 2 -> {FIG2_OUT}")

# ==============================================================
# FIGURE 3 : Exercise 3  e^x = sum x^n/n!  up to 10,000
# ==============================================================
print()
print("=" * 78)
print("FIGURE 3 / Exercise 3: e^x = sum x^n/n!  up to 10,000")
print("=" * 78)

N_max = 10000
x_primary = 1
true_e = math.e

# compute partial sums via recurrence term_{n}= term_{n-1}*x/n
def partial_sums(x, Nmax):
    terms = np.zeros(Nmax + 1, dtype=float)
    sums = np.zeros(Nmax + 1, dtype=float)
    term = 1.0
    s = 1.0
    terms[0] = 1.0
    sums[0] = 1.0
    for n in range(1, Nmax + 1):
        term = term * x / n
        s += term
        terms[n] = term
        sums[n] = s
        if term == 0.0 and n > 200:
            # remaining sums stay constant
            if n < Nmax:
                sums[n+1:] = s
                terms[n+1:] = 0.0
            break
    return terms, sums

terms1, sums1 = partial_sums(x_primary, N_max)
# also compute x=2,5 for insight but primary is x=1
terms2, sums2 = partial_sums(2, N_max)
terms5, sums5 = partial_sums(5, N_max)

milestones = [1, 2, 3, 5, 10, 15, 20, 50, 100, 1000, 10000]
# include N=0 as well
milestones_plot = [1, 2, 3, 5, 10, 15, 20, 30, 50, 100, 1000, 10000]

print(f"x=1  true e = {true_e:.15f}")
print(f"{'N':>6} | {'S_N':>18} | {'|S_N - e|':>14}")
print("-" * 48)
for N in [1,2,3,5,10,20,50,100,1000,10000]:
    s = sums1[N]
    err = abs(s - true_e)
    print(f"{N:>6} | {s:>18.12f} | {err:>14.2e}")
print()
print(f"At N=10000, S={sums1[10000]:.15f} vs e={true_e:.15f} err={abs(sums1[10000]-true_e):.2e}")
print(f"x=2: S10000={sums2[10000]:.8f} vs exp2={math.exp(2):.8f} err={abs(sums2[10000]-math.exp(2)):.2e}")
print(f"x=5: S10000={sums5[10000]:.8f} vs exp5={math.exp(5):.8f} err={abs(sums5[10000]-math.exp(5)):.2e}")
print()

# error array for x=1
# sample log-spaced N for smooth line
N_plot = np.unique(np.logspace(0, 4, 400, dtype=int))
N_plot = N_plot[N_plot <= N_max]
N_plot = np.insert(N_plot, 0, 0)
# N_plot includes 0
err_plot = np.abs(sums1[N_plot] - true_e)
err_plot = np.where(err_plot == 0, 1e-16, err_plot)

# --- Single Combined Figure 3 (1 figure, 2 panels) ---
fig3 = plt.figure(3, figsize=(12, 5))
fig3.suptitle("Exercise 3: e^x = sum x^n/n!  (x=1, summation up to N=10,000)", fontsize=11, fontweight="bold")
gs3 = fig3.add_gridspec(1, 2, wspace=0.30)

# (0,0) Histogram of partial sums (bar) - purple like p2
ax3a = fig3.add_subplot(gs3[0, 0])
vals_bar = [sums1[n] for n in milestones_plot]
cols_bar = plt.cm.Purples(np.linspace(0.35, 0.92, len(milestones_plot)))
bars3 = ax3a.bar(range(len(milestones_plot)), vals_bar, color=cols_bar, edgecolor="#4A148C", linewidth=0.5)
ax3a.axhline(true_e, color="red", linestyle="--", linewidth=1.2, label=f"e={true_e:.5f}")
ax3a.set_xticks(range(len(milestones_plot)))
ax3a.set_xticklabels([str(n) for n in milestones_plot], fontsize=7, rotation=30, ha="right")
ax3a.set_xlabel("number of terms N in the summation")
ax3a.set_ylabel("$S_N = sum_{n=0}^N x^n/n!$")
ax3a.set_title("Histogram of the partial sums", fontsize=9)
ax3a.set_ylim(0.9, 2.95)
ax3a.grid(True, axis="y", linestyle="--", alpha=0.5)
ax3a.legend(fontsize=7)
for bar, v in zip(bars3, vals_bar):
    ax3a.text(bar.get_x() + bar.get_width()/2, bar.get_height()+0.04, f"{v:.3f}", ha="center", va="bottom", fontsize=5.5, rotation=90, color="#333333")

# (0,1) Error vs N (log-log) - how many correct digits
ax3b = fig3.add_subplot(gs3[0, 1])
ax3b.loglog(N_plot + 1, err_plot, color="#1f77b4", linewidth=1.8, marker="o", markersize=2, alpha=0.9)
ax3b.axhline(1e-12, color="green", linestyle=":", linewidth=1.2, label="1e-12")
ax3b.axhline(1e-15, color="blue", linestyle="--", linewidth=1.0, label="~1e-15 (double)")
# annotate digits
for N_ann, txt in [(1, "0 digits"), (3, "2 digits"), (5, "2 digits"), (10, "6 digits"), (20, "12 digits")]:
    # find closest N_plot
    idx = np.argmin(np.abs(N_plot - N_ann))
    ax3b.annotate(txt, xy=(N_plot[idx]+1, err_plot[idx]), xytext=(6, 4), textcoords="offset points",
                  fontsize=6, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#CCCCCC", alpha=0.9))
ax3b.set_xlabel("number of terms N in the summation (log scale)")
ax3b.set_ylabel("|$S_N - e|$  (log scale)")
ax3b.set_title("How many correct digits each N buys (log-log)", fontsize=9)
ax3b.grid(True, which="both", linestyle="--", alpha=0.5)
ax3b.legend(fontsize=7)
# twin axis for correct digits
ax3b2 = ax3b.twinx()
# convert error to digits: -log10(err)
ax3b2.set_ylim(ax3b.get_ylim())
ax3b2.set_yscale("log")
# set ticks for digits: manual
# we'll just label secondary as digits
ax3b2.set_ylabel("correct decimal digits", fontsize=7)

fig3.tight_layout(rect=[0, 0, 1, 0.93])
fig3.savefig(FIG3_OUT, dpi=300, bbox_inches="tight")
print(f"Saved FIGURE 3 -> {FIG3_OUT}")

print()
print("All done: 3 figures (Figure 1,2,3) -> 3 images in figures/.")
print(f"  Figure 1: {FIG1_OUT}")
print(f"  Figure 2: {FIG2_OUT}")
print(f"  Figure 3: {FIG3_OUT}")

plt.show()
