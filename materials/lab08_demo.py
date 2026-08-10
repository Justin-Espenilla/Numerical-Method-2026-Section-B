"""
================================================================================
 LAB 08 DEMO  -  Infinite series and the cost of stopping
 Numerical Methods Laboratory  |  Prepared by Engr. Escranda
================================================================================

WHAT THIS PROGRAM IS
    The worked example from Lab Lecture 8, written out in full. Read it from
    top to bottom: every block is numbered and explained before it runs.

HOW TO RUN IT
    python lab08_demo.py

    It prints a set of tables to the screen and writes one figure to the
    ./figures/ folder. Nothing else is required.

HOW THE PROGRAM IS ORGANISED
    SETUP    imports, output folder, plot settings
    PART 1   define consolidation_U() - a series with a convergence test
    PART 2   sum it term by term at T = 0.2 and follow every number
    PART 3   show that the number of terms depends on WHERE you evaluate
    PART 4   a perfectly convergent series that still fails, and the fix
    PART 5   plot the term count against the time factor

HOW TO READ THE COMMENTS
    #  STEP n   marks a stage of the calculation
    #  WHY:     explains a decision that is not obvious from the code
    #  CHECK:   marks a line whose purpose is to verify, not to compute
================================================================================
"""

# ------------------------------------------------------------------------------
# SETUP 1 of 3  -  imports
# ------------------------------------------------------------------------------
# os          : builds the path to the figures folder in a way that works on
#               Windows, macOS and Linux without changing the code.
# numpy (np)  : array and matrix arithmetic.
# matplotlib  : the plotting library. "Agg" is a non-interactive backend: it
#               draws straight to a PNG file and never opens a window.
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")          # WHY: choose the backend BEFORE importing pyplot
import matplotlib.pyplot as plt

# ------------------------------------------------------------------------------
# SETUP 2 of 3  -  where the figure will be written
# ------------------------------------------------------------------------------
FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(FIG, exist_ok=True)

# ------------------------------------------------------------------------------
# SETUP 3 of 3  -  plot appearance, set once for the whole program
# ------------------------------------------------------------------------------
plt.rcParams.update({"figure.dpi": 150, "font.size": 9,
                     "axes.grid": True, "grid.alpha": .3})
BLUE, DARK, ORANGE = "#0b5fa5", "#08436f", "#8a5b00"

# ==============================================================================
# PART 1  -  A SERIES SUMMED PROPERLY
# ==============================================================================

def consolidation_U(T, es=1e-8, max_terms=5000):
    """Terzaghi's average degree of consolidation as a function of time factor T.

    THE SERIES
        U(T) = 1 - SUM over m of  (2 / M^2) * exp(-M^2 T)
        with  M = pi (2m + 1) / 2,  m = 0, 1, 2, ...

        U is the fraction of the primary settlement that has occurred, and T is
        the dimensionless time  T = cv t / H_dr^2.

    THE THREE FEATURES THAT MATTER, ALL COMMONLY OMITTED
        1. IT STOPS ON A MEASURED ERROR, NOT A TERM COUNT.
           The test is the approximate percent relative error

               ea = |(new sum - old sum) / new sum| * 100

           which is the change the last term made. A routine hard-wired to sum
           ten terms is accurate for late-time settlement and wrong for
           early-time settlement, and it can never tell you which case you are
           in.

        2. IT CAPS THE LOOP. A series that fails to converge must still
           terminate, and the caller must be able to detect that it did.

        3. IT REPORTS HOW HARD IT WORKED. Returning the term count and the
           final error turns an opaque number into a result with provenance.

    RETURNS
        (U, terms_used, ea)
    """
    # T = 0 is the boundary case: nothing has consolidated, and the series
    # converges infinitely slowly there. Handle it explicitly rather than
    # letting the loop grind to the cap.
    if T <= 0:
        return 0.0, 0, 0.0

    total = 0.0
    ea = float("inf")                     # so the first comparison never passes

    for m in range(max_terms):
        M = np.pi * (2 * m + 1) / 2
        term = (2 / M ** 2) * np.exp(-M ** 2 * T)

        old_total = total
        total += term

        if total > 0:
            ea = abs((total - old_total) / total) * 100
        if ea < es:
            return 1 - total, m + 1, ea

    return 1 - total, max_terms, ea


# ==============================================================================
# PART 2  -  TERM BY TERM, SO EVERY NUMBER CAN BE CHECKED BY HAND
# ==============================================================================
# Work the first term through with a calculator alongside this output:
#   M   = pi/2        = 1.570796
#   M^2               = 2.467401
#   2 / M^2           = 0.810569
#   exp(-2.467401 * 0.2) = exp(-0.493480) = 0.610500
#   product           = 0.494851

print("PART 2  TERM BY TERM AT T = 0.2")
print(f"   {'m':>3}{'M':>11}{'M^2':>12}{'term':>15}{'running sum':>15}"
      f"{'U':>11}{'ea %':>12}")

T = 0.2
total = 0.0
for m in range(4):
    M = np.pi * (2 * m + 1) / 2
    term = (2 / M ** 2) * np.exp(-M ** 2 * T)
    old_total = total
    total += term
    ea = abs((total - old_total) / total) * 100
    print(f"   {m:>3}{M:>11.6f}{M**2:>12.6f}{term:>15.9f}"
          f"{total:>15.9f}{1-total:>11.6f}{ea:>12.3e}")

print("   U(0.2) = 0.5041, the published value.")
print("   The second term contributes 0.2 % and the third 0.00003 %: each term")
print("   is about 500 times smaller than the last, because the exponent grows")
print("   as m^2. Two terms give three figures, three terms give six.\n")


# ==============================================================================
# PART 3  -  CONVERGENCE DEPENDS ON WHERE YOU EVALUATE
# ==============================================================================
# es is set from the Scarborough criterion, which converts a demand for
# significant figures into a tolerance:
#
#       es = (0.5 x 10^(2-n)) %      ->  6 figures: 5e-5 %

print("PART 3  HOW MANY TERMS? IT DEPENDS ENTIRELY ON T")
print(f"   {'T':>8}{'U(T)':>12}{'terms needed':>15}")

for T in (1.0, 0.5, 0.2, 0.05, 0.01, 0.001):
    U, terms, _ = consolidation_U(T, es=5e-5)      # 6 significant figures
    print(f"   {T:>8.3f}{U:>12.6f}{terms:>15}")

print("   Late in the process one or two terms suffice. Early in the process")
print("   the same accuracy costs twenty-seven. This is why the stopping")
print("   decision must be made by the code, not by the programmer.\n")


# ==============================================================================
# PART 4  -  A CONVERGENT SERIES THAT STILL FAILS
# ==============================================================================

def exp_series(x, n_terms=300):
    """Sum the Maclaurin series for e^x, and report the largest term used.

    THE RECURRENCE
        Each term is the previous term times x/k, so the whole sum costs two
        arithmetic operations per term - no factorials, no powers, no overflow.

    WHY RETURN THE LARGEST TERM
        It is the diagnostic. If the largest term is far bigger than the final
        answer, the leading digits have cancelled and what survives is noise.
    """
    term, total, largest = 1.0, 1.0, 1.0
    for k in range(1, n_terms):
        term *= x / k
        total += term
        largest = max(largest, abs(term))
    return total, largest


print("PART 4  SUBTRACTIVE CANCELLATION")
print(f"   {'x':>5}{'series':>16}{'true value':>16}{'error %':>12}"
      f"{'largest term':>16}")

for x in (-5, -10, -20):
    s, largest = exp_series(float(x))
    true = np.exp(x)
    print(f"   {x:>5}{s:>16.6e}{true:>16.6e}"
          f"{abs((s - true) / true) * 100:>12.2e}{largest:>16.2e}")

print("   The series for e^-20 converges for every real x - the mathematics is")
print("   sound. But its terms reach 4.3e+07 on the way to an answer of")
print("   2.1e-09. Sixteen digits of cancellation consume all the precision")
print("   double arithmetic has, and the result is wrong by 200 %.")

# THE FIX: compute e^+20, where every term is positive and nothing cancels,
# then take the reciprocal. Algebraically identical, numerically far better.
fixed = 1.0 / exp_series(20.0)[0]
print(f"\n   THE FIX: 1 / series(+20) = {fixed:.6e}")
print(f"            true value       = {np.exp(-20):.6e}")
print("   Same mathematics, different arithmetic, fifteen figures recovered.")
print("   Whenever a formula subtracts two nearly equal numbers, look for an")
print("   equivalent that does not.\n")


# ==============================================================================
# PART 5  -  THE FIGURE
# ==============================================================================
# A semilog x-axis is used because T spans three orders of magnitude. The
# vertical axis stays linear because the term count does not.

print("PART 5  BUILDING THE FIGURE")

Ts = np.logspace(-3, 0.3, 60)                       # 0.001 to about 2
terms = [consolidation_U(t, es=5e-5)[1] for t in Ts]

fig, ax = plt.subplots(figsize=(5.2, 3.2))
ax.semilogx(Ts, terms, "o-", color=BLUE, ms=3)

ax.set_xlabel("time factor T  (dimensionless)")
ax.set_ylabel("terms needed for 6 significant figures")
ax.set_title("Lab 8 demo: the cost of the series depends on T")

fig.tight_layout()
out = f"{FIG}/demo_lab08.png"
fig.savefig(out)
plt.close(fig)
print(f"   figure written to {out}")
