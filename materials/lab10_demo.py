"""
================================================================================
 LAB 10 DEMO  -  Capstone: beam deflection by finite differences
 Numerical Methods Laboratory  |  Prepared by Engr. Escranda
================================================================================

WHAT THIS PROGRAM IS
    The worked example from Lab Lecture 10, written out in full. Read it from
    top to bottom: every block is numbered and explained before it runs.

HOW TO RUN IT
    python lab10_demo.py

    It prints a set of tables to the screen and writes one figure to the
    ./figures/ folder. Nothing else is required.

HOW THE PROGRAM IS ORGANISED
    SETUP    imports, output folder, plot settings
    PART 1   define moment()  - the load effect from statics
    PART 2   define beam()    - discretise the governing equation into a matrix
    PART 3   verify against the exact answer and measure the convergence ratio
    PART 4   improve the result by Richardson extrapolation
    PART 5   differentiate the deflection to get the support rotation
    PART 6   plot the deflected shape and the convergence curve

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
# THE PROBLEM
# ==============================================================================
# A simply supported beam of span L carries a uniformly distributed load w.
# The governing equation relates curvature to bending moment:
#
#       d2y/dx2 = M(x) / (E I)          with   y(0) = y(L) = 0
#
# For constant EI this has a closed-form answer, which is precisely why we
# start here: it is the only case in which the method can be CHECKED.

L, W, EI = 6.0, 20.0, 2.0e5          # m, kN/m, kN.m2


def moment(x):
    """Bending moment for a simply supported span under a UDL, kN.m.

        M(x) = w x (L - x) / 2

    Derived from statics: each reaction is wL/2, so
    M(x) = (wL/2)x - w x^2/2, which factorises to the form above.
    """
    return W * x * (L - x) / 2.0


# ==============================================================================
# PART 2  -  TURNING THE DIFFERENTIAL EQUATION INTO A MATRIX
# ==============================================================================

def beam(n):
    """Deflection of the beam by finite differences, using n intervals.

    THE DISCRETISATION
        Replace the second derivative by the centred second difference from
        Lab 9:

            ( y[i-1] - 2 y[i] + y[i+1] ) / h^2  =  M_i / (E I)

        Multiply through by h^2 and the equation at node i becomes

            y[i-1] - 2 y[i] + y[i+1]  =  h^2 M_i / (E I)

        Writing that at every INTERIOR node gives n-1 equations in n-1 unknown
        deflections. The matrix is tridiagonal: each node couples only to its
        immediate neighbours.

    THE BOUNDARY CONDITIONS - WHERE MOST MARKS ARE LOST
        The supports are NOT equations in the system. They are known values,
        y = 0, that never enter it. The equation at the first interior node
        would have contained y[0], but y[0] = 0, so that term simply vanishes.
        This is why the matrix has n-1 rows and not n+1. A system one row too
        large still solves and still returns plausible numbers, which is what
        makes the error so dangerous.

    RETURNS
        (x, y) with the two support deflections included as zeros.
    """
    h = L / n
    x = np.linspace(0, L, n + 1)

    # STEP 1  build the coefficient matrix.
    # np.diag(v) puts v on the main diagonal; the second argument offsets it,
    # so k=1 is the superdiagonal and k=-1 the subdiagonal. The result is the
    # familiar 1, -2, 1 stencil.
    A = (np.diag(-2.0 * np.ones(n - 1))
         + np.diag(np.ones(n - 2), 1)
         + np.diag(np.ones(n - 2), -1))

    # STEP 2  build the right-hand side, one entry per interior node.
    # x[1:n] is exactly the interior: it excludes both supports.
    rhs = h * h * moment(x[1:n]) / EI

    # STEP 3  solve, then place the answers back into a full-length array whose
    # first and last entries stay zero - the boundary conditions.
    y = np.zeros(n + 1)
    y[1:n] = np.linalg.solve(A, rhs)     # in the assignment, use YOUR Lab 6 solver
    return x, y


# ==============================================================================
# PART 3  -  VERIFY BEFORE YOU TRUST
# ==============================================================================
# The exact midspan deflection for this case is  5 w L^4 / (384 E I).
# Any student who skips this check has no evidence their code is right, because
# the haunched beam they actually need has no closed-form answer to compare to.

exact = 5 * W * L ** 4 / (384 * EI)

print("PART 3  VERIFICATION AGAINST THE CLOSED-FORM ANSWER")
print(f"   exact y_max = 5 w L^4 / (384 E I) = {exact*1000:.6f} mm\n")
print(f"   {'n':>5}{'h (m)':>10}{'y_max (mm)':>15}{'error (mm)':>14}{'ratio':>8}")

previous_error = None
results = {}
for n in (4, 8, 16, 32, 64, 128):
    x, y = beam(n)
    y_max = float(np.max(np.abs(y)))
    results[n] = y_max
    error = abs(y_max - exact)
    ratio = f"{previous_error / error:.3f}" if previous_error else "-"
    print(f"   {n:>5}{L/n:>10.4f}{y_max*1000:>15.6f}{error*1000:>14.3e}{ratio:>8}")
    previous_error = error

print("\n   The ratio is 4.000 at every refinement. That is the signature of an")
print("   O(h^2) method, which is exactly what the centred second difference")
print("   should be. A ratio of 2.000 would mean the boundary treatment has")
print("   dropped the whole solution to first order - the classic capstone bug.\n")


# ==============================================================================
# PART 4  -  SOMETHING FOR NOTHING: RICHARDSON EXTRAPOLATION
# ==============================================================================
# If the error behaves as C h^2, then two solutions at h and h/2 contain enough
# information to eliminate the leading error term:
#
#       y_better = ( 4 y_fine - y_coarse ) / 3
#
# The 4 is 2^p with p = 2, the known order. No extra solve is required.

richardson = (4 * results[128] - results[64]) / 3

print("PART 4  RICHARDSON EXTRAPOLATION")
print(f"   from n = 64 and n = 128 : {richardson*1000:.6f} mm")
print(f"   exact                   : {exact*1000:.6f} mm")
print(f"   remaining error         : {abs(richardson - exact)*1000:.2e} mm")
print("   Six correct figures out of two coarse solutions, at no extra cost.\n")


# ==============================================================================
# PART 5  -  ROTATION, BY DIFFERENTIATING THE DEFLECTION
# ==============================================================================
# The slope dy/dx is the rotation. Support rotation governs bearing selection
# and the movement joint at the abutment, so it is a real design quantity and
# not an academic one.
#
# NOTE THE ACCURACY COST: this is a numerical derivative OF a numerical
# solution, so it is one order less accurate than the deflection itself. Always
# check it against theory where theory exists.

print("PART 5  SUPPORT ROTATION")

x, y = beam(64)
theta = np.gradient(y, x[1] - x[0])       # np.gradient: centred differences
theory = W * L ** 3 / (24 * EI)           # exact support rotation for this case

print(f"   computed |theta| at the support = {abs(theta[0]):.6f} rad")
print(f"   theory    w L^3 / (24 E I)      = {theory:.6f} rad")
print(f"   agreement to {abs(abs(theta[0]) - theory):.1e} rad\n")


# ==============================================================================
# PART 6  -  THE FIGURE
# ==============================================================================
# Two panels: the physical result on top, the evidence that it can be trusted
# underneath. A deflected shape without a convergence study is a picture; with
# one it is an engineering result.

print("PART 6  BUILDING THE FIGURE")

fig, axs = plt.subplots(2, 1, figsize=(5.6, 4.8))

# --- top panel: the deflected shape -----------------------------------------
# Plotted as -y so that downward deflection appears downward on the page, which
# is how a structural engineer expects to read it.
axs[0].plot(x, -y * 1000, color=BLUE, lw=1.8)
axs[0].set_xlabel("x (m)")
axs[0].set_ylabel("deflection (mm, down)")
axs[0].set_title("Lab 10 demo: deflected shape at n = 64")

# --- bottom panel: the convergence evidence ---------------------------------
ns = np.array([4, 8, 16, 32, 64, 128])
errors = np.array([abs(results[k] - exact) for k in ns])

axs[1].loglog(L / ns, errors * 1000, "o-", color=DARK, ms=4)

# Measure the slope from the data rather than asserting it.
slope = np.polyfit(np.log10(L / ns), np.log10(errors), 1)[0]
axs[1].set_xlabel("h (m)")
axs[1].set_ylabel("error (mm)")
axs[1].set_title(f"convergence: measured slope {slope:.2f}, theory 2")

fig.tight_layout()
out = f"{FIG}/demo_lab10.png"
fig.savefig(out)
plt.close(fig)
print(f"   figure written to {out}")
