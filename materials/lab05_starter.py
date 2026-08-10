"""
LAB 05 STARTER - Discharge, work and RMS
Numerical Methods Laboratory. Prepared by Engr. Escranda.

Rename to lab05_<surname>.py before submitting.
Fill in every TODO. Keep the docstrings: they are part of the grade.

Rules for this course:
  * Build the method yourself. Library solvers are cross-checks only, and must
    be labelled as such in the code and the report.
  * Every result must carry a unit and a defensible number of significant figures.
  * Save figures to ./figures/ at 150 dpi with labelled axes.
  * Capture the console output:  python lab05_<surname>.py > lab05_output_<surname>.txt
"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

SEED = 0        # TODO: the last two digits of your student number
os.makedirs("figures", exist_ok=True)
plt.rcParams.update({"figure.dpi": 150})

def trapz_data(x, y):
    raise NotImplementedError


def discharge(x, H, U):
    """Q = integral U H dx. State the unit check in the report before coding."""
    raise NotImplementedError


def centroid_x(x, H):
    """First moment divided by area."""
    raise NotImplementedError


def rms(t, v):
    """Root mean square over the record. Verify on a pure sine before use."""
    raise NotImplementedError


def richardson_trapz(x, y):
    """Return (I_fine, I_coarse, error_estimate, I_improved)."""
    raise NotImplementedError

if __name__ == "__main__":
    # TODO: call your part functions here, printing every reported number.
    pass
