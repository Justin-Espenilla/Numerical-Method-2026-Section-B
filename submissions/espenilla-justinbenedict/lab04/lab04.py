"""
civil_series.py -- Civil Engineering Series Exercise (Combined Figure)
Author: Espenilla
Source: python-4/Civil_Engineering_Series_Exercise.pdf  (Sep 15, 2026)
Output: single combined figure -> python-4/figures/civil_series_combined.png
        + tables printed + recommendation saved to python-4/figures/civil_recommendation.txt

Engineering scenario: y = L sin(theta), L=20 m, theta in degrees.
Parts covered:
 1. Geometric Series: geometric_sum(x,N) loop without closed form
 2. Power Series: power_series(x, coefficients) loop
 3. Maclaurin sin(theta) loop (explicit factorial loop)
 4. Engineering investigation table for angles 1,2,5,10,15,20,30 deg, N=1..4
 5. Taylor sin(theta) centered at a=10 deg, Maclaurin vs Taylor error comparison
 6. Error tolerance <0.1% -- min terms, critical angle for sin~theta
 7. Final engineering recommendation with civil-engineer reasoning

Implementation note: All series summations use explicit Python loops as required.
No symbolic math hidden. math.sin only for exact verification.

Civil engineer mindset (web-grounded):
 - 0.1% tolerance = 3.5 mm on y~3.5 m at 10 deg, 10 mm on 10 m at 30 deg -- strict, near aerospace level.
   Civil 1% tolerance found in references for load-bearing; 0.1% requires justification.
 - Small-angle sin~theta error ~ theta^2/6*100 (%). So 0.1% fails at ~4.4 deg (0.077 rad), 1% at ~14 deg.
   GT/Gatech figure: 4% sin-only error allows up to 25 deg. So 1-term valid only for flat slopes.
 - Maclaurin best near 0 deg, Taylor at 10 deg best within ±10 deg of center. Remainders scale as (theta-a)^{N+1}.
 - Field practice: exact math.sin is free (calculator/CAD). Series value is pedagogical / embedded MCU.
   Civil choice = simplest that passes everywhere with margin.
"""

import math
import os
import subprocess
import sys
import matplotlib
# Use an interactive backend so figures pop up when you run the script.
# "Agg" (previous setting) only saves to files and never displays windows.
# TkAgg works on standard Windows Python (tkinter verified available).
try:
    matplotlib.use("TkAgg")
except Exception:
    # Fallback: keep default backend (still try to show; saving always works)
    pass
import matplotlib.pyplot as plt
import numpy as np

# --- 0. Setup paths ---
BASE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE, "figures")
os.makedirs(FIG_DIR, exist_ok=True)
FIG_COMBINED = os.path.join(FIG_DIR, "civil_series_combined.png")
REC_TXT = os.path.join(FIG_DIR, "civil_recommendation.txt")
# also save individual for convenience
FIG_CONV = os.path.join(FIG_DIR, "civil_convergence.png")
FIG_FUNC = os.path.join(FIG_DIR, "civil_function_comparison.png")
FIG_ERR = os.path.join(FIG_DIR, "civil_error_comparison.png")

plt.rcParams.update({"font.size": 9})

L = 20.0
ANGLES_DEG = [1, 2, 5, 10, 15, 20, 30]
A_TAYLOR_DEG = 10
A_TAYLOR_RAD = math.radians(A_TAYLOR_DEG)

# ==============================================================
# CORE FUNCTIONS (explicit loops as per PDF)
# ==============================================================
def geometric_sum(x, N):
    """Calculate S_N = 1 + x + x^2 + ... + x^N using loop (no closed form)."""
    total = 0.0
    for k in range(N + 1):
        total += x ** k
    return total

def power_series(x, coefficients):
    """Evaluate P_N(x) = a0 + a1*x + ... + aN*x^N with given coefficients."""
    result = 0.0
    for k, a_k in enumerate(coefficients):
        result += a_k * (x ** k)
    return result

def sin_maclaurin(theta, N):
    """Approximate sin(theta) with N terms of Maclaurin series (theta in radians).
       N=1 -> theta, N=2 -> theta - theta^3/3!, etc.
    """
    result = 0.0
    for n in range(N):
        sign = (-1) ** n
        factorial = math.factorial(2 * n + 1)
        result += sign * (theta ** (2 * n + 1)) / factorial
    return result

def sin_taylor(theta, a, N):
    """Approximate sin(theta) using Taylor centered at a (both radians) with N terms.
       Derivatives of sin cycle every 4: sin(a), cos(a), -sin(a), -cos(a)
    """
    result = 0.0
    sin_a = math.sin(a)
    cos_a = math.cos(a)
    for n in range(N):
        pattern = n % 4
        if pattern == 0:
            f_deriv = sin_a
        elif pattern == 1:
            f_deriv = cos_a
        elif pattern == 2:
            f_deriv = -sin_a
        else:
            f_deriv = -cos_a
        term = f_deriv * ((theta - a) ** n) / math.factorial(n)
        result += term
    return result

def pct_error(approx, exact):
    if exact == 0:
        return 0.0 if approx == 0 else float("inf")
    return abs(approx - exact) / abs(exact) * 100.0

# ==============================================================
# PART 1: GEOMETRIC SERIES
# ==============================================================
print("=" * 78)
print("PART 1: GEOMETRIC SERIES  S_N = 1 + x + ... + x^N, exact = 1/(1-x)")
print("=" * 78)
xs = [0.5, 0.8, 0.9]
N_tests = [5, 10, 20, 50]
header_parts = [f'N={n:>2} S_N' for n in N_tests]
print(f"{'x':>5} | {'exact 1/(1-x)':>14} | " + " | ".join([f"{p:>12}" for p in header_parts]) + " |  N for <0.1%")
print("-" * 90)
for x in xs:
    exact = 1 / (1 - x)
    row = f"{x:>5.1f} | {exact:>14.6f} | "
    s_vals = []
    for N in N_tests:
        s = geometric_sum(x, N)
        s_vals.append(s)
        err = pct_error(s, exact)
        row += f"{s:>12.6f} | "
    # find min N for <0.1%
    minN = None
    for N in range(0, 200):
        if pct_error(geometric_sum(x, N), exact) < 0.1:
            minN = N
            break
    row += f" {minN}"
    print(row)
    # detailed error line
    err_line = f"      | {'% err':>14} | " + " | ".join([f"{pct_error(s, exact):>11.4f}%" for s in s_vals])
    print(err_line)
print()
print("Civil insight: Convergence ~ x^{N+1}. At x=0.5 fast (N=10 => 0.05% err),")
print("at x=0.9 slow (N=20 => 8.8% err, N=50 => 0.5% err). Same as larger theta -> needs more terms.")
print()

# ==============================================================
# PART 2: POWER SERIES (demonstration)
# ==============================================================
print("=" * 78)
print("PART 2: POWER SERIES  P_N(x)=a0+a1*x+...+aN*x^N")
print("=" * 78)
# Example: polynomial 1 + 2*x + 3*x^2 as power series
coeffs_demo = [1, 2, 3]
x_demo = 2.0
val_demo = power_series(x_demo, coeffs_demo)
print(f"Demo: coeff={coeffs_demo}, x={x_demo} => P={val_demo}  (expected 1+4+12=17)")
# Show Maclaurin coefficients for sin as power series (odd only)
# sin coefficients up to 7th degree: [0,1,0,-1/6,0,1/120,0,-1/5040]
coeffs_sin = [0, 1, 0, -1/math.factorial(3), 0, 1/math.factorial(5), 0, -1/math.factorial(7)]
for th_deg in [10, 30]:
    th = math.radians(th_deg)
    pval = power_series(th, coeffs_sin)
    exact = math.sin(th)
    print(f"  sin({th_deg} deg) via power_series coeff sin: approx {pval:.8f} vs exact {exact:.8f}  err {pct_error(pval,exact):.4f}%")
print("Key Insight: A polynomial is a finite power series; infinite series approximates transcendental functions.")
print()

# ==============================================================
# PART 3: MACLAURIN FOR sin(theta) at 10 deg
# ==============================================================
print("=" * 78)
print("PART 3: MACLAURIN SERIES FOR sin(theta) at theta=10 deg (0.17453 rad)")
print("=" * 78)
theta10_rad = math.radians(10)
exact10 = math.sin(theta10_rad)
print(f"Exact sin(10 deg) = {exact10:.10f}")
print(f"{'N terms':>8} | {'approximation':>15} | {'abs error':>12} | {'% error':>10} | {'formula'}")
print("-" * 78)
for N in [1, 2, 3, 4]:
    approx = sin_maclaurin(theta10_rad, N)
    abse = abs(approx - exact10)
    pce = pct_error(approx, exact10)
    if N == 1:
        form = "theta"
    elif N == 2:
        form = "theta - theta^3/3!"
    elif N == 3:
        form = "theta - theta^3/3! + theta^5/5!"
    else:
        form = "theta - theta^3/3! + theta^5/5! - theta^7/7!"
    print(f"{N:>8} | {approx:>15.10f} | {abse:>12.2e} | {pce:>9.4f}% | {form}")
print()
print("Investigation answer: 1-term (+0.5095%) fails 0.1% at 10 deg, 2-term (0.0008%) passes easily,")
print("3-term error ~0.0000003%, 4-term <1e-10%. Error drops ~ theta^2/(2N+1) factor each term.")
print()

# ==============================================================
# PART 4: ENGINEERING INVESTIGATION  y = L sin(theta)
# ==============================================================
print("=" * 78)
print("PART 4: ENGINEERING INVESTIGATION  y = L sin(theta), L=20 m")
print("Angles: 1,2,5,10,15,20,30 deg, N=1..4 terms (Maclaurin)")
print("=" * 78)

def y_exact(theta_deg):
    return L * math.sin(math.radians(theta_deg))

def y_mac(theta_deg, N):
    return L * sin_maclaurin(math.radians(theta_deg), N)

def y_tay(theta_deg, N, a_rad=A_TAYLOR_RAD):
    return L * sin_taylor(math.radians(theta_deg), a_rad, N)

# Print tables per N
for N in [1, 2, 3, 4]:
    print(f"\n--- Maclaurin N={N} terms {'(theta)' if N==1 else ''} ---")
    print(f"{'Angle':>6} | {'theta rad':>10} | {'Exact y (m)':>12} | {'Approx y (m)':>12} | {'Abs err (m)':>12} | {'% err':>8}")
    print("-" * 78)
    for ang in ANGLES_DEG:
        th = math.radians(ang)
        exact = y_exact(ang)
        approx = y_mac(ang, N)
        abse = abs(approx - exact)
        pce = pct_error(approx, exact)
        print(f"{ang:>5} deg | {th:>10.6f} | {exact:>12.6f} | {approx:>12.6f} | {abse:>12.6f} | {pce:>7.4f}%")
    # summary
    # also compute max error
    max_pce = max(pct_error(y_mac(a, N), y_exact(a)) for a in ANGLES_DEG)
    print(f"  Max % err across 1-30 deg at N={N}: {max_pce:.4f}%")

# Also store for later plots
mac_table = {}  # N -> list per angle
for N in [1, 2, 3, 4, 5, 6]:
    mac_table[N] = [pct_error(y_mac(a, N), y_exact(a)) for a in ANGLES_DEG]
    # also absolute
tay_table = {}
for N in [1, 2, 3, 4, 5, 6]:
    tay_table[N] = [pct_error(y_tay(a, N), y_exact(a)) for a in ANGLES_DEG]

# Analysis questions answers (pre-computed civil engineer logic check)
print("\nAnalysis Questions (civil engineer view):")
print("1. Error vs angle: Increases ~ theta^{2N+1}. At N=1, pce 0.002% at 1 deg -> 4.72% at 30 deg (theta rad ^2/6).")
for N in [1,2,3,4]:
    pcs = [pct_error(y_mac(a,N), y_exact(a)) for a in [1,5,15,30]]
    print(f"   N={N}: 1deg {pcs[0]:.4f}%, 5deg {pcs[1]:.4f}%, 15deg {pcs[2]:.4f}%, 30deg {pcs[3]:.4f}%")
print("2. Error vs terms: Drops factorial. 30deg: 4.7198% (1-term) -> 0.0652% (2-term) -> 0.00043% (3-term) -> ~0% (4-term).")
print("3. Small angles <5 deg: N=2 sufficient for <0.1% (N=1 fails at 5 deg with 0.127%, at 4.44 deg critical).")
print("4. Larger angles >20 deg: N=2 already passes at 30 deg (0.065%), N=3 gives 230x margin (0.00043%). Civil engineer adds safety factor 2-3 -> recommend N=3.")
print()

# ==============================================================
# PART 5: TAYLOR SERIES centered at a=10 deg
# ==============================================================
print("=" * 78)
print("PART 5: TAYLOR SERIES centered at a=10 deg vs Maclaurin (center 0)")
print("=" * 78)
print(f"Taylor center a={A_TAYLOR_DEG} deg ({A_TAYLOR_RAD:.6f} rad)  N=1..4")
print(f"{'Angle':>6} | {'Exact y':>10} | {'Mac N=2':>10} {'%':>7} | {'Tay N=2':>10} {'%':>7} | {'Mac N=3':>10} {'%':>7} | {'Tay N=3':>10} {'%':>7}")
print("-" * 95)
for ang in ANGLES_DEG:
    exact = y_exact(ang)
    m2 = y_mac(ang, 2)
    t2 = y_tay(ang, 2)
    m3 = y_mac(ang, 3)
    t3 = y_tay(ang, 3)
    print(f"{ang:>5} deg | {exact:>10.4f} | {m2:>10.4f} {pct_error(m2,exact):>6.3f}% | {t2:>10.4f} {pct_error(t2,exact):>6.3f}% | {m3:>10.4f} {pct_error(m3,exact):>6.3f}% | {t3:>10.4f} {pct_error(t3,exact):>6.3f}%")
print()
print("Comparison analysis:")
# find cross over: compute for fine angles
fine_degs = np.linspace(1, 30, 60)
mac_err_fine = [pct_error(y_mac(d,3), y_exact(d)) for d in fine_degs]
tay_err_fine = [pct_error(y_tay(d,3), y_exact(d)) for d in fine_degs]
# where Taylor better?
better_near = sum(1 for m,t in zip(mac_err_fine,tay_err_fine) if t < m)
print(f"  At N=3, Taylor < Maclaurin for {better_near}/{len(fine_degs)} sampled angles.")
print(f"  At 1 deg (9 deg from center): Mac {pct_error(y_mac(1,3), y_exact(1)):.4f}% vs Tay {pct_error(y_tay(1,3), y_exact(1)):.4f}% -> Maclaurin wins far from 10 deg")
print(f"  At 10 deg (0 deg from center): Mac {pct_error(y_mac(10,3), y_exact(10)):.5f}% vs Tay {pct_error(y_tay(10,3), y_exact(10)):.5f}% -> Taylor wins exactly at center")
print(f"  At 15 deg (5 deg from center): Mac {pct_error(y_mac(15,3), y_exact(15)):.4f}% vs Tay {pct_error(y_tay(15,3), y_exact(15)):.4f}% -> Maclaurin wins (both <0.05% but Mac 0%)")
print(f"  At 30 deg (20 deg from center): Mac {pct_error(y_mac(30,3), y_exact(30)):.4f}% vs Tay {pct_error(y_tay(30,3), y_exact(30)):.4f}% (N=3) -> Maclaurin wins far away (20 deg distance)")
print("  Civil takeaway: Choose center near your operating band. For general 0-30 deg survey, Maclaurin is simpler and more balanced.")
print("                  For repetitive work around 10 deg (e.g., typical ramp), Taylor@10 with 2 terms saves one term.")
print()

# ==============================================================
# PART 6: ENGINEERING DECISION -- ERROR TOLERANCE <0.1%
# ==============================================================
print("=" * 78)
print("PART 6: ENGINEERING DECISION -- Tolerance <0.1% error")
print("=" * 78)
tol = 0.1
print(f"Tolerance: {tol}%  (0.1% => 3.5 mm at 10 deg, 10 mm at 30 deg on 20 m)")
print()

# Task 1: min N for each angle for both Maclaurin and Taylor
def min_terms_for_angle(angle_deg, method="maclaurin", tol=0.1, Nmax=15):
    exact = y_exact(angle_deg)
    for N in range(1, Nmax+1):
        if method == "maclaurin":
            approx = y_mac(angle_deg, N)
        else:
            approx = y_tay(angle_deg, N)
        if pct_error(approx, exact) < tol:
            return N, pct_error(approx, exact)
    return None, None

print(f"{'Angle':>6} | {'Mac min N':>9} {'pce':>8} | {'Taylor min N':>12} {'pce':>8} | {'Winner':>10}")
print("-" * 70)
for ang in ANGLES_DEG:
    mn_mac, pc_mac = min_terms_for_angle(ang, "maclaurin", tol)
    mn_tay, pc_tay = min_terms_for_angle(ang, "taylor", tol)
    winner = "Maclaurin" if mn_mac <= mn_tay else "Taylor"
    if mn_mac == mn_tay:
        winner = "Tie"
    print(f"{ang:>5} deg | {mn_mac:>9} {pc_mac:>7.4f}% | {mn_tay:>12} {pc_tay:>7.4f}% | {winner:>10}")
print()

# Task 2: critical angle for sin~theta (1-term)
print("Task 2: Critical angle for sin(theta) ~ theta (1-term Maclaurin)")
print("Searching angle where % error first exceeds 0.1% and 1% ...")
critical_01 = None
critical_1 = None
# fine search 0.1 deg steps
for deg in np.arange(0.1, 30.1, 0.1):
    th = math.radians(deg)
    pce = pct_error(sin_maclaurin(th, 1), math.sin(th))
    if critical_01 is None and pce > 0.1:
        critical_01 = deg
    if critical_1 is None and pce > 1.0:
        critical_1 = deg
        break

print(f"  0.1% threshold crossed at ~{critical_01:.1f} deg  (theory ~4.4 deg =0.077 rad, sin approx error ~theta^2/6*100)")
# more precise bisection around 4-5 deg for 0.1%
lo, hi = 4.0, 5.0
for _ in range(20):
    mid = (lo+hi)/2
    pce = pct_error(sin_maclaurin(math.radians(mid),1), math.sin(math.radians(mid)))
    if pce < 0.1:
        lo = mid
    else:
        hi = mid
print(f"  Precise 0.1% critical: {hi:.2f} deg  (pce={pct_error(sin_maclaurin(math.radians(hi),1), math.sin(math.radians(hi))):.4f}%)")
print(f"  1% threshold crossed at ~{critical_1:.1f} deg (matches Wikipedia 14 deg and GT 4% at 25 deg logic)")
print()

print("Additional Analysis Questions:")
print("1. Does more terms always improve? Yes until floating precision limit, but monotonically for this range.")
print("   Remainder bound |R_N| <= |theta|^{2N+1}/(2N+1)! . At 30 deg (0.523 rad), N=4 remainder ~0.524^9/362880~1e-6 absolute.")
print("2. Why Maclaurin most accurate near zero? Centered at 0, remainder proportional to (theta-0)^{N+1}.")
print("3. Why Taylor center shift helps? Shifts expansion point, remainder (theta-a)^{N+1} smaller near a.")
print("4. Distance from center: Error ~ distance^{N+1}. Doubling distance ~ 2^{N+1} more error.")
print("5. Critical angle for sin~theta at 0.1%: ~4.5 deg. At 5 deg already 0.127% fails. So for civil flat slopes <4 deg you can use y~L*theta(rad).")
print()

# ==============================================================
# PART 7: FINAL ENGINEERING RECOMMENDATION
# ==============================================================
recommendation_text = """
FINAL ENGINEERING RECOMMENDATION -- y = L sin(theta), L=20 m, required <0.1% error
================================================================================
Date: 2026-09-16
Scenario: Sloping structural / surveying system, angles 1-30 deg.

FINDINGS (measured from Parts 4-6, verified by loop implementation):
- 1-term Maclaurin (sin~theta): fails at 5 deg (0.127%), passes only to ~4.44 deg. MAX error 4.72% at 30 deg.
- 2-term Maclaurin: PASSES ALL 1-30 deg at 0.1% (max 0.065% at 30 deg; at 10 deg 0.0008%, at 15 deg 0.0040%, at 20 deg 0.0126%).
  Margin at 30 deg is thin (0.065% vs 0.1% = 1.5x safety).
- 3-term Maclaurin: passes ALL 1-30 deg with large margin (max 0.00043% at 30 deg, <1e-6 else). 150x safety vs spec.
- 4-term Maclaurin: error <1e-7% at 30 deg (<0.00001 m on 10 m), essentially exact to double precision.
- Taylor@10deg: best near 10 deg. At N=2, Taylor errors 8.61% at 1 deg (9deg from center), 0.633% at 5 deg, 0.297% at 15 deg, 3.48% at 30 deg -- all worse than Maclaurin except exactly at 10 deg (0% vs 0.0008%).
  At N=3, Taylor at 30 deg 1.37% vs Maclaurin 0.00043% -- Maclaurin dominates for general 0-30 deg.
  Taylor needs N=4 to finally pass everywhere (max 0.029% at 30 deg, 0.020% at 1 deg), still 6x worse than Maclaurin N=3.

CONVERGENCE BEHAVIOR:
- Geometric example proves principle: x->1 slows convergence; same for theta large.
- Maclaurin error drops factorial: each added term divides error by ~(2N+1)*(2N) / theta^2.
  At 30 deg, factor ~ 7*6/(0.523^2)=153x per term after N=2, so 3 terms dramatic.
- Taylor error drops with (theta-a) distance.

COMPUTATIONAL SIMPLICITY vs ACCURACY:
- Maclaurin 2-term: 3 ops (theta^3/6), 3-term: + theta^5/120 (5 ops), 4-term: + theta^7/5040 (7 ops).
  No need to store sin(a), cos(a), nor compute (theta-a).
- Taylor 2-term: needs sin_a, cos_a, (theta-a) power, ~same ops but extra constants + branching.
  Minimal saving only if you work repeatedly 5-15 deg and can guarantee band.

VALID ANGLE RANGE (@0.1% spec, L=20 m):
- Maclaurin 2-term: 0-30 deg valid (0.065% worst) -- technically passes, but thin margin at 30 deg.
- Maclaurin 3-term: 0-30 deg valid with >150x margin (0.00043% worst) -- recommended for robustness.
- Taylor@10 4-term: 0-30 deg valid (0.03% worst) -- needs twice the terms as Maclaurin 2-term for same range.

RECOMMENDED SOLUTION:
-----------------------
PRIMARY RECOMMENDATION (General Purpose, most logical for civil engineer):
  Use 2-term Maclaurin for minimum that passes:  y ~ L * (theta - theta^3/6)  [theta in radians]
  Valid 0-30 deg with <0.1% error (0.065% worst at 30 deg, 6.5 mm error on 10 m vs 10 mm allowance).
  RECOMMENDED FOR FIELD USE: 3-term Maclaurin:  y ~ L * (theta - theta^3/6 + theta^5/120)
  Valid 0-30 deg with 0.00043% worst (0.043 mm on 10 m) -- 230x margin, negligible extra cost (2 more ops),
  and protects against spec tightening to 0.01% or occasional >30 deg (35 deg: 2-term 0.14% fails, 3-term 0.0015% passes).
  This is the best tradeoff:
  - Simple: one formula, centered at 0, no table of sin/cos centers
  - Accurate: passes spec everywhere with safety factor matching civil practice (FS~2-3)
  - Transparent: error bound is textbook remainder |theta|^{2N+1}/(2N+1)!, inspectable in field calc
  - Computationally cheap: 2-term 3 ops, 3-term 5 ops (precompute 1/6, 1/120); field calc or MCU negligible

ALTERNATIVE IF OPERATING BAND IS NARROW (e.g., all slopes ~8-12 deg):
  Taylor@10 with N=3 achieves 0.042% at 15 deg (Mac 2-term 0.004% already better), so no advantage.
  Taylor only wins if you insist on N=1 (at 10 deg 0% vs Mac 0.51%), but N=1 not valid beyond 4.5 deg anywhere else.
  Conclusion: For this 1-30 deg survey, even narrow-band does not justify Taylor complexity. Documented for completeness.

IF EXACT CALCULATOR AVAILABLE (Modern practice):
  Use math.sin (or CAD/table). Series is not more accurate than hardware; its value is understanding
  when you can trust a hand approximation and what margin you have. For deliverables, field crews
  should carry the 3-term formula on a laminated card for no-battery backup.

CRITICAL ANGLE FOR sin~theta:
  Do NOT use y~L*theta beyond ~4.5 deg for 0.1% spec. At 5 deg you already exceed by 27% over tolerance.
  For 1% tolerance you can stretch to ~14 deg, for 4% to ~25 deg (GT reference).

NUMERICAL EVIDENCE (from tables, L=20 m, verified by civil_series.py):
  At 5 deg:  exact 1.743115 m, 1-term 1.745329 (+0.127% fail), 2-term 1.743114 (-0.00002% pass)
  At 15 deg: exact 5.176381 m, 1-term 5.235988 (+1.15% fail), 2-term 5.176176 (-0.0040% pass), 3-term 5.176381 (+0.0000% pass)
  At 30 deg: exact 10.000000 m, 1-term 10.471976 (+4.72% fail), 2-term 9.993484 (-0.065% pass), 3-term 10.000043 (+0.00043% pass), 4-term 10.000000 (~0% pass)
  Taylor@10 at 30 deg N=3: 10.1366 m (+1.37% fail), N=4: 10.0030 m (+0.03% pass but 70x worse than Mac N=3) -> Maclaurin dominant for 0-30 deg.

TRADEOFF SUMMARY TABLE (0-30 deg, verified):
  Terms | Maclaurin max % (0-30) | Taylor@10 max % (0-30) | Ops | Valid @0.1%? | Margin
  1     | 4.7198% FAIL           | 8.61% FAIL             | 1   | NO (<4.44 deg) | --
  2     | 0.0652% PASS           | 8.61% FAIL (1 deg)     | 3   | YES (Mac only) | 1.5x thin
  3     | 0.00043% PASS          | 3.67% FAIL (1 deg)     | 5   | YES (Mac only) | 230x robust
  4     | ~0% PASS               | 0.0299% PASS           | 7   | YES both       | Mac 69x better

CONCLUSION: Adopt 2-term Maclaurin as minimum passing; RECOMMENDED 3-term Maclaurin as standard for safety margin (230x) and future-proofing.
            Document that sin~theta is only for <4.44 deg at 0.1% spec (1% at ~14 deg, 4% at ~25 deg per GT), and that Taylor@10 not advantageous for this 0-30 deg range -- it needs N=4 to pass where Maclaurin needs N=2.
"""

print(recommendation_text)

# Save recommendation to file
with open(REC_TXT, "w", encoding="utf-8") as f:
    f.write(recommendation_text)
print(f"Saved written recommendation -> {REC_TXT}")
print()

# ==============================================================
# REQUIRED PYTHON OUTPUT -- PLOTS
# ==============================================================
print("=" * 78)
print("GENERATING PLOTS -- Combined + Individual Deliverables")
print("=" * 78)

# Prepare data for plots
# 1. Convergence data: terms 1..7 for several angles
terms_axis = np.arange(1, 8)
angles_for_conv = [1, 5, 10, 15, 20, 30]
colors_conv = plt.cm.tab10(np.linspace(0, 1, len(angles_for_conv)))

mac_conv = {}
tay_conv = {}
for ang in angles_for_conv:
    mac_conv[ang] = []
    tay_conv[ang] = []
    exact = y_exact(ang)
    for N in terms_axis:
        mac_conv[ang].append(pct_error(y_mac(ang, N), exact))
        tay_conv[ang].append(pct_error(y_tay(ang, N), exact))

# 2. Function comparison: dense theta 0-35 deg
deg_dense = np.linspace(0, 35, 400)
rad_dense = np.radians(deg_dense)
exact_dense = np.array([math.sin(r) for r in rad_dense])
mac_dense = {}
for N in [1, 2, 3, 4]:
    mac_dense[N] = np.array([sin_maclaurin(r, N) for r in rad_dense])
tay_dense = {}
for N in [1, 2, 3, 4]:
    tay_dense[N] = np.array([sin_taylor(r, A_TAYLOR_RAD, N) for r in rad_dense])

# 3. Error comparison arrays for bar charts
err_mac_abs_N2 = [abs(y_mac(a,2)-y_exact(a)) for a in ANGLES_DEG]
err_tay_abs_N2 = [abs(y_tay(a,2)-y_exact(a)) for a in ANGLES_DEG]
err_mac_pct_N3 = [pct_error(y_mac(a,3), y_exact(a)) for a in ANGLES_DEG]
err_tay_pct_N3 = [pct_error(y_tay(a,3), y_exact(a)) for a in ANGLES_DEG]

# 4. Vertical y and pct error vs angle for each N (Maclaurin)
y_mac_curves = {}
for N in [1,2,3,4]:
    y_mac_curves[N] = np.array([y_mac(d, N) for d in deg_dense])
y_exact_dense = np.array([y_exact(d) for d in deg_dense])

# ------------------- COMBINED FIGURE (3 rows x 2 cols = 6 panels) -------------------
fig = plt.figure(figsize=(16, 14))
gs = fig.add_gridspec(3, 3, hspace=0.45, wspace=0.35)
fig.suptitle("Civil Engineering Series Exercise -- Combined Deliverables  |  y = L sin(theta), L=20 m, <0.1% tolerance\n"
             "Convergence + Function Comparison + Error Comparison  |  Author: Espenilla",
             fontsize=13, fontweight="bold", y=0.98)

# (0,0) Convergence Maclaurin
ax = fig.add_subplot(gs[0, 0])
for idx, ang in enumerate(angles_for_conv):
    ax.semilogy(terms_axis, mac_conv[ang], marker="o", linewidth=1.8, markersize=4, color=colors_conv[idx], label=f"{ang}°")
ax.axhline(0.1, color="red", linestyle="--", linewidth=1.2, label="0.1% tol")
ax.set_xticks(terms_axis)
ax.set_xlabel("Number of terms N")
ax.set_ylabel("% error (log scale)")
ax.set_title("(A) Maclaurin Convergence (% err vs N)", fontsize=10, fontweight="bold")
ax.grid(True, which="both", linestyle="--", alpha=0.5)
ax.legend(fontsize=6, ncol=2)
ax.set_ylim(1e-4, 10)

# (0,1) Convergence Taylor
ax2 = fig.add_subplot(gs[0, 1])
for idx, ang in enumerate(angles_for_conv):
    ax2.semilogy(terms_axis, tay_conv[ang], marker="s", linewidth=1.6, markersize=4, color=colors_conv[idx], label=f"{ang}°")
ax2.axhline(0.1, color="red", linestyle="--", linewidth=1.2, label="0.1% tol")
ax2.set_xticks(terms_axis)
ax2.set_xlabel("Number of terms N")
ax2.set_ylabel("% error (log scale)")
ax2.set_title("(B) Taylor @10° Convergence (% err vs N)", fontsize=10, fontweight="bold")
ax2.grid(True, which="both", linestyle="--", alpha=0.5)
ax2.legend(fontsize=6, ncol=2)
ax2.set_ylim(1e-4, 20)

# (0,2) Function comparison Maclaurin
ax3 = fig.add_subplot(gs[0, 2])
ax3.plot(deg_dense, exact_dense, color="black", linewidth=2.2, label="exact sinθ")
for N, col, ls in [(1, "#d62728", "--"), (2, "#ff7f0e", "-."), (3, "#2ca02c", "-"), (4, "#1f77b4", ":")]:
    ax3.plot(deg_dense, mac_dense[N], color=col, linestyle=ls, linewidth=1.5, label=f"Mac N={N}")
ax3.set_xlabel("θ (degrees)")
ax3.set_ylabel("sin(θ)")
ax3.set_title("(C) Function: Exact vs Maclaurin", fontsize=10, fontweight="bold")
ax3.set_xlim(0,35)
ax3.set_ylim(-0.05, 0.65)
ax3.grid(True, linestyle="--", alpha=0.5)
ax3.legend(fontsize=6)

# (1,0) Function comparison Taylor
ax4 = fig.add_subplot(gs[1, 0])
ax4.plot(deg_dense, exact_dense, color="black", linewidth=2.2, label="exact sinθ")
for N, col, ls in [(1, "#8c564b", "--"), (2, "#e377c2", "-."), (3, "#7f7f7f", "-"), (4, "#17becf", ":")]:
    ax4.plot(deg_dense, tay_dense[N], color=col, linestyle=ls, linewidth=1.5, label=f"Taylor N={N}")
ax4.axvline(A_TAYLOR_DEG, color="red", linestyle=":", linewidth=1.4, label="center 10°")
ax4.set_xlabel("θ (degrees)")
ax4.set_ylabel("sin(θ)")
ax4.set_title("(D) Function: Exact vs Taylor @10°", fontsize=10, fontweight="bold")
ax4.set_xlim(0,35)
ax4.set_ylim(-0.05, 0.65)
ax4.grid(True, linestyle="--", alpha=0.5)
ax4.legend(fontsize=6)

# (1,1) Absolute error comparison at N=2 and N=3
ax5 = fig.add_subplot(gs[1, 1])
x_pos = np.arange(len(ANGLES_DEG))
w = 0.20
b1 = ax5.bar(x_pos -1.5*w, err_mac_abs_N2, width=w, color="#4A90E2", edgecolor="white", label="Mac N=2 abs")
b2 = ax5.bar(x_pos -0.5*w, err_tay_abs_N2, width=w, color="#F5A623", edgecolor="white", label="Tay N=2 abs")
b3 = ax5.bar(x_pos +0.5*w, [abs(y_mac(a,3)-y_exact(a)) for a in ANGLES_DEG], width=w, color="#2ca02c", edgecolor="white", label="Mac N=3 abs")
b4 = ax5.bar(x_pos +1.5*w, [abs(y_tay(a,3)-y_exact(a)) for a in ANGLES_DEG], width=w, color="#d62728", edgecolor="white", label="Tay N=3 abs")
ax5.set_xticks(x_pos)
ax5.set_xticklabels([f"{a}°" for a in ANGLES_DEG], fontsize=8)
ax5.set_ylabel("Absolute error (m)  log scale")
ax5.set_yscale("log")
ax5.set_title("(E) Absolute Error: Mac vs Tay (N=2,3)", fontsize=10, fontweight="bold")
ax5.grid(True, which="both", linestyle="--", alpha=0.5)
ax5.legend(fontsize=6)
# annotate worst
for i, ang in enumerate(ANGLES_DEG):
    if err_mac_abs_N2[i] > 0.1:
        ax5.text(x_pos[i]-1.5*w, err_mac_abs_N2[i]*1.15, f"{err_mac_abs_N2[i]:.2f}", ha="center", va="bottom", fontsize=5, rotation=90)

# (1,2) Percentage error at N=3
ax6 = fig.add_subplot(gs[1, 2])
b5 = ax6.bar(x_pos -0.2, err_mac_pct_N3, width=0.35, color="#1f77b4", edgecolor="white", label="Mac N=3")
b6 = ax6.bar(x_pos +0.2, err_tay_pct_N3, width=0.35, color="#ff7f0e", edgecolor="white", label="Tay N=3")
ax6.axhline(0.1, color="red", linestyle="--", linewidth=1.4, label="0.1% tol")
ax6.set_xticks(x_pos)
ax6.set_xticklabels([f"{a}°" for a in ANGLES_DEG], fontsize=8)
ax6.set_ylabel("% error")
ax6.set_yscale("log")
ax6.set_title("(F) % Error Comparison N=3 (log)", fontsize=10, fontweight="bold")
ax6.grid(True, which="both", linestyle="--", alpha=0.5)
ax6.legend(fontsize=6)
ax6.set_ylim(5e-4, 2)
# annotate values
for i, (m,t) in enumerate(zip(err_mac_pct_N3, err_tay_pct_N3)):
    ax6.text(x_pos[i]-0.2, m*1.2, f"{m:.3f}%", ha="center", va="bottom", fontsize=5, rotation=90, color="#0B5394")
    ax6.text(x_pos[i]+0.2, t*1.2, f"{t:.3f}%", ha="center", va="bottom", fontsize=5, rotation=90, color="#7B2D26")

# (2,0:2) Vertical component y vs angle with error inset - span 2 columns
ax7 = fig.add_subplot(gs[2, 0:2])
ax7.plot(deg_dense, y_exact_dense, color="black", linewidth=2.5, label="exact y = L sinθ")
for N, col, ls in [(1, "#d62728", "--"), (2, "#ff7f0e", "-."), (3, "#2ca02c", "-"), (4, "#1f77b4", "-")]:
    ax7.plot(deg_dense, y_mac_curves[N], color=col, linestyle=ls, linewidth=1.6, label=f"Mac N={N}")
ax7.set_xlabel("θ (degrees)")
ax7.set_ylabel("y = L sinθ (m), L=20 m")
ax7.set_title("(G) Vertical Component: Exact vs Maclaurin Approx (N=1..4)", fontsize=10, fontweight="bold")
ax7.set_xlim(0,35)
ax7.set_ylim(0, 12)
ax7.grid(True, linestyle="--", alpha=0.5)
ax7.legend(fontsize=7, ncol=2)

# (2,2) % error vs angle for Maclaurin 1-4
ax8 = fig.add_subplot(gs[2, 2])
for N, col in [(1, "#d62728"), (2, "#ff7f0e"), (3, "#2ca02c"), (4, "#1f77b4")]:
    pct_curve = np.array([pct_error(y_mac(d, N), y_exact(d)) for d in deg_dense])
    # avoid zero for log
    pct_curve = np.where(pct_curve < 1e-8, 1e-8, pct_curve)
    ax8.semilogy(deg_dense, pct_curve, color=col, linewidth=1.7, label=f"N={N}")
ax8.axhline(0.1, color="red", linestyle="--", linewidth=1.4, label="0.1% tol")
ax8.axhline(1.0, color="orange", linestyle=":", linewidth=1.2, label="1% tol")
# mark critical angles
ax8.axvline(4.5, color="#7D3C98", linestyle=":", linewidth=1.2, alpha=0.8)
ax8.text(4.5, 0.02, "4.5°\ncrit 0.1%", ha="center", va="bottom", fontsize=6, color="#7D3C98",
         bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#CCCCCC"))
ax8.set_xlabel("θ (degrees)")
ax8.set_ylabel("% error (log)")
ax8.set_title("(H) % Error vs Angle (Maclaurin)", fontsize=10, fontweight="bold")
ax8.set_xlim(0,35)
ax8.set_ylim(1e-4, 10)
ax8.grid(True, which="both", linestyle="--", alpha=0.5)
ax8.legend(fontsize=6)

fig.tight_layout(rect=[0, 0.02, 1, 0.95])
fig.savefig(FIG_COMBINED, dpi=300, bbox_inches="tight")
print(f"Saved COMBINED figure -> {FIG_COMBINED}")

# Also save individual figures for deliverable checklist
# Convergence individual
fig_c = plt.figure(figsize=(10, 4.5))
gsc = fig_c.add_gridspec(1, 2, wspace=0.30)
fig_c.suptitle("Convergence Plot -- % Error vs Number of Terms", fontweight="bold", fontsize=11)
ac = fig_c.add_subplot(gsc[0,0])
for idx, ang in enumerate(angles_for_conv):
    ac.semilogy(terms_axis, mac_conv[ang], marker="o", linewidth=1.8, color=colors_conv[idx], label=f"{ang}°")
ac.axhline(0.1, color="red", linestyle="--", label="0.1%")
ac.set_xticks(terms_axis)
ac.set_xlabel("N terms")
ac.set_ylabel("% error (log)")
ac.set_title("Maclaurin")
ac.grid(True, which="both", linestyle="--", alpha=0.5)
ac.legend(fontsize=7, ncol=2)
ac = fig_c.add_subplot(gsc[0,1])
for idx, ang in enumerate(angles_for_conv):
    ac.semilogy(terms_axis, tay_conv[ang], marker="s", linewidth=1.8, color=colors_conv[idx], label=f"{ang}°")
ac.axhline(0.1, color="red", linestyle="--", label="0.1%")
ac.set_xticks(terms_axis)
ac.set_xlabel("N terms")
ac.set_ylabel("% error (log)")
ac.set_title("Taylor @10°")
ac.grid(True, which="both", linestyle="--", alpha=0.5)
ac.legend(fontsize=7, ncol=2)
fig_c.tight_layout(rect=[0,0,1,0.92])
fig_c.savefig(FIG_CONV, dpi=300, bbox_inches="tight")
print(f"Saved Convergence -> {FIG_CONV}")

# Function comparison individual
fig_f = plt.figure(figsize=(10, 4.5))
gsf = fig_f.add_gridspec(1, 2, wspace=0.25)
fig_f.suptitle("Function Comparison -- Exact sin(θ) vs Approximations", fontweight="bold", fontsize=11)
af = fig_f.add_subplot(gsf[0,0])
af.plot(deg_dense, exact_dense, color="black", linewidth=2.2, label="exact")
for N, col, ls in [(1, "#d62728", "--"), (2, "#ff7f0e", "-."), (3, "#2ca02c", "-"), (4, "#1f77b4", ":")]:
    af.plot(deg_dense, mac_dense[N], color=col, linestyle=ls, linewidth=1.4, label=f"Mac N={N}")
af.set_xlabel("θ (deg)")
af.set_ylabel("sinθ")
af.set_title("Maclaurin")
af.grid(True, linestyle="--", alpha=0.5)
af.legend(fontsize=7)
af = fig_f.add_subplot(gsf[0,1])
af.plot(deg_dense, exact_dense, color="black", linewidth=2.2, label="exact")
for N, col, ls in [(1, "#8c564b", "--"), (2, "#e377c2", "-."), (3, "#7f7f7f", "-"), (4, "#17becf", ":")]:
    af.plot(deg_dense, tay_dense[N], color=col, linestyle=ls, linewidth=1.4, label=f"Tay N={N}")
af.axvline(10, color="red", linestyle=":", label="center 10°")
af.set_xlabel("θ (deg)")
af.set_ylabel("sinθ")
af.set_title("Taylor @10°")
af.grid(True, linestyle="--", alpha=0.5)
af.legend(fontsize=7)
fig_f.tight_layout(rect=[0,0,1,0.92])
fig_f.savefig(FIG_FUNC, dpi=300, bbox_inches="tight")
print(f"Saved Function Comparison -> {FIG_FUNC}")

# Error comparison individual
fig_e = plt.figure(figsize=(10, 4.5))
gse = fig_e.add_gridspec(1, 2, wspace=0.28)
fig_e.suptitle("Error Comparison -- Maclaurin vs Taylor", fontweight="bold", fontsize=11)
ae = fig_e.add_subplot(gse[0,0])
x = np.arange(len(ANGLES_DEG))
w=0.2
ae.bar(x-1.5*w, err_mac_abs_N2, width=w, color="#4A90E2", label="Mac N2")
ae.bar(x-0.5*w, err_tay_abs_N2, width=w, color="#F5A623", label="Tay N2")
ae.bar(x+0.5*w, [abs(y_mac(a,3)-y_exact(a)) for a in ANGLES_DEG], width=w, color="#2ca02c", label="Mac N3")
ae.bar(x+1.5*w, [abs(y_tay(a,3)-y_exact(a)) for a in ANGLES_DEG], width=w, color="#d62728", label="Tay N3")
ae.set_xticks(x)
ae.set_xticklabels([f"{a}°" for a in ANGLES_DEG])
ae.set_ylabel("Abs error (m) log")
ae.set_yscale("log")
ae.set_title("Absolute Error")
ae.grid(True, which="both", linestyle="--", alpha=0.5)
ae.legend(fontsize=7)
ae2 = fig_e.add_subplot(gse[0,1])
ae2.bar(x-0.2, err_mac_pct_N3, width=0.35, color="#1f77b4", label="Mac N3")
ae2.bar(x+0.2, err_tay_pct_N3, width=0.35, color="#ff7f0e", label="Tay N3")
ae2.axhline(0.1, color="red", linestyle="--", label="0.1%")
ae2.set_xticks(x)
ae2.set_xticklabels([f"{a}°" for a in ANGLES_DEG])
ae2.set_ylabel("% error log")
ae2.set_yscale("log")
ae2.set_title("% Error at N=3")
ae2.grid(True, which="both", linestyle="--", alpha=0.5)
ae2.legend(fontsize=7)
fig_e.tight_layout(rect=[0,0,1,0.92])
fig_e.savefig(FIG_ERR, dpi=300, bbox_inches="tight")
print(f"Saved Error Comparison -> {FIG_ERR}")

# --- Show figures interactively so images appear when you run the script ---
# Set LAB04_NO_SHOW=1 or pass --no-show to skip popups (useful for automated runs)
NO_SHOW = os.environ.get("LAB04_NO_SHOW", "0") == "1" or "--no-show" in sys.argv
print("Displaying figures... (close the figure windows to finish)")
if not NO_SHOW:
    try:
        plt.show()
    except Exception as e:
        print(f"plt.show() failed: {e}")
else:
    print("Skipped plt.show() (--no-show / LAB04_NO_SHOW=1)")

# Backup: also open the saved PNGs in the default image viewer,
# so images still appear even if the interactive backend is unavailable.
def _open_image(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # noqa: S606 -- local file, user requested display
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
        print(f"Opened in viewer -> {path}")
    except Exception as e:
        print(f"Could not auto-open {path}: {e}")

if not NO_SHOW:
    for _p in [FIG_COMBINED, FIG_CONV, FIG_FUNC, FIG_ERR]:
        if os.path.exists(_p):
            _open_image(_p)
else:
    print("Skipped auto-open in viewer (--no-show / LAB04_NO_SHOW=1)")

plt.close('all')

print()
print("=" * 78)
print("ALL DELIVERABLES DONE")
print(f"  Combined figure: {FIG_COMBINED}")
print(f"  Convergence: {FIG_CONV}")
print(f"  Function: {FIG_FUNC}")
print(f"  Error: {FIG_ERR}")
print(f"  Recommendation txt: {REC_TXT}")
print("=" * 78)
