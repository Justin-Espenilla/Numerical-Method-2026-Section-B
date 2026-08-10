"""
LAB 01 STARTER - Rates of change from real data
Numerical Methods Laboratory. Prepared by Engr. Escranda.

Rename to lab01_<surname>.py before submitting.
Fill in every TODO. Keep the docstrings: they are part of the grade.

Rules for this course:
  * Build the method yourself. Library solvers are cross-checks only, and must
    be labelled as such in the code and the report.
  * Every result must carry a unit and a defensible number of significant figures.
  * Save figures to ./figures/ at 150 dpi with labelled axes.
  * Capture the console output:  python lab01_<surname>.py > lab01_output_<surname>.txt
"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

SEED = 0        # TODO: the last two digits of your student number
os.makedirs("figures", exist_ok=True)
plt.rcParams.update({"figure.dpi": 150})

def derivative(x, y):
    """dy/dx at every sample. Centred interior, 3-point one-sided at both ends.

    Returns an array the same length as y. Raises ValueError if x is unequally spaced.
    """
    raise NotImplementedError


def second_derivative(x, y):
    """d2y/dx2 at the interior points. Length n-2."""
    raise NotImplementedError


def moving_average(y, window):
    """Centred moving average, odd window, edge padding. Same length as y."""
    raise NotImplementedError


def reservoir_data(seed):
    """Supplied by the assignment - copy it in unchanged."""
    raise NotImplementedError


def part_a():
    """Order verification on f(x) = x^3 - 2x at x = 1.5. Error-ratio table + slopes."""
    raise NotImplementedError


def part_b():
    """Reservoir record: noise prediction, window sweep, peak inflow, inflection."""
    raise NotImplementedError


def part_c():
    """Terminal-velocity sensitivities, two verified by hand."""
    raise NotImplementedError

if __name__ == "__main__":
    # TODO: call your part functions here, printing every reported number.
    pass
