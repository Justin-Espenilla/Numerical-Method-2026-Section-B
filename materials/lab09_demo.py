"""
================================================================================
 LAB 09 DEMO  -  Taylor series and Newton-Raphson for normal depth
 Numerical Methods Laboratory  |  Prepared by Engr. Escranda
================================================================================

WHAT THIS PROGRAM IS
    The worked example from Lab Lecture 9, written out in full. Read it from
    top to bottom: every block is numbered and explained before it runs.

HOW TO RUN IT
    python lab09_demo.py

    It prints a set of tables to the screen and writes one figure to the
    ./figures/ folder. Nothing else is required.

HOW THE PROGRAM IS ORGANISED
    SETUP    imports, output folder, plot settings
    PART 1   define the Manning residual f(y) whose root is the normal depth
    PART 2   define its derivative by a centred difference
    PART 3   iterate Newton-Raphson and tabulate every step
    PART 4   measure the convergence: the digits double each iteration
    PART 5   show the same Taylor expansion producing the difference formulas
    PART 6   plot f(y) with the root marked

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
# PART 1  -  THE EQUATION THAT CANNOT BE REARRANGED
# ==============================================================================
# A trapezoidal drainage channel must carry 15 m3/s. Manning's equation gives
# the discharge for a GIVEN depth; the designer needs the reverse. The depth
# appears inside the area, inside the wetted perimeter, and inside a two-thirds
# power. There is no algebraic rearrangement, and there never will be.
#
# So we stop trying to solve and start trying to search: move everything to one
# side and hunt for the value of y that makes it zero.

B, Z, N_MANNING, S0, Q_DESIGN = 3.0, 2.0, 0.025, 0.001, 15.0
#   B  base width (m)              Z  side slope, Z horizontal to 1 vertical
#   N  Manning's roughness         S0 bed slope
#   Q  design discharge (m3/s)


def f(y):
    """Manning residual. Its root is the normal depth.

        f(y) = (1/n) A R^(2/3) sqrt(S) - Q

        A = (B + Z y) y                    flow area, m2
        P = B + 2 y sqrt(1 + Z^2)          wetted perimeter, m
        R = A / P                          hydraulic radius, m

    A NOTE ON THE HYDRAULICS, WHICH MATTERS MORE THAN THE NUMERICS
        The wetted perimeter counts only the surfaces in contact with the bed
        and banks - not the free water surface. The exponent on R is 2/3, not
        3/2. An error in either still runs, still converges, and returns a
        confidently wrong depth.
    """
    A = (B + Z * y) * y
    P = B + 2 * y * np.sqrt(1 + Z * Z)
    R = A / P
    return (1 / N_MANNING) * A * R ** (2 / 3) * np.sqrt(S0) - Q_DESIGN


# ==============================================================================
# PART 2  -  THE DERIVATIVE
# ==============================================================================

def fprime(y, h=1e-6):
    """df/dy by the centred difference of Lab 1.

    WHY NUMERICALLY AND NOT BY HAND?
        The analytical derivative exists and is worth deriving - it costs one
        function evaluation per step instead of two, and it removes the
        perturbation size as a source of error. But the numerical version needs
        no algebra, cannot be mis-differentiated, and is accurate to O(h^2).
        For a one-off design calculation it is the right trade.
    """
    return (f(y + h) - f(y - h)) / (2 * h)


# ==============================================================================
# PART 3  -  NEWTON-RAPHSON, WHICH IS JUST A TWO-TERM TAYLOR SERIES
# ==============================================================================
# Expand f about the current guess and keep two terms:
#
#       0 = f(y_i) + f'(y_i) (y_{i+1} - y_i)
#
# Solve for the next guess:
#
#       y_{i+1} = y_i - f(y_i) / f'(y_i)
#
# That is all Newton-Raphson is: the tangent line from Taylor's expansion,
# solved for where it crosses zero. The neglected term is the h^2 curvature
# term, and because the error is squared at each step the number of correct
# digits roughly DOUBLES per iteration.

print("PART 3  NEWTON-RAPHSON FROM AN INITIAL GUESS OF 1.0 m")
print(f"   channel: B = {B} m, Z = {Z}, n = {N_MANNING}, "
      f"S = {S0}, Q = {Q_DESIGN} m3/s")
print(f"\n   {'i':>3}{'y_i':>14}{'f(y_i)':>15}{'f prime':>13}"
      f"{'y_i+1':>14}{'ea %':>12}")

y = 1.0
iterates = [y]
for i in range(6):
    fy = f(y)
    fp = fprime(y)

    # CHECK: a vanishing derivative means a flat tangent, which throws the next
    # iterate to infinity. In channel hydraulics this happens near critical
    # depth. Guard it rather than letting it produce inf.
    if abs(fp) < 1e-14:
        raise RuntimeError("derivative vanished; Newton cannot proceed")

    y_new = y - fy / fp
    ea = abs((y_new - y) / y_new) * 100          # approximate relative error
    print(f"   {i:>3}{y:>14.8f}{fy:>15.8f}{fp:>13.6f}{y_new:>14.8f}{ea:>12.3e}")
    y = y_new
    iterates.append(y)

# The final geometry, reported in the units an engineer needs.
A = (B + Z * y) * y
P = B + 2 * y * np.sqrt(1 + Z * Z)
print(f"\n   normal depth   y = {y:.6f} m")
print(f"   flow area      A = {A:.4f} m2")
print(f"   wetted perim.  P = {P:.4f} m")
print(f"   hydraulic rad. R = {A/P:.4f} m")
print(f"   mean velocity  V = Q/A = {Q_DESIGN/A:.4f} m/s\n")


# ==============================================================================
# PART 4  -  MEASURING THE CONVERGENCE
# ==============================================================================
print("PART 4  HOW FAST IS QUADRATIC CONVERGENCE?")
print(f"   {'i':>3}{'|y_i - root|':>16}{'log10 of it':>14}")

root = y
for i, v in enumerate(iterates[:-1]):
    e = abs(v - root)
    if e > 0:
        print(f"   {i:>3}{e:>16.3e}{np.log10(e):>14.2f}")

print("   Read the log column: each value is roughly DOUBLE the previous one in")
print("   magnitude. Two correct digits become four, four become eight, eight")
print("   become sixteen. Bisection, by comparison, gains about 0.3 of a digit")
print("   per iteration and would need some 45 iterations to match this.")
print("   The price of that speed is fragility - Newton can and does diverge.\n")


# ==============================================================================
# PART 5  -  THE SAME EXPANSION GIVES THE DIFFERENCE FORMULAS
# ==============================================================================
# Truncating Taylor after the first derivative term gives the forward
# difference, error O(h). Writing the expansion for +h and -h and SUBTRACTING
# cancels the h^2 terms exactly, giving the centred difference, error O(h^2).
# That is the whole reason centred formulas are better for free.

print("PART 5  THE DIFFERENCE FORMULAS COME FROM THE SAME EXPANSION")

def g(x):
    return np.exp(x / 2) * np.sin(x)

def g_exact_prime(x):
    return np.exp(x / 2) * (0.5 * np.sin(x) + np.cos(x))

print(f"   {'h':>10}{'forward error':>16}{'ratio':>8}"
      f"{'centred error':>16}{'ratio':>8}")

prev_f = prev_c = None
for h in (0.2, 0.1, 0.05, 0.025):
    err_f = abs((g(1 + h) - g(1)) / h - g_exact_prime(1))
    err_c = abs((g(1 + h) - g(1 - h)) / (2 * h) - g_exact_prime(1))
    rf = f"{prev_f / err_f:.2f}" if prev_f else "-"
    rc = f"{prev_c / err_c:.2f}" if prev_c else "-"
    print(f"   {h:>10.4f}{err_f:>16.3e}{rf:>8}{err_c:>16.3e}{rc:>8}")
    prev_f, prev_c = err_f, err_c

print("   Ratios of 2 and 4: first order and second order, exactly as the")
print("   truncated expansions predict.\n")


# ==============================================================================
# PART 6  -  THE FIGURE
# ==============================================================================
print("PART 6  BUILDING THE FIGURE")

# Plotting f(y) before solving is always worth the six lines it costs: it shows
# how many roots exist, roughly where they are, and whether the physical range
# contains one.
ys = np.linspace(0.2, 4.0, 300)
fig, ax = plt.subplots(figsize=(5.2, 3.3))

ax.plot(ys, [f(v) for v in ys], color=BLUE, lw=1.5)
ax.axhline(0, color="k", lw=.7)                    # the level we are hunting
ax.plot(root, 0, "o", color=ORANGE, ms=7,
        label=f"normal depth {root:.3f} m")

ax.set_xlabel("depth y (m)")
ax.set_ylabel("f(y)   (m3/s)")
ax.set_title("Lab 9 demo: the root of Manning's residual")
ax.legend(fontsize=8)

fig.tight_layout()
out = f"{FIG}/demo_lab09.png"
fig.savefig(out)
plt.close(fig)
print(f"   figure written to {out}")
