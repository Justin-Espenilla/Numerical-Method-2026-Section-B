"""
LAB 03 STARTER - Downhill in the fog
Numerical Methods Laboratory. Prepared by Engr. Escranda.

Rename to lab03_<surname>.py before submitting.
Fill in every TODO. Keep the docstrings: they are part of the grade.

Rules for this course:
  * Build the method yourself. Library solvers are cross-checks only, and must
    be labelled as such in the code and the report.
  * Every result must carry a unit and a defensible number of significant figures.
  * Save figures to ./figures/ at 150 dpi with labelled axes.
  * Capture the console output:  python lab03_<surname>.py > lab03_output_<surname>.txt
"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

SEED = 0        # TODO: the last two digits of your student number
os.makedirs("figures", exist_ok=True)
plt.rcParams.update({"figure.dpi": 150})

def gradient(func, x, rel_h=1e-6):
    """Numerical gradient by scaled centred differences."""
    raise NotImplementedError


def gradient_descent(func, x0, alpha=0.01, tol=1e-6, max_iter=50000, mode="fixed"):
    """Minimise func. mode is 'fixed', 'backtrack' or 'momentum'.

    Returns (x, f, n_iter, history). Stop on |grad| < tol. Raise on divergence.
    Count function evaluations - the assignment marks cost in evaluations.
    """
    raise NotImplementedError


def creep_data(seed):
    """Supplied by the assignment - copy it in unchanged."""
    raise NotImplementedError

if __name__ == "__main__":
    # TODO: call your part functions here, printing every reported number.
    pass
