"""
LAB 07 STARTER - Load cases, seepage and conditioning
Numerical Methods Laboratory. Prepared by Engr. Escranda.

Rename to lab07_<surname>.py before submitting.
Fill in every TODO. Keep the docstrings: they are part of the grade.

Rules for this course:
  * Build the method yourself. Library solvers are cross-checks only, and must
    be labelled as such in the code and the report.
  * Every result must carry a unit and a defensible number of significant figures.
  * Save figures to ./figures/ at 150 dpi with labelled axes.
  * Capture the console output:  python lab07_<surname>.py > lab07_output_<surname>.txt
"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

SEED = 0        # TODO: the last two digits of your student number
os.makedirs("figures", exist_ok=True)
plt.rcParams.update({"figure.dpi": 150})

def lu_decompose(A):
    """Doolittle LU with partial pivoting. Return (LU, piv)."""
    raise NotImplementedError


def lu_solve(LU, piv, b):
    """Forward then back substitution. Cost n^2."""
    raise NotImplementedError


def is_diagonally_dominant(A):
    raise NotImplementedError


def gauss_seidel(A, b, tol=1e-8, max_iter=20000, lam=1.0):
    """Gauss-Seidel with optional relaxation. Return (x, iterations, history)."""
    raise NotImplementedError


def seepage_grid(nx, ny, ...):   # TODO: define your own signature
    """Solve Laplace on the grid with the sheet pile as a no-flow boundary."""
    raise NotImplementedError

if __name__ == "__main__":
    # TODO: call your part functions here, printing every reported number.
    pass
