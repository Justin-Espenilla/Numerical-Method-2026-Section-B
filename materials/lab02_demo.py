"""
================================================================================
 LAB 02 DEMO  -  Sensitivity analysis: which number should you worry about?
 Numerical Methods Laboratory  |  Prepared by Engr. Escranda
================================================================================

WHAT THIS PROGRAM IS
    The worked example from Lab Lecture 2, written out in full. Read it from
    top to bottom: every block is numbered and explained before it runs.

HOW TO RUN IT
    python lab02_demo.py

    It prints a set of tables to the screen and writes one figure to the
    ./figures/ folder. Nothing else is required.

HOW THE PROGRAM IS ORGANISED
    SETUP    imports, output folder, plot settings
    PART 1   define head_loss()  - the engineering model
    PART 2   define partial()    - one numerical partial derivative
    PART 3   evaluate the model at the operating point
    PART 4   build the sensitivity table and check it against the physics
    PART 5   propagate the input uncertainties into the answer
    PART 6   draw the tornado chart

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
# PART 1  -  THE ENGINEERING MODEL
# ==============================================================================

def head_loss(p):
    """Darcy-Weisbach head loss in a circular pipe, in metres.

    THE PHYSICS
        h_L = f * (L/D) * V^2 / (2g)        with     V = 4Q / (pi D^2)

        f  friction factor (dimensionless)
        L  pipe length (m)
        D  internal diameter (m)
        Q  volumetric flow (m^3/s)
        g  gravitational acceleration (m/s^2)

    WHY A DICTIONARY INSTEAD OF POSITIONAL ARGUMENTS?
        Because the name stays attached to the number. In a report,
        "d(h_L)/d(D)" is meaningful; "the third sensitivity" is not. It also
        means partial() below can perturb a parameter BY NAME.
    """
    V = 4 * p["Q"] / (np.pi * p["D"] ** 2)          # continuity: V = Q / area
    return p["f"] * p["L"] / p["D"] * V ** 2 / (2 * p["g"])


# ==============================================================================
# PART 2  -  ONE NUMERICAL PARTIAL DERIVATIVE
# ==============================================================================

def partial(func, params, key, rel_h=1e-6):
    """d(func)/d(params[key]) by a centred difference.

    THE MATHEMATICS
        df/dx ~ ( f(x+h) - f(x-h) ) / (2h)          error = O(h^2)

        Every other parameter is held fixed, which is what makes this a PARTIAL
        derivative rather than a total one.

    THE CRITICAL DETAIL - SCALING THE PERTURBATION
        A fixed h = 0.001 is meaningless when one input is a diameter of 0.3 m
        and another is a modulus of 2e11 Pa. On the modulus it is an
        insultingly small nudge lost to round-off; on a Poisson ratio it is a
        third of a percent. So h is taken as a FRACTION of the variable's own
        magnitude.

        max(abs(x), 1.0) guards the case x = 0, where a relative step would be
        zero and the derivative would come out as 0/0.
    """
    x = params[key]
    h = max(abs(x), 1.0) * rel_h

    # dict(params) makes a shallow COPY. Without it we would permanently
    # damage the caller's parameter set - a classic and hard-to-find bug.
    up, down = dict(params), dict(params)
    up[key] = x + h
    down[key] = x - h

    return (func(up) - func(down)) / (2 * h)


# ==============================================================================
# PART 3  -  THE OPERATING POINT
# ==============================================================================
params = {"f": 0.022, "L": 450.0, "D": 0.30, "Q": 0.085, "g": 9.81}
h0 = head_loss(params)

print("PART 3  THE OPERATING POINT")
print(f"   pipe: L = {params['L']} m, D = {params['D']} m, "
      f"Q = {params['Q']} m3/s, f = {params['f']}")
print(f"   head loss h_L = {h0:.4f} m\n")


# ==============================================================================
# PART 4  -  THE SENSITIVITY TABLE
# ==============================================================================
# A raw partial derivative cannot be compared across parameters: d(h)/d(D) is
# in m per m, d(h)/d(Q) is in m per m^3/s. Comparing them is comparing metres
# with cubic metres per second. The fix is to make the sensitivity
# DIMENSIONLESS:
#
#       S = (df/dx) * (x / f)
#
# Read aloud: "a one percent change in x produces an S percent change in f".

print("PART 4  SENSITIVITY TABLE")
print(f"   {'param':>6}{'value':>12}{'d(h_L)/dx':>16}{'S':>10}{'exponent':>10}")

# h_L is proportional to f * L * Q^2 * D^-5, so for this pure power law the
# dimensionless sensitivity must equal the exponent exactly. That is our CHECK.
expected_exponent = {"f": 1, "L": 1, "D": -5, "Q": 2, "g": -1}
S = {}

for k in params:
    dfdx = partial(head_loss, params, k)
    S[k] = dfdx * params[k] / h0                    # the dimensionless form
    print(f"   {k:>6}{params[k]:>12.5g}{dfdx:>16.5g}"
          f"{S[k]:>10.4f}{expected_exponent[k]:>10d}")

print("\n   CHECK: every S reproduces the exponent of that variable in")
print("   h_L = f L Q^2 D^-5. If yours do not, the perturbation size is wrong")
print("   or the model has a bug. This check catches most Lab 2 errors.")
print("   ENGINEERING READING: diameter is five times more damaging per percent")
print("   than length, so the calipers are worth more than the tape.\n")


# ==============================================================================
# PART 5  -  PROPAGATING THE UNCERTAINTIES
# ==============================================================================
# Knowing which input matters is step one. The client wants a tolerance on the
# answer. Two formulas, answering two different questions:
#
#   worst case  dF = SUM |df/dx_j| * dx_j        every error conspires at once
#   RSS         sF = sqrt( SUM (df/dx_j * s_j)^2 )   errors independent, some cancel

print("PART 5  PROPAGATING THE INPUT UNCERTAINTIES")
u = {"f": 0.004, "L": 5.0, "D": 0.005, "Q": 0.003}   # +/- 1 sigma on each

worst = 0.0
sum_of_squares = 0.0
for k, uk in u.items():
    contribution = partial(head_loss, params, k) * uk   # metres of head loss
    worst += abs(contribution)
    sum_of_squares += contribution ** 2
rss = np.sqrt(sum_of_squares)

print(f"   h_L = {h0:.3f} +/- {rss:.3f} m   (root-sum-square)")
print(f"   h_L = {h0:.3f} +/- {worst:.3f} m   (worst case)")
print("   Worst case belongs in a code check; RSS in a performance estimate.")
print("   Reporting one without saying which is a quiet way to mislead.\n")


# ==============================================================================
# PART 6  -  THE TORNADO CHART
# ==============================================================================
# A horizontal bar chart of |S|, longest at the top. This is the figure that
# ends arguments in a design review.

print("PART 6  BUILDING THE TORNADO CHART")

fig, ax = plt.subplots(figsize=(5.2, 3.0))

# Sort the parameter names by descending |S|. The lambda is the sort key;
# the minus sign turns an ascending sort into a descending one.
order = sorted(S, key=lambda k: -abs(S[k]))

# barh draws horizontal bars. Matplotlib places the first item at the BOTTOM,
# so both lists are reversed to put the largest bar at the top.
ax.barh(order[::-1], [abs(S[k]) for k in order][::-1], color=BLUE)

ax.set_xlabel("|S|  (percent change in h_L per percent change in the input)")
ax.set_title("Lab 2 demo: tornado chart for head loss")

fig.tight_layout()
out = f"{FIG}/demo_lab02.png"
fig.savefig(out)
plt.close(fig)
print(f"   figure written to {out}")
