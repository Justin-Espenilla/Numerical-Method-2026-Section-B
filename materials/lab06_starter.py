"""
LAB 06 STARTER - Solving a truss
Numerical Methods Laboratory. Prepared by Engr. Escranda.

Rename to lab06_<surname>.py before submitting.
Fill in every TODO. Keep the docstrings: they are part of the grade.

Rules for this course:
  * Build the method yourself. Library solvers are cross-checks only, and must
    be labelled as such in the code and the report.
  * Every result must carry a unit and a defensible number of significant figures.
  * Save figures to ./figures/ at 150 dpi with labelled axes.
  * Capture the console output:  python lab06_<surname>.py > lab06_output_<surname>.txt
"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

SEED = 0        # TODO: the last two digits of your student number
os.makedirs("figures", exist_ok=True)
plt.rcParams.update({"figure.dpi": 150})

def gauss_naive(A, b):
    """Elimination without pivoting. Must not modify the caller's arrays."""
    raise NotImplementedError


def gauss_pivot(A, b, tol=1e-12):
    """Elimination with partial pivoting and a singularity check."""
    raise NotImplementedError


def residual(A, x, b):
    """Maximum absolute residual."""
    raise NotImplementedError


def assemble_truss(joints, members, loads, supports):
    """Build the equilibrium matrix by LOOPING over joints, not by typing entries.

    Return (A, b, unknown_names). Tension positive.
    """
    raise NotImplementedError

if __name__ == "__main__":
    # TODO: call your part functions here, printing every reported number.
    pass
