"""
================================================================================
 LAB 07 DEMO  -  Iterative solution and conditioning
 Numerical Methods Laboratory  |  Prepared by Engr. Escranda
================================================================================

WHAT THIS PROGRAM IS
    The worked example from Lab Lecture 7, written out in full. Read it from
    top to bottom: every block is numbered and explained before it runs.

HOW TO RUN IT
    python lab07_demo.py

    It prints a set of tables to the screen and writes one figure to the
    ./figures/ folder. Nothing else is required.

HOW THE PROGRAM IS ORGANISED
    SETUP    imports, output folder, plot settings
    PART 1   define gauss_seidel() - the iterative solver
    PART 2   check diagonal dominance BEFORE iterating
    PART 3   run six sweeps by hand and watch the values settle
    PART 4   accelerate the same system with over-relaxation
    PART 5   the Hilbert matrix: a small residual with a worthless answer
    PART 6   plot sweeps against the relaxation factor

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
# PART 1  -  THE ITERATIVE SOLVER
# ==============================================================================

def gauss_seidel(A, b, tol=1e-8, max_iter=20000, lam=1.0):
    """Solve A x = b by repeated sweeps instead of elimination.

    THE IDEA
        Rearrange equation i to make x_i its subject:

            x_i = ( b_i - SUM_{j != i} a_ij x_j ) / a_ii

        Guess all the unknowns, apply that formula to each in turn, and repeat
        until the values stop changing.

    WHY BOTHER, WHEN ELIMINATION IS EXACT?
        A 200 x 100 seepage grid has 20,000 unknowns. Its matrix has 400
        million entries, of which fewer than 100,000 are non-zero, because each
        node touches only its four neighbours. Storing it densely needs 3.2 GB
        and factoring it needs 2.7e12 operations. An iterative sweep never
        forms the matrix at all.

    GAUSS-SEIDEL versus JACOBI
        Jacobi computes a whole new vector from the old one. Gauss-Seidel uses
        each updated value IMMEDIATELY, within the same sweep - the x[:i] slice
        below already holds new values while x[i+1:] still holds old ones. One
        line of difference, typically half the iterations.

    RELAXATION (lam)
        lam = 1     plain Gauss-Seidel
        1 < lam < 2 over-relaxation: deliberately overshoot each correction,
                    which on a large grid can cut the sweep count by an order
                    of magnitude
        lam < 1     under-relaxation: stabilises a system that would oscillate
    """
    A = np.asarray(A, float)
    b = np.asarray(b, float)
    n = len(b)
    x = np.zeros(n)                       # the initial guess: all zeros
    history = []

    for sweep in range(1, max_iter + 1):
        x_old = x.copy()                  # needed to measure the change

        for i in range(n):
            # The sum of every off-diagonal term. Splitting it into two slices
            # avoids having to skip index i inside a loop.
            s = A[i, :i] @ x[:i] + A[i, i + 1:] @ x[i + 1:]
            x_new = (b[i] - s) / A[i, i]
            x[i] = lam * x_new + (1 - lam) * x[i]      # relaxation blend

        # The stopping test: the largest RELATIVE change over one sweep.
        # np.maximum guards against dividing by a value that is still zero.
        ea = np.max(np.abs(x - x_old) / np.maximum(np.abs(x), 1e-30))
        history.append(ea)
        if ea < tol:
            return x, sweep, history

    return x, max_iter, history


# ==============================================================================
# PART 2  -  THE SYSTEM, AND THE CHECK THAT COMES FIRST
# ==============================================================================
# Four interior nodes of a seepage grid. Each node is connected to its two
# interior neighbours and to boundary nodes held at fixed head. The five-point
# stencil gives  4 h_i - (sum of neighbours) = (sum of known boundary heads).

A = np.array([[4., -1., -1., 0.],
              [-1., 4., 0., -1.],
              [-1., 0., 4., -1.],
              [0., -1., -1., 4.]])
b = np.array([6., 6., 1.5, 1.5])

print("PART 2  CHECK DIAGONAL DOMINANCE BEFORE ITERATING")

# THE CONDITION: |a_ii| >= sum of |a_ij| for j != i, in every row, with strict
# inequality in at least one. It says each unknown is influenced most strongly
# by its own equation - which is exactly what physical systems dominated by
# local effects (seepage, conduction, pipe networks) produce naturally.
diagonal = np.abs(np.diag(A))
off_diagonal = np.abs(A).sum(axis=1) - diagonal     # row sum minus the diagonal

print(f"   diagonal terms       {diagonal}")
print(f"   off-diagonal sums    {off_diagonal}")
dominant = bool(np.all(diagonal >= off_diagonal) and np.any(diagonal > off_diagonal))
print(f"   diagonally dominant  {dominant}  ->  convergence is guaranteed")
print("   If this check fails, reorder the equations. If reordering cannot fix")
print("   it, use elimination instead - the iteration will simply diverge.\n")


# ==============================================================================
# PART 3  -  SIX SWEEPS, WRITTEN OUT
# ==============================================================================
# This block deliberately does NOT call the function above. It performs the
# sweeps in the open so that every number can be followed by hand.

print("PART 3  SIX SWEEPS FROM AN INITIAL GUESS OF ZERO")
print(f"   {'sweep':>6}{'h1':>11}{'h2':>11}{'h3':>11}{'h4':>11}{'max change %':>14}")

x = np.zeros(4)
for sweep in range(1, 7):
    x_old = x.copy()
    for i in range(4):
        s = A[i, :i] @ x[:i] + A[i, i + 1:] @ x[i + 1:]
        x[i] = (b[i] - s) / A[i, i]
    ea = np.max(np.abs(x - x_old) / np.maximum(np.abs(x), 1e-30)) * 100
    print(f"   {sweep:>6}{x[0]:>11.6f}{x[1]:>11.6f}{x[2]:>11.6f}{x[3]:>11.6f}{ea:>14.4f}")

print(f"   {'exact':>6}{2.4375:>11.6f}{2.4375:>11.6f}{1.3125:>11.6f}{1.3125:>11.6f}")
print("   The error falls by roughly a factor of four per sweep. That is LINEAR")
print("   convergence with a fixed ratio, which is what iteration delivers.\n")


# ==============================================================================
# PART 4  -  ACCELERATION BY OVER-RELAXATION
# ==============================================================================
print("PART 4  THE SAME SYSTEM, DIFFERENT RELAXATION FACTORS")
print(f"   {'lambda':>8}{'sweeps to 1e-10':>18}")

for lam in (1.0, 1.2, 1.4, 1.6, 1.8):
    _, sweeps, _ = gauss_seidel(A, b, tol=1e-10, lam=lam)
    print(f"   {lam:>8.1f}{sweeps:>18}")

print("   There is an optimum. It depends on the matrix and is normally found")
print("   by experiment, which is exactly what the sweep above is.\n")


# ==============================================================================
# PART 5  -  A SMALL RESIDUAL IS NOT ACCURACY
# ==============================================================================
# The Hilbert matrix, a_ij = 1/(i+j-1), is what the normal equations produce
# when a high-order polynomial is fitted to data. It is the standard example of
# an ill-conditioned system, and it is not artificial.
#
# THE EXPERIMENT: choose the answer first - all ones - compute b = A x, then
# solve for x and see how much of the known answer comes back.

print("PART 5  CONDITIONING: THE HILBERT MATRIX")
print(f"   {'n':>4}{'cond(A)':>13}{'max error':>13}{'max residual':>15}"
      f"{'figures lost':>14}")

for n in (4, 8, 12):
    H = np.array([[1.0 / (i + j + 1) for j in range(n)] for i in range(n)])
    x_true = np.ones(n)
    bb = H @ x_true

    xs = np.linalg.solve(H, bb)              # a library solve, deliberately
    cond = np.linalg.cond(H)
    error = np.max(np.abs(xs - x_true))      # how wrong the ANSWER is
    resid = np.max(np.abs(H @ xs - bb))      # how well it fits the EQUATIONS

    print(f"   {n:>4}{cond:>13.2e}{error:>13.2e}{resid:>15.2e}"
          f"{np.log10(cond):>14.1f}")

print("   Read the last three columns together. The residual stays at round-off")
print("   while the error grows to order 1. Both are true at once because the")
print("   rows are nearly dependent: a vector far from the true answer still")
print("   satisfies the equations. RESIDUAL measures whether you solved the")
print("   system; the CONDITION NUMBER measures whether the system was worth")
print("   solving. Rule of thumb: figures lost is about log10(cond), out of the")
print("   16 that double precision provides.\n")


# ==============================================================================
# PART 6  -  THE FIGURE
# ==============================================================================
print("PART 6  BUILDING THE FIGURE")

lams = np.arange(1.0, 1.96, 0.05)
sweeps = [gauss_seidel(A, b, tol=1e-10, lam=l)[1] for l in lams]

fig, ax = plt.subplots(figsize=(5.0, 3.2))
ax.plot(lams, sweeps, "o-", color=BLUE, ms=4)

# Mark the best value found, read from the data rather than judged by eye.
best = int(np.argmin(sweeps))
ax.plot(lams[best], sweeps[best], "*", color=ORANGE, ms=14,
        label=f"optimum lambda = {lams[best]:.2f}")

ax.set_xlabel("relaxation factor lambda")
ax.set_ylabel("sweeps to reach 1e-10")
ax.set_title("Lab 7 demo: over-relaxation")
ax.legend(fontsize=7)

fig.tight_layout()
out = f"{FIG}/demo_lab07.png"
fig.savefig(out)
plt.close(fig)
print(f"   figure written to {out}")
