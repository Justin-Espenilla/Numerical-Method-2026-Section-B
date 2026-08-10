"""
================================================================================
 LAB 04 DEMO  -  The integral as accumulation
 Numerical Methods Laboratory  |  Prepared by Engr. Escranda
================================================================================

WHAT THIS PROGRAM IS
    The worked example from Lab Lecture 4, written out in full. Read it from
    top to bottom: every block is numbered and explained before it runs.

HOW TO RUN IT
    python lab04_demo.py

    It prints a set of tables to the screen and writes one figure to the
    ./figures/ folder. Nothing else is required.

HOW THE PROGRAM IS ORGANISED
    SETUP    imports, output folder, plot settings
    PART 1   define the three integration rules
    PART 2   state the exact answer to compare against
    PART 3   run the error-ratio study that proves each rule's order
    PART 4   plot the three error curves on log-log axes

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
# numpy (np)  : array arithmetic. Every formula below acts on whole arrays at
#               once instead of looping element by element.
# matplotlib  : the plotting library. "Agg" is a non-interactive backend: it
#               draws straight to a PNG file and never opens a window, which is
#               what we want when the program is run from a terminal.
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")          # WHY: choose the backend BEFORE importing pyplot
import matplotlib.pyplot as plt

# ------------------------------------------------------------------------------
# SETUP 2 of 3  -  where the figure will be written
# ------------------------------------------------------------------------------
# __file__ is this script's own path. Taking its folder means the figure lands
# next to the program no matter which directory you launched it from.
FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(FIG, exist_ok=True)     # exist_ok=True: do nothing if it already exists

# ------------------------------------------------------------------------------
# SETUP 3 of 3  -  plot appearance, set once for the whole program
# ------------------------------------------------------------------------------
# 150 dpi is the minimum resolution accepted for submitted figures.
# The three colours are the course palette; naming them here means a single
# edit changes every plot.
plt.rcParams.update({"figure.dpi": 150, "font.size": 9,
                     "axes.grid": True, "grid.alpha": .3})
BLUE, DARK, ORANGE = "#0b5fa5", "#08436f", "#8a5b00"

# ==============================================================================
# PART 1  -  THE THREE RULES
# ==============================================================================
# All three approximate the same integral. They differ ONLY in what shape they
# assume the function has between the samples: flat, straight, or parabolic.
# That single choice is worth five orders of magnitude in accuracy.

def left_rect(f, a, b, n):
    """Left Riemann sum: a flat top on every strip.  Error = O(h).

        I ~ h * ( f0 + f1 + ... + f(n-1) )

    It uses the height at the LEFT edge of each strip and ignores the right,
    which is why it is only first order.
    """
    h = (b - a) / n
    # a + h*arange(n) gives the n left edges: a, a+h, a+2h, ... a+(n-1)h.
    # The right-hand end b is deliberately not included.
    return h * np.sum(f(a + h * np.arange(n)))


def trapezoid(f, a, b, n):
    """Composite trapezoidal rule: a straight line across each strip. O(h^2).

        I ~ h * [ f0/2 + f1 + f2 + ... + f(n-1) + fn/2 ]

    WHY THE HALVES AT THE ENDS
        Every interior sample is the right edge of one trapezoid and the left
        edge of the next, so it is counted twice. The two end samples belong to
        one trapezoid each, so they count once. The 1-2-2-...-2-1 pattern is a
        head count, not a formula to memorise.
    """
    h = (b - a) / n
    y = f(np.linspace(a, b, n + 1))          # n strips need n+1 sample points
    return h * (y[0] / 2 + y[1:-1].sum() + y[-1] / 2)


def simpson(f, a, b, n):
    """Composite Simpson 1/3 rule: a parabola through each PAIR of strips. O(h^4).

        I ~ (h/3) * [ f0 + 4f1 + 2f2 + 4f3 + ... + 4f(n-1) + fn ]

    WHY n MUST BE EVEN
        The rule consumes strips two at a time, because it takes three points
        to define a parabola. An odd n would leave one strip unpaired.

    THE SLICING
        y[1:-1:2] is every ODD-indexed interior point  -> weight 4
        y[2:-1:2] is every EVEN-indexed interior point -> weight 2
    """
    if n % 2:
        raise ValueError("Simpson's 1/3 rule needs an even number of strips.")
    h = (b - a) / n
    y = f(np.linspace(a, b, n + 1))
    return h / 3 * (y[0] + 4 * y[1:-1:2].sum() + 2 * y[2:-1:2].sum() + y[-1])


# ==============================================================================
# PART 2  -  THE TEST INTEGRAL
# ==============================================================================
# We integrate e^x from 0 to 1. Its antiderivative is e^x, so the exact answer
# is e - 1. Having an exact value is what lets us measure a true error.

exact = np.e - 1
print("PART 2  THE TEST INTEGRAL")
print("   I = integral of e^x from 0 to 1 = e - 1")
print(f"     = {exact:.12f}\n")


# ==============================================================================
# PART 3  -  THE ERROR-RATIO STUDY
# ==============================================================================
# THE IDEA: an O(h^p) rule has error proportional to h^p. Doubling n halves h,
# so the error must fall by a factor of 2^p:
#
#       O(h)    -> ratio 2        O(h^2) -> ratio 4        O(h^4) -> ratio 16
#
# The ratio column is therefore a direct measurement of the ORDER of a method,
# and it is the fastest way to find a bug in an integration routine.

print("PART 3  DOUBLE n AND WATCH THE ERRORS FALL")
print(f"   {'n':>6}{'rectangle':>14}{'ratio':>8}"
      f"{'trapezoid':>14}{'ratio':>8}{'Simpson':>14}{'ratio':>8}")

prev_r = prev_t = prev_s = None          # previous errors, for the ratios
for n in (4, 8, 16, 32, 64, 128):
    err_r = abs(left_rect(np.exp, 0, 1, n) - exact)
    err_t = abs(trapezoid(np.exp, 0, 1, n) - exact)
    err_s = abs(simpson(np.exp, 0, 1, n) - exact)

    # A small helper keeps the print statement readable: it formats the ratio,
    # or a dash on the first row where there is nothing to compare against.
    def ratio(prev, now):
        return f"{prev / now:.2f}" if prev else "-"

    print(f"   {n:>6}{err_r:>14.3e}{ratio(prev_r, err_r):>8}"
          f"{err_t:>14.3e}{ratio(prev_t, err_t):>8}"
          f"{err_s:>14.3e}{ratio(prev_s, err_s):>8}")
    prev_r, prev_t, prev_s = err_r, err_t, err_s

print("\n   The ratios settle on 2, 4 and 16 - the orders O(h), O(h^2), O(h^4).")
print("   Note that all three rules use the SAME number of function")
print("   evaluations. The accuracy difference is bought entirely by assuming")
print("   a better shape between the samples.\n")


# ==============================================================================
# PART 4  -  THE LOG-LOG ERROR PLOT
# ==============================================================================
# WHY LOG-LOG: if error = C * h^p then log(error) = log(C) + p*log(h). On
# log-log axes a power law is a STRAIGHT LINE whose SLOPE is the order p. The
# eye can then read the order directly off the figure.

print("PART 4  BUILDING THE FIGURE")

ns = np.array([4, 8, 16, 32, 64, 128, 256])
hs = 1.0 / ns                                    # the step size for each n

fig, ax = plt.subplots(figsize=(5.2, 3.5))

# Loop over the three rules, drawing one line each. Bundling the name, the
# function and the colour into a tuple keeps the loop short and the styling
# consistent.
for name, rule, colour in (("rectangle, O(h)", left_rect, "#9bb8d3"),
                           ("trapezoid, O(h^2)", trapezoid, BLUE),
                           ("Simpson, O(h^4)", simpson, DARK)):
    errors = [abs(rule(np.exp, 0, 1, int(n)) - exact) for n in ns]

    # np.polyfit fits a straight line to the log-log data; the first returned
    # coefficient is the slope, which is the measured order of the rule.
    slope = np.polyfit(np.log10(hs), np.log10(errors), 1)[0]

    ax.loglog(hs, errors, "o-", color=colour, ms=3.5,
              label=f"{name}   measured slope {slope:.2f}")

ax.set_xlabel("step size h")
ax.set_ylabel("|error|")
ax.set_title("Lab 4 demo: three rules, three slopes")
ax.legend(fontsize=7)

fig.tight_layout()
out = f"{FIG}/demo_lab04.png"
fig.savefig(out)
plt.close(fig)
print(f"   figure written to {out}")
