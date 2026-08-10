"""
LAB 09 STARTER - Normal depth and the order of a method
Numerical Methods Laboratory. Prepared by Engr. Escranda.

Rename to lab09_<surname>.py before submitting.
Fill in every TODO. Keep the docstrings: they are part of the grade.

Rules for this course:
  * Build the method yourself. Library solvers are cross-checks only, and must
    be labelled as such in the code and the report.
  * Every result must carry a unit and a defensible number of significant figures.
  * Save figures to ./figures/ at 150 dpi with labelled axes.
  * Capture the console output:  python lab09_<surname>.py > lab09_output_<surname>.txt
"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

SEED = 0        # TODO: the last two digits of your student number
os.makedirs("figures", exist_ok=True)
plt.rcParams.update({"figure.dpi": 150})

B, Z, N_MANNING, S0, Q_DESIGN = 3.0, 2.0, 0.025, 0.001, 15.0


def channel_f(y):
    """Manning residual: (1/n) A R^(2/3) sqrt(S) - Q. Zero at the normal depth."""
    raise NotImplementedError


def channel_fprime_numeric(y, h=1e-6):
    raise NotImplementedError


def channel_fprime_exact(y):
    """Derive by hand first, then code it. Show the derivation in the report."""
    raise NotImplementedError


def newton(fn, dfn, x0, es=1e-6, max_iter=50):
    """Return (root, iterations, ea, history). Guard a vanishing derivative."""
    raise NotImplementedError


def safeguarded(fn, dfn, lo, hi, xtol=1e-10, ftol=1e-12, max_iter=200):
    """Newton inside a bracket, bisection when the step misbehaves.

    Judge convergence on the BRACKET WIDTH and |f|, never on the change in x
    alone - a bisection fallback can otherwise return its own midpoint.
    """
    raise NotImplementedError

if __name__ == "__main__":
    # TODO: call your part functions here, printing every reported number.
    pass
