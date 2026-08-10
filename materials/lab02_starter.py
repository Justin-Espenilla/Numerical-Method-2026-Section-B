"""
LAB 02 STARTER - Where should the money go?
Numerical Methods Laboratory. Prepared by Engr. Escranda.

Rename to lab02_<surname>.py before submitting.
Fill in every TODO. Keep the docstrings: they are part of the grade.

Rules for this course:
  * Build the method yourself. Library solvers are cross-checks only, and must
    be labelled as such in the code and the report.
  * Every result must carry a unit and a defensible number of significant figures.
  * Save figures to ./figures/ at 150 dpi with labelled axes.
  * Capture the console output:  python lab02_<surname>.py > lab02_output_<surname>.txt
"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

SEED = 0        # TODO: the last two digits of your student number
os.makedirs("figures", exist_ok=True)
plt.rcParams.update({"figure.dpi": 150})

def delta(p):
    """Midspan deflection of a simply supported beam, central point load, in metres.

    p is a dict with keys P, L, E, b, h.
    """
    raise NotImplementedError


def partial(func, params, key, rel_h=1e-6):
    """Centred-difference partial derivative with a SCALED perturbation."""
    raise NotImplementedError


def sensitivity_table(func, params):
    """Return (name, value, dfdx, S) sorted by |S| descending."""
    raise NotImplementedError


def propagate(func, params, sigmas):
    """Return (worst_case, rss) uncertainty."""
    raise NotImplementedError


def monte_carlo(func, params, sigmas, n=20000, seed=SEED):
    """Return the sample array of func under normal parameter scatter."""
    raise NotImplementedError

if __name__ == "__main__":
    # TODO: call your part functions here, printing every reported number.
    pass
