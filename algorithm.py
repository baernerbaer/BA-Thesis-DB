
from math import pow, log2, e

'''
This file includes the implementation of the spaced-repetition algorithm by David Buehler

@author David Buehler
@date January/February/March 2023
'''


def pow_z(x, y):
    """Catches the edge case 'zero to the power of y', which throws a RangeError when using math.pow"""
    if x == 0 and y != 0:
        return 0
    return pow(x, y)


def calculate_stability_difficulty(s_i, delta_t, d_i, grade, new_card=False):
    """Calculates the new stability and difficulty according to the pre-defined algorithm (see algorithm.pdf for details)"""
    if grade > 4 or grade < 1:
        raise Exception("Grade out of bounds")
    mean_reversion_rate = 0.2

    # if the card is new, we need to set the previous values as defined in the algorithm
    if new_card:
        s_i = 1
        d_i = 5 + 3 - grade
        print(f"[D] New card => s0 = {s_i}, d0 = {d_i}")

    r = pow_z(0.9, (delta_t / s_i))
    print(f"[D] R = {r}")

    d_i_p1 = d_i + 3 - grade + mean_reversion_rate * (2 - d_i + grade)
    print(f"[D] d_i+1 = {d_i_p1}")
    if grade == 1:  # failure of recall
        s_i_p1 = pow_z(e, -0.041) * pow_z(d_i_p1, -0.041) * pow_z(s_i, 0.377) * pow_z(1-r, -0.227)
        print(f"[D] s_i+1 = sf = {s_i_p1}")
    else:  # Other grade = successful recall
        s_i_p1 = s_i * (pow_z(e, 3.81) * pow_z(0.73, d_i_p1-1) * pow_z(s_i / -log2(0.9), -0.127) * pow_z(1-r, 0.970) + 1)
        print(f"[D] s_i+1 = {s_i_p1}")
    return int(round(s_i_p1)), d_i_p1
