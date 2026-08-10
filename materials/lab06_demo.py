"""
================================================================================
 LAB 06 DEMO  -  The matrix as a machine: Gauss elimination
 Numerical Methods Laboratory  |  Prepared by Engr. Escranda
================================================================================

WHAT THIS PROGRAM IS
    The worked example from Lab Lecture 6, written out in full. Read it from
    top to bottom: every block is numbered and explained before it runs.

HOW TO RUN IT
    python lab06_demo.py

    It prints a set of tables to the screen and writes one figure to the
    ./figures/ folder. Nothing else is required.

HOW THE PROGRAM IS ORGANISED
    SETUP    imports, output folder, plot settings
    PART 1   define gauss_pivot() - elimination with partial pivoting
    PART 2   solve the three-bar joint from the lecture, and check the residual
    PART 3   show what a small pivot does to the arithmetic
    PART 4   show what a zero pivot does to a routine without pivoting
    PART 5   plot multiplier size against pivot size

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
# PART 1  -  THE SOLVER
# ==============================================================================

def gauss_pivot(A, b, tol=1e-12):
    """Solve the linear system A x = b by Gauss elimination with partial pivoting.

    THE METHOD, IN TWO PHASES
        1. FORWARD ELIMINATION. Use equation k to remove unknown k from every
           equation below it, until the matrix is upper triangular.
        2. BACK SUBSTITUTION. The last equation now has one unknown. Solve it,
           substitute upwards, and work back to the first.

    WHAT PARTIAL PIVOTING ADDS
        Before eliminating in column k, find the row at or below k with the
        LARGEST absolute value in that column and swap it into the pivot
        position. Every elimination multiplier is then at most 1 in magnitude,
        so no existing round-off is amplified. Without it, a small pivot
        produces a huge multiplier that magnifies error, and a zero pivot
        divides by zero. Pivoting costs a search and a swap - a few per cent of
        the runtime - and there is no situation in which you should omit it.

    THE COST
        About n^3/3 multiplications. Doubling the size of the structure
        multiplies the work by eight.

    RETURNS
        x, the solution vector.
    """
    # WHY np.array and not np.asarray: we want a genuine COPY. This routine
    # destroys what it works on, and it must not destroy the caller's data.
    A = np.array(A, float)
    b = np.array(b, float)
    n = len(b)

    # ---------------------------------------------------------------- phase 1
    for k in range(n - 1):                 # k is the column being cleared

        # STEP 1  find the best pivot available in this column.
        # np.argmax returns the index of the largest value WITHIN THE SLICE
        # A[k:, k], so k is added back to convert it to a row number.
        p = k + int(np.argmax(np.abs(A[k:, k])))

        # CHECK: if even the best pivot is essentially zero, the matrix is
        # singular - a mechanism rather than a structure. Fail loudly.
        if abs(A[p, k]) < tol:
            raise ValueError(f"Matrix is singular at column {k}.")

        # STEP 2  swap that row into the pivot position.
        # Fancy indexing with a list swaps both rows in one statement.
        if p != k:
            A[[k, p]] = A[[p, k]]
            b[[k, p]] = b[[p, k]]

        # STEP 3  eliminate unknown k from every row below.
        for i in range(k + 1, n):
            factor = A[i, k] / A[k, k]     # after pivoting, |factor| <= 1
            # The slice A[k, k:] skips the columns already cleared - they are
            # zero, so subtracting a multiple of zero would be wasted work.
            A[i, k:] -= factor * A[k, k:]
            b[i] -= factor * b[k]

    # ---------------------------------------------------------------- phase 2
    x = np.zeros(n)
    for i in range(n - 1, -1, -1):         # count DOWN from the last equation
        # A[i, i+1:] @ x[i+1:] is the dot product of the already-known unknowns
        # with their coefficients - everything to the right of the diagonal.
        x[i] = (b[i] - A[i, i + 1:] @ x[i + 1:]) / A[i, i]

    return x


# ==============================================================================
# PART 2  -  THE THREE-BAR JOINT
# ==============================================================================
# A pin carries a 10 kN vertical load. Three members meet there. Writing
# equilibrium at the joint (sum Fx = 0, sum Fy = 0) plus one support condition
# gives three equations in the three member forces.
#
# Row 1 : horizontal equilibrium      Row 2 : vertical equilibrium
# Row 3 : the support condition
# The coefficients are the direction cosines of the members.
# SIGN CONVENTION: tension positive. State it in the report; it is part of the
# answer, not a formality.

print("PART 2  THE THREE-BAR JOINT FROM THE LECTURE")

A = np.array([[0.8660, 0.0, -0.7071],       # F1 at 30 deg, F3 at 135 deg
              [0.5000, 1.0,  0.7071],       # F2 vertical
              [0.0000, 1.0,  0.0000]])
b = np.array([0.0, -10.0, -4.0])            # kN

x = gauss_pivot(A, b)

for name, value in zip(("F1 (30 deg)", "F2 (vertical)", "F3 (135 deg)"), x):
    sense = "tension" if value > 0 else "compression"
    print(f"   {name:>14} = {value:8.4f} kN   {sense}")

# CHECK: the residual r = b - A x measures whether the solution actually
# satisfies the equations. It should sit at round-off level, about 1e-16 for
# numbers of order 1. A large residual means the solve failed.
residual = np.max(np.abs(b - A @ x))
print(f"   max |residual| = {residual:.2e} kN   (round-off level: good)\n")


# ==============================================================================
# PART 3  -  WHAT A SMALL PIVOT DOES
# ==============================================================================
# The classic example. Both equations are perfectly ordinary; the only problem
# is that the first coefficient is small.
#
#       0.0003 x1 + 3 x2 = 2.0001
#            1 x1 + 1 x2 = 1
#
# Eliminating with the first row as pivot needs the multiplier 1/0.0003 = 3333.
# That multiplier magnifies whatever round-off is already present in row 1 by a
# factor of three thousand before subtracting it from row 2.

print("PART 3  WHY PIVOTING IS NOT OPTIONAL")

Ae = np.array([[3e-4, 3.0],
               [1.0, 1.0]])

# Build b from the KNOWN answer (1/3, 2/3) so the exact solution is certain.
x_true = np.array([1 / 3, 2 / 3])
be = Ae @ x_true

print(f"   without pivoting the multiplier would be 1/0.0003 = {1/3e-4:.1f}")
print(f"   with pivoting the multiplier is at most 1")
x_pivoted = gauss_pivot(Ae, be)
print(f"   pivoted solution : ({x_pivoted[0]:.10f}, {x_pivoted[1]:.10f})")
print(f"   exact solution   : ({x_true[0]:.10f}, {x_true[1]:.10f})\n")


# ==============================================================================
# PART 4  -  A ZERO PIVOT IS ROUTINE, NOT EXOTIC
# ==============================================================================
# Nothing is wrong with this system: it has a unique solution. But the very
# first pivot is zero, so a routine without pivoting divides by zero on its
# first step and returns nan. In a truss this happens whenever the first joint
# has no member acting along the first coordinate direction - that is, often.

print("PART 4  A ZERO PIVOT")

Az = np.array([[0.0, 2.0, 1.0],
               [1.0, 3.0, 2.0],
               [2.0, 1.0, 4.0]])
bz = np.array([7.0, 13.0, 15.0])

xz = gauss_pivot(Az, bz)
print(f"   with pivoting : ({xz[0]:.4f}, {xz[1]:.4f}, {xz[2]:.4f})")
print(f"   CHECK by substitution: A x = {np.round(Az @ xz, 6)} against b = {bz}")
print("   Without pivoting this system produces nan on the first elimination.\n")


# ==============================================================================
# PART 5  -  THE FIGURE
# ==============================================================================
# The multiplier used in elimination is 1/pivot. On log-log axes that is a
# straight line of slope -1: shrink the pivot by a thousand and the multiplier,
# and with it the error amplification, grows by a thousand.

print("PART 5  BUILDING THE FIGURE")

pivots = np.array([3e-4, 3e-6, 3e-9, 3e-12])
multipliers = 1 / pivots

fig, ax = plt.subplots(figsize=(5.0, 3.2))
ax.loglog(pivots, multipliers, "o-", color=BLUE, ms=5)

# Annotate one point so the reader sees the physical meaning immediately.
ax.annotate("pivot 3e-12 needs a\nmultiplier of 3e+11",
            xy=(pivots[-1], multipliers[-1]), xytext=(1e-9, 1e10),
            fontsize=7, color=DARK,
            arrowprops=dict(arrowstyle="->", color=DARK, lw=.8))

ax.set_xlabel("pivot magnitude")
ax.set_ylabel("elimination multiplier  1 / pivot")
ax.set_title("Lab 6 demo: a small pivot means a huge multiplier")

fig.tight_layout()
out = f"{FIG}/demo_lab06.png"
fig.savefig(out)
plt.close(fig)
print(f"   figure written to {out}")
