"""
================================================================================
 LAB 05 DEMO  -  Integrals that earn their keep: river discharge
 Numerical Methods Laboratory  |  Prepared by Engr. Escranda
================================================================================

WHAT THIS PROGRAM IS
    The worked example from Lab Lecture 5, written out in full. Read it from
    top to bottom: every block is numbered and explained before it runs.

HOW TO RUN IT
    python lab05_demo.py

    It prints a set of tables to the screen and writes one figure to the
    ./figures/ folder. Nothing else is required.

HOW THE PROGRAM IS ORGANISED
    SETUP    imports, output folder, plot settings
    PART 1   define trapz_data() - integration of MEASURED data
    PART 2   enter the gauging survey
    PART 3   compute area, discharge and the two rival mean velocities
    PART 4   locate the centroid of the section
    PART 5   attach an error bar by Richardson extrapolation
    PART 6   draw the cross-section with the velocity profile

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
# PART 1  -  INTEGRATING MEASURED DATA
# ==============================================================================

def trapz_data(x, y):
    """Trapezoidal rule for tabulated data, allowing UNEQUAL spacing.

    THE MATHEMATICS
        Each strip contributes  (x[i+1] - x[i]) * (y[i] + y[i+1]) / 2
        which is width times average height. Summing the strips gives the area.

    WHY THIS VERSION HAS NO h
        The classroom formula assumes a constant spacing h. Field data does
        not oblige: gauging stations are placed where the bank allows, and
        loggers drop samples. Here every strip carries its OWN width, taken
        from np.diff(x), so unequal spacing costs nothing and is handled
        correctly rather than silently ignored.
    """
    dx = np.diff(x)                       # the n widths between n+1 stations
    return float(np.sum(dx * (y[:-1] + y[1:]) / 2))


# ==============================================================================
# PART 2  -  THE SURVEY
# ==============================================================================
# A gauging team measures, at each station across the river: the distance from
# the bank, the depth, and the flow velocity. Three columns of numbers, no
# equation anywhere.

x = np.array([0, 1.2, 2.4, 3.6, 4.8, 6.0, 7.2, 8.4, 9.6, 10.8, 12.0])  # m
H = np.array([0, 0.4, 0.9, 1.5, 1.9, 2.1, 2.0, 1.6, 1.1, 0.5, 0.0])    # m
U = np.array([0, 0.3, 0.6, 0.9, 1.1, 1.2, 1.15, 0.95, 0.7, 0.35, 0.0])  # m/s

print("PART 2  THE GAUGING SURVEY")
print(f"   {len(x)} stations across a {x[-1]:.0f} m channel")
print(f"   maximum depth {H.max():.2f} m, maximum velocity {U.max():.2f} m/s\n")


# ==============================================================================
# PART 3  -  AREA, DISCHARGE, AND THE TWO RIVAL MEAN VELOCITIES
# ==============================================================================
# THE STEP STUDENTS SKIP: deciding WHAT to integrate.
#
#   Take a vertical sliver of the section, width dx.
#   Its area is        H dx                     -> integrate for the area
#   The water in it moves at U, so it carries   U H dx   -> integrate for Q
#
# The integrand for discharge is the PRODUCT of two measured columns, not
# either column on its own.
#
# UNIT CHECK, always before coding:
#   A = int H dx    -> (m)(m)      = m^2
#   Q = int U H dx  -> (m/s)(m)(m) = m^3/s
#   Q/A             -> (m^3/s)/(m^2) = m/s

print("PART 3  AREA, DISCHARGE AND MEAN VELOCITY")

A = trapz_data(x, H)               # cross-sectional area,  m^2
Q = trapz_data(x, U * H)           # discharge,             m^3/s
mean_correct = Q / A               # discharge-weighted mean velocity, m/s
mean_wrong = U.mean()              # plain arithmetic mean of the column

print(f"   area                A = {A:8.4f} m2      integrand:  H dx")
print(f"   discharge           Q = {Q:8.4f} m3/s    integrand:  U H dx")
print(f"   mean velocity     Q/A = {mean_correct:8.4f} m/s")
print(f"   plain U.mean()        = {mean_wrong:8.4f} m/s"
      f"   ({(mean_wrong - mean_correct) / mean_correct * 100:+.1f} %, and WRONG)")
print("   WHY WRONG: the arithmetic mean gives the shallow, slow banks the same")
print("   weight as the deep, fast mid-channel. Discharge weights each station")
print("   by its depth, which is what the physics does.\n")


# ==============================================================================
# PART 4  -  THE CENTROID
# ==============================================================================
# The same machinery, one line, a different question:
#
#       x_bar = ( int x H dx ) / ( int H dx )     = first moment / area
#
# This one formula also gives the centre of mass of a bar of varying density,
# the centre of pressure on a submerged gate, and the mean of a probability
# distribution. They are one idea wearing three uniforms: a weighted average.

x_bar = trapz_data(x, x * H) / A
print("PART 4  CENTROID OF THE SECTION")
print(f"   x_bar = {x_bar:.4f} m, against mid-channel at {x[-1]/2:.2f} m")
print(f"   The section leans {'right' if x_bar > x[-1]/2 else 'left'} of centre, "
      f"matching where the depth peaks.\n")


# ==============================================================================
# PART 5  -  AN ERROR BAR, FROM THE DATA YOU ALREADY HAVE
# ==============================================================================
# Field data has no exact value to compare against, so we use the ORDER of the
# method instead. Integrate twice - once with every station, once with every
# second station - and use the difference to estimate the error:
#
#       E ~ ( I_fine - I_coarse ) / 3        for a second-order rule
#
# This is Richardson extrapolation. It costs one extra summation and turns a
# bare number into a result with a stated accuracy, which is the single most
# professional thing you can add to an applied integration.

print("PART 5  ERROR ESTIMATE BY RICHARDSON EXTRAPOLATION")

I_fine = Q                                   # all 11 stations
I_coarse = trapz_data(x[::2], (U * H)[::2])  # every 2nd station: 6 of them
error_estimate = (I_fine - I_coarse) / 3

print(f"   all stations        {I_fine:.4f} m3/s")
print(f"   every 2nd station   {I_coarse:.4f} m3/s")
print(f"   estimated error     {error_estimate:+.4f} m3/s"
      f"   ({abs(error_estimate) / I_fine * 100:.2f} %)")
print(f"   REPORT AS  Q = {I_fine:.2f} +/- {abs(error_estimate):.2f} m3/s")
print("   Three significant figures is all this survey supports.\n")


# ==============================================================================
# PART 6  -  THE FIGURE
# ==============================================================================
# One figure, two quantities with different units. A second y-axis sharing the
# same x-axis is the honest way to show them together - provided both axes are
# labelled, which is why the labels below are not optional.

print("PART 6  BUILDING THE FIGURE")

fig, ax = plt.subplots(figsize=(5.8, 3.2))

# STEP 1  the channel itself, drawn as depth BELOW the water surface, so -H.
# fill_between shades the wetted area, which makes the section readable at a
# glance.
ax.fill_between(x, -H, 0, color="#cfe0f0", label="wetted section")
ax.plot(x, -H, color=DARK, lw=1.4)

# STEP 2  the velocity profile on its own axis.
# ax.twinx() creates a second axes object sharing the x-axis but with an
# independent y-axis on the right-hand side.
ax2 = ax.twinx()
ax2.plot(x, U, "o-", color=ORANGE, ms=3, lw=1)
ax2.set_ylabel("velocity (m/s)")
ax2.grid(False)                  # WHY: two grids on one figure is unreadable

# STEP 3  mark the centroid computed in PART 4
ax.axvline(x_bar, color=BLUE, ls="--", lw=1.2)
ax.text(x_bar + 0.1, -H.max() * 0.9, f"centroid {x_bar:.2f} m",
        color=BLUE, fontsize=7)

ax.set_xlabel("distance from bank (m)")
ax.set_ylabel("depth below surface (m)")
ax.set_title(f"Lab 5 demo:  Q = {Q:.2f} m3/s,  mean velocity {mean_correct:.3f} m/s")

fig.tight_layout()
out = f"{FIG}/demo_lab05.png"
fig.savefig(out)
plt.close(fig)
print(f"   figure written to {out}")
