"""
LAB 10 STARTER - Capstone: design of a haunched deck
Numerical Methods Laboratory. Prepared by Engr. Escranda.

Rename to lab10_<surname>.py before submitting.
Fill in every TODO. Keep the docstrings: they are part of the grade.

Rules for this course:
  * Build the method yourself. Library solvers are cross-checks only, and must
    be labelled as such in the code and the report.
  * Every result must carry a unit and a defensible number of significant figures.
  * Save figures to ./figures/ at 150 dpi with labelled axes.
  * Capture the console output:  python lab10_<surname>.py > lab10_output_<surname>.txt
"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

SEED = 0        # TODO: the last two digits of your student number
os.makedirs("figures", exist_ok=True)
plt.rcParams.update({"figure.dpi": 150})

L, W, P, XP = 8.0, 24.0, 15.0, 3.0      # m, kN/m, kN, m
BW, E = 0.40, 25.0e6                    # m, kPa
LIMIT = L / 360.0


def depth(x, d0):
    """Parabolic haunch profile."""
    raise NotImplementedError


def EI(x, d0):
    raise NotImplementedError


def shear_and_moment(x):
    """By cumulative integration of the load. Handle the point load explicitly."""
    raise NotImplementedError


def solve_beam(n, d0):
    """Tridiagonal finite-difference solve. Supports are KNOWN, not unknowns.

    Return (x, y). Verify against 5wL^4/384EI with constant EI BEFORE using it.
    """
    raise NotImplementedError


def design_depth(target=LIMIT):
    """Find d0 such that the maximum deflection equals the limit."""
    raise NotImplementedError

if __name__ == "__main__":
    # TODO: call your part functions here, printing every reported number.
    pass
