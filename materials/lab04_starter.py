"""
LAB 04 STARTER - Totals from rates
Numerical Methods Laboratory. Prepared by Engr. Escranda.

Rename to lab04_<surname>.py before submitting.
Fill in every TODO. Keep the docstrings: they are part of the grade.

Rules for this course:
  * Build the method yourself. Library solvers are cross-checks only, and must
    be labelled as such in the code and the report.
  * Every result must carry a unit and a defensible number of significant figures.
  * Save figures to ./figures/ at 150 dpi with labelled axes.
  * Capture the console output:  python lab04_<surname>.py > lab04_output_<surname>.txt
"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

SEED = 0        # TODO: the last two digits of your student number
os.makedirs("figures", exist_ok=True)
plt.rcParams.update({"figure.dpi": 150})

def left_rect(f, a, b, n):
    raise NotImplementedError


def trapezoid(f, a, b, n):
    raise NotImplementedError


def simpson(f, a, b, n):
    """Composite Simpson 1/3. Must reject odd n with a clear error."""
    raise NotImplementedError


def trapz_data(x, y):
    """Trapezoidal rule for tabulated data with UNEQUAL spacing."""
    raise NotImplementedError


def cumulative_trapz(x, y):
    """Running integral, same length as x, starting at zero."""
    raise NotImplementedError


def storm_record(seed):
    """Supplied by the assignment - copy it in unchanged."""
    raise NotImplementedError

if __name__ == "__main__":
    # TODO: call your part functions here, printing every reported number.
    pass
