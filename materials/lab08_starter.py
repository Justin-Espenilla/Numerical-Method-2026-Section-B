"""
LAB 08 STARTER - Consolidation by series summation
Numerical Methods Laboratory. Prepared by Engr. Escranda.

Rename to lab08_<surname>.py before submitting.
Fill in every TODO. Keep the docstrings: they are part of the grade.

Rules for this course:
  * Build the method yourself. Library solvers are cross-checks only, and must
    be labelled as such in the code and the report.
  * Every result must carry a unit and a defensible number of significant figures.
  * Save figures to ./figures/ at 150 dpi with labelled axes.
  * Capture the console output:  python lab08_<surname>.py > lab08_output_<surname>.txt
"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

SEED = 0        # TODO: the last two digits of your student number
os.makedirs("figures", exist_ok=True)
plt.rcParams.update({"figure.dpi": 150})

def scarborough(n_sig_figs):
    """Stopping tolerance in percent for n correct significant figures."""
    raise NotImplementedError


def consolidation_U(T, es, max_terms=5000):
    """Terzaghi average degree of consolidation.

    Return (U, terms_used, ea). Stop on the approximate relative error, cap the
    term count, and handle T <= 0 as a special case.
    """
    raise NotImplementedError


def exp_series(x, n_terms=300):
    """Return (sum, largest_term_magnitude). Use the recurrence, no factorials."""
    raise NotImplementedError


def machine_epsilon():
    """By halving. Do not call np.finfo for the answer."""
    raise NotImplementedError

if __name__ == "__main__":
    # TODO: call your part functions here, printing every reported number.
    pass
