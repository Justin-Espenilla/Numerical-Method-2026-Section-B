"""
================================================================================
 LAB 03 DEMO  -  Gradient descent: following the derivative downhill
 Numerical Methods Laboratory  |  Prepared by Engr. Escranda
================================================================================

WHAT THIS PROGRAM IS
    The worked example from Lab Lecture 3, written out in full. Read it from
    top to bottom: every block is numbered and explained before it runs.

HOW TO RUN IT
    python lab03_demo.py

    It prints a set of tables to the screen and writes one figure to the
    ./figures/ folder. Nothing else is required.

HOW THE PROGRAM IS ORGANISED
    SETUP    imports, output folder, plot settings
    PART 1   define gradient()        - the vector of partial derivatives
    PART 2   define descent()         - the iteration itself
    PART 3   minimise a bowl and find the step size at which it diverges
    PART 4   minimise a narrow valley and watch the zigzag
    PART 5   plot the path over a contour map

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
# PART 1  -  THE GRADIENT
# ==============================================================================

def gradient(func, x, rel_h=1e-6):
    """The vector of partial derivatives of func at the point x.

    THE MATHEMATICS
        grad f = [ df/dx1, df/dx2, ..., df/dxn ]

        Each component is a centred difference in ONE coordinate while the
        others are frozen - exactly the partial derivative of Lab 2, applied
        one axis at a time.

    TWO FACTS THAT MAKE THE METHOD WORK
        1. grad f points in the direction of steepest INCREASE, so -grad f is
           the steepest way down.
        2. At a minimum the ground is flat, so grad f = 0. That is both the
           target and the stopping test.

    THE COST
        2n function evaluations per gradient: n coordinates, two evaluations
        each. For five design variables that is ten evaluations per step, and
        a thousand steps is ten thousand evaluations. Remember this number.
    """
    x = np.asarray(x, float)
    g = np.zeros_like(x)                    # one slot per coordinate

    for j in range(x.size):                 # loop over the coordinates
        h = max(abs(x[j]), 1.0) * rel_h     # scaled step, as in Lab 2

        # .copy() is essential: without it, up and down would be two names for
        # the SAME array and the two evaluations would be identical.
        up, down = x.copy(), x.copy()
        up[j] += h
        down[j] -= h

        g[j] = (func(up) - func(down)) / (2 * h)

    return g


# ==============================================================================
# PART 2  -  THE ITERATION
# ==============================================================================

def descent(func, x0, alpha=0.1, tol=1e-6, max_iter=20000):
    """Minimise func by fixed-step gradient descent.

    THE UPDATE RULE
        x_{k+1} = x_k - alpha * grad f(x_k)

        alpha is the step size (the "learning rate"). Too small and the run
        takes forever; too large and the iterates overshoot and fly apart.

    THE STOPPING TEST
        We stop when |grad f| < tol - "the ground is flat". Two alternatives
        are tempting and worse:
          * stopping when x stops moving: a tiny alpha also stops the motion,
            so you would declare victory half way up the slope;
          * stopping when f stops improving: on a long flat valley floor that
            triggers far too early.

    RETURNS
        (x, iterations, path)  where path is the list of every iterate, kept
        so that PART 5 can draw the route taken.
    """
    x = np.asarray(x0, float).copy()
    path = [x.copy()]

    for k in range(max_iter):
        g = gradient(func, x)

        # np.linalg.norm(g) is the length of the gradient vector, sqrt(sum g^2)
        if np.linalg.norm(g) < tol:
            return x, k, path

        x = x - alpha * g                   # THE STEP: downhill by alpha
        path.append(x.copy())

        # CHECK: detect divergence before it produces inf and nan. A run that
        # has left the region of interest will never come back.
        if not np.all(np.isfinite(x)) or np.linalg.norm(x) > 1e12:
            raise RuntimeError(f"diverged at iteration {k}")

    return x, max_iter, path


# ==============================================================================
# PART 3  -  A BOWL, AND THE STEP SIZE THAT BREAKS IT
# ==============================================================================

def bowl(x):
    """f = (x1 - 3)^2 + 2 (x2 + 1)^2.  Minimum at (3, -1), where f = 0.

    Its Hessian (the matrix of second derivatives) is the constant diag(2, 4),
    so the largest eigenvalue is 4. For a quadratic, gradient descent converges
    only when alpha < 2 / lambda_max = 2/4 = 0.5. That prediction is tested
    below.
    """
    return (x[0] - 3) ** 2 + 2 * (x[1] + 1) ** 2


print("PART 3  THE BOWL. THEORY SAYS IT DIVERGES ABOVE alpha = 2/4 = 0.5")
print(f"   {'alpha':>7}{'result':>32}{'iterations':>12}")

for a in (0.01, 0.1, 0.4, 0.6):
    try:
        x, k, _ = descent(bowl, [0.0, 0.0], alpha=a)
        print(f"   {a:>7.2f}{f'converged to ({x[0]:.5f}, {x[1]:.5f})':>32}{k:>12}")
    except RuntimeError as e:
        print(f"   {a:>7.2f}{'DIVERGED':>32}{str(e).split()[-1]:>12}")

print("   The break is exactly where the eigenvalue predicts. Step size is not")
print("   a matter of taste; it is set by the curvature of the function.\n")


# ==============================================================================
# PART 4  -  A NARROW VALLEY
# ==============================================================================

def rosenbrock(x):
    """The banana function. Minimum at (1, 1), where f = 0.

    Its valley is long, curved and extremely narrow. The gradient points almost
    ACROSS the valley rather than along it, so the iterates zigzag from wall to
    wall while creeping forward. Almost all the effort goes sideways.
    """
    return (1 - x[0]) ** 2 + 100 * (x[1] - x[0] ** 2) ** 2


print("PART 4  THE NARROW VALLEY")
x, k, path = descent(rosenbrock, [-1.2, 1.0], alpha=1e-3, tol=1e-5, max_iter=30000)
print(f"   start (-1.2, 1.0), alpha = 1e-3")
print(f"   reached ({x[0]:.6f}, {x[1]:.6f}) after {k} iterations")
print("   The minimum is at (1, 1). Look at the figure to see where those")
print("   iterations actually went.\n")


# ==============================================================================
# PART 5  -  THE CONTOUR PLOT WITH THE PATH DRAWN ON IT
# ==============================================================================
print("PART 5  BUILDING THE FIGURE")

# STEP 1  build a grid of points covering the region of interest.
# np.meshgrid turns two 1-D axes into two 2-D coordinate arrays, so that Z can
# be evaluated at every combination in one vectorised expression.
X, Y = np.meshgrid(np.linspace(-2, 2, 400), np.linspace(-1, 3, 400))
Z = (1 - X) ** 2 + 100 * (Y - X ** 2) ** 2

fig, ax = plt.subplots(figsize=(5.4, 3.8))

# STEP 2  draw the contours.
# The function spans several orders of magnitude, so evenly spaced levels would
# bunch up near the minimum. np.logspace gives levels spaced logarithmically.
ax.contour(X, Y, Z, levels=np.logspace(-1, 3.5, 20),
           linewidths=.5, colors="#b8c9da")

# STEP 3  overlay the path. np.array turns the list of iterates into an array
# so that P[:, 0] is all the x1 values and P[:, 1] all the x2 values.
# The [::50] slice plots every 50th point - drawing all 30,000 would be a
# solid smear rather than a visible track.
P = np.array(path)
ax.plot(P[::50, 0], P[::50, 1], ".-", color=BLUE, lw=.8, ms=2,
        label="descent path")

# STEP 4  mark the true minimum
ax.plot(1, 1, "*", color=ORANGE, ms=12, label="minimum (1, 1)")

ax.set_xlabel("x1")
ax.set_ylabel("x2")
ax.set_title("Lab 3 demo: the zigzag down a narrow valley")
ax.legend(fontsize=7)
ax.grid(False)              # WHY: a grid competes with the contour lines

fig.tight_layout()
out = f"{FIG}/demo_lab03.png"
fig.savefig(out)
plt.close(fig)
print(f"   figure written to {out}")
