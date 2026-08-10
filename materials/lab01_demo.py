"""
================================================================================
 LAB 01 DEMO  -  The derivative you can actually measure
 Numerical Methods Laboratory  |  Prepared by Engr. Escranda
================================================================================

WHAT THIS PROGRAM IS
    The worked example from Lab Lecture 1, written out in full. Read it from
    top to bottom: every block is numbered and explained before it runs.

HOW TO RUN IT
    python lab01_demo.py

    It prints a set of tables to the screen and writes one figure to the
    ./figures/ folder. Nothing else is required.

HOW THE PROGRAM IS ORGANISED
    SETUP    imports, output folder, plot settings
    PART 1   define derivative()  - the finite-difference engine
    PART 2   test it on sin(x), whose derivative we know exactly
    PART 3   halve the step size and confirm the error falls by four
    PART 4   add 0.1 % noise and watch the derivative fall apart
    PART 5   smooth the data, differentiate again, compare
    PART 6   build the figure and save it

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
# PART 1  -  THE DIFFERENTIATION ENGINE
# ==============================================================================

def derivative(x, y):
    """Estimate dy/dx at EVERY sample of an equally spaced record.

    THE MATHEMATICS
        Interior points use the centred difference

            f'(x_i) ~ ( y[i+1] - y[i-1] ) / (2h)          error = O(h^2)

        The first and last samples have no neighbour on one side, so they use
        the three-point one-sided formulas

            f'(x_0) ~ ( -3y[0] + 4y[1] - y[2] ) / (2h)    error = O(h^2)
            f'(x_n) ~ (  3y[n] - 4y[n-1] + y[n-2] ) / (2h)

    WHY NOT A SIMPLE TWO-POINT FORMULA AT THE ENDS?
        ( y[1] - y[0] ) / h is easier to write but only O(h). One bad endpoint
        drags the accuracy of the whole record down to first order, and the
        endpoints are usually the values an engineer cares about most.

    PARAMETERS
        x : 1-D array of sample positions, equally spaced
        y : 1-D array of measured values, same length as x

    RETURNS
        1-D array of derivatives, the SAME LENGTH as y
    """
    # Convert to float arrays. asarray does not copy if the input is already an
    # array, so this costs nothing when the caller passes NumPy arrays.
    x, y = np.asarray(x, float), np.asarray(y, float)

    # STEP 1  measure the spacing from the data rather than trusting the caller
    h = x[1] - x[0]

    # CHECK: every gap must equal the first one. np.diff(x) is the array of
    # differences; allclose compares with a tolerance, because floating-point
    # values that "should" be equal rarely are exactly equal.
    if not np.allclose(np.diff(x), h):
        raise ValueError("Samples are not equally spaced.")

    # STEP 2  make an output array of the right size, uninitialised for speed
    d = np.empty_like(y)

    # STEP 3  interior points, all at once.
    #   y[2:]   is y from index 2 to the end        (the "point ahead")
    #   y[:-2]  is y from the start to index n-2    (the "point behind")
    # Subtracting these two slices computes every interior centred difference
    # in one vectorised operation - no Python loop.
    d[1:-1] = (y[2:] - y[:-2]) / (2 * h)

    # STEP 4  the two endpoints, using the one-sided formulas
    d[0] = (-3 * y[0] + 4 * y[1] - y[2]) / (2 * h)
    d[-1] = (3 * y[-1] - 4 * y[-2] + y[-3]) / (2 * h)

    return d


def moving_average(y, w):
    """Smooth y with a centred moving average of odd width w.

    HOW IT WORKS
        np.convolve slides a kernel of w equal weights (each 1/w) along the
        data and sums the products - which is exactly an average of the w
        values under the kernel.

    THE EDGE PROBLEM
        At the first and last few samples the kernel hangs off the end of the
        data. np.pad with mode="edge" extends the record by repeating the first
        and last values, so the average is always taken over w real numbers and
        the output is the same length as the input.
    """
    pad = w // 2                       # how far the kernel reaches either side
    padded = np.pad(y, pad, mode="edge")
    kernel = np.ones(w) / w            # w weights, each 1/w, so they sum to 1
    return np.convolve(padded, kernel, mode="valid")


# ==============================================================================
# PART 2  -  TEST IT ON A FUNCTION WHOSE DERIVATIVE WE KNOW
# ==============================================================================
# WHY: never trust a differentiator you have not checked. sin(x) is ideal
# because its exact derivative, cos(x), is available for comparison.

print("PART 2  TEST ON A FUNCTION WHOSE DERIVATIVE WE KNOW")
x = np.linspace(0, 2 * np.pi, 50)      # 50 samples over one full period
y = np.sin(x)

d_numeric = derivative(x, y)           # what our routine produces
d_exact = np.cos(x)                    # what calculus says it should be
err = np.abs(d_numeric - d_exact)      # the error at every sample

print(f"   max error over the interior points : {err[1:-1].max():.3e}")
print(f"   error at the very first sample     : {err[0]:.3e}")
print("   The endpoint is worse. It uses a different formula and sits at the")
print("   edge of the data, where there is less information to work with.\n")


# ==============================================================================
# PART 3  -  CONFIRM THE ORDER OF ACCURACY
# ==============================================================================
# THE CLAIM: the centred difference is O(h^2). If that is true, HALVING h must
# divide the error by 2^2 = 4. This is the single most useful test in the whole
# course, because it needs no exact answer beyond one reference value.

print("PART 3  HALVE h AND WATCH THE ERROR FALL BY FOUR")
print(f"   {'n':>6}{'h':>12}{'max error':>14}{'ratio':>9}")

previous_error = None                  # holds the error from the run before
for n in (25, 50, 100, 200):           # each n roughly doubles the sample count
    xx = np.linspace(0, 2 * np.pi, n)
    e = np.abs(derivative(xx, np.sin(xx)) - np.cos(xx))[1:-1].max()

    # On the first pass there is nothing to compare with, hence the blank.
    ratio = f"{previous_error / e:.2f}" if previous_error else "-"
    print(f"   {n:>6}{xx[1]-xx[0]:>12.5f}{e:>14.3e}{ratio:>9}")
    previous_error = e

print("   The ratio settles on 4.00, which is the experimental proof that the")
print("   method really is second order. A ratio of 2 would mean a bug.\n")


# ==============================================================================
# PART 4  -  WHAT NOISE DOES TO A DERIVATIVE
# ==============================================================================
# A real sensor is never exact. Here we add noise of one part in a thousand -
# far too small to see on a plot of the data itself - and differentiate again.

print("PART 4  NOISE: 0.1 % ON THE DATA, RUIN ON THE DERIVATIVE")

# default_rng(0) seeds the random generator so this program prints the same
# numbers every time it runs. Reproducibility is a requirement, not a nicety.
rng = np.random.default_rng(0)

xn = np.linspace(0, 2 * np.pi, 200)
clean = np.sin(xn)
noise = rng.normal(0, 1e-3, xn.size)   # mean 0, standard deviation 0.001
noisy = clean + noise

e_clean = np.abs(derivative(xn, clean) - np.cos(xn)).max()
e_noisy = np.abs(derivative(xn, noisy) - np.cos(xn)).max()

print(f"   clean data : max derivative error {e_clean:.3e}")
print(f"   noisy data : max derivative error {e_noisy:.3e}"
      f"   ({e_noisy / e_clean:.0f} times worse)")
print("   WHY: the centred difference divides a difference of two noisy values")
print("   by 2h. With h small, that division multiplies the noise up.\n")


# ==============================================================================
# PART 5  -  SMOOTH FIRST, THEN DIFFERENTIATE
# ==============================================================================
print("PART 5  SMOOTH, THEN DIFFERENTIATE")

smoothed = moving_average(noisy, 9)         # 9-sample window
d_smoothed = derivative(xn, smoothed)

# Trim 10 samples from each end before measuring the error: the padding used by
# the moving average makes the extreme edges unrepresentative.
e_smoothed = np.abs(d_smoothed - np.cos(xn))[10:-10].max()

print(f"   after a 9-point moving average     : {e_smoothed:.3e}")
print(f"   improvement over the raw derivative: {e_noisy / e_smoothed:.0f} times")
print("   The window length is an engineering judgement: too short leaves noise,")
print("   too long flattens the real peaks. Whatever you choose, say so.\n")


# ==============================================================================
# PART 6  -  THE FIGURE
# ==============================================================================
# The figure has two stacked panels sharing one x-axis: the data on top, the
# derivatives underneath. That layout is deliberate - it lets the reader see
# that data which looks clean produces a derivative that is not.

print("PART 6  BUILDING THE FIGURE")

# plt.subplots(rows, cols) returns the figure object and an array of axes.
# figsize is in inches; sharex ties the two x-axes together so they zoom as one.
fig, axs = plt.subplots(2, 1, figsize=(5.8, 4.6), sharex=True)

# --- top panel: the measured data -------------------------------------------
axs[0].plot(xn, noisy, ".", color=BLUE, ms=2)     # "." = dots, ms = marker size
axs[0].set_ylabel("y")
axs[0].set_title("Lab 1 demo: 0.1 % noise is invisible here")

# --- bottom panel: three curves for comparison ------------------------------
axs[1].plot(xn, derivative(xn, noisy), color="#9bb8d3", lw=.8,
            label="raw derivative")
axs[1].plot(xn, d_smoothed, color=DARK, lw=1.5, label="after smoothing")
axs[1].plot(xn, np.cos(xn), color=ORANGE, lw=1, ls="--", label="true")
axs[1].set_xlabel("x")                            # units belong on every axis
axs[1].set_ylabel("dy/dx")
axs[1].set_title("but it is not invisible here")
axs[1].legend(fontsize=7)                         # the legend names the curves

# tight_layout resizes the panels so nothing overlaps the labels.
fig.tight_layout()

# savefig writes the PNG. plt.close releases the memory - important when a
# program produces many figures in a loop.
out = f"{FIG}/demo_lab01.png"
fig.savefig(out)
plt.close(fig)

print(f"   figure written to {out}")
