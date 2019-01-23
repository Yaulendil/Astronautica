# This module is meant to be compiled to C via Cython

import numpy as _np


def _avg(*numbers):
    return sum(numbers) / len(numbers)


def find_collision(pair, end: float, start=0.0):
    """
    Iteratively zero in on the first time where the distance between two
    objects is less than the sum of their radii

    Returns a float of seconds at which the objects collide, or False if they do not
    """

    t0 = start  # Time 0, minimum time
    d0 = pair.distance_at(t0)
    t1 = end  # Time 1, maximum time
    d1 = pair.distance_at(t1)
    result = False

    # TODO: Automatically select precision such that uncertainty < object radius
    for i in range(pair.precision):
        # Repeat the following over a steadily more precise window of time
        tm = _avg(t0, t1)  # Time M, middle time
        dm = pair.distance_at(tm)
        if d0 < pair.contact:
            # The objects are in contact at the start of this window
            result = False
            break
        elif dm < pair.contact:
            # The objects are in contact halfway through this window
            result = tm
            t1 = tm
            d1 = dm
        elif d1 < pair.contact:
            # The objects are in contact at the end of this window
            result = t1
            t0 = tm
            d0 = dm
        else:
            # The objects are not in contact at any known point;
            # However, they may still pass through each other between points
            if d0 < dm < d1 or d0 > dm < d1:
                # The objects seem to be diverging, but may have passed
                half_0 = dm - d0  # Change in distance over the first half
                half_1 = d1 - dm  # Change in distance over the second half
                if half_0 == half_1:
                    # Divergence is constant; Objects do not pass
                    result = False
                    break
                elif half_0 > half_1:
                    # First half is greater change than second half;
                    # If they pass, it happens in the second half
                    t0 = tm
                    d0 = dm
                else:  # half_0 < half_1
                    # First half is smaller change than second half;
                    # If they pass, it happens in the first half
                    t1 = tm
                    d1 = dm
            # elif d0 > dm < d1:
            #     # The objects pass each other during this window
            else:
                # No other condition could result in an impact
                return False
    return result


# Implementation by Fnord on StackOverflow
# https://stackoverflow.com/a/18994296


def distance_between_lines(
    a0,
    a1,
    b0,
    b1,
    clampAll=True,
    clampA0=False,
    clampA1=False,
    clampB0=False,
    clampB1=False,
):
    """ Given two lines defined by numpy.array pairs (a0,a1,b0,b1)
        Return the closest points on each segment and their distance
    """

    # If clampAll=True, set all clamps to True
    if clampAll:
        clampA0 = True
        clampA1 = True
        clampB0 = True
        clampB1 = True

    # Calculate denomitator
    A = a1 - a0
    B = b1 - b0
    magA = _np.linalg.norm(A)
    magB = _np.linalg.norm(B)

    _A = A / magA
    _B = B / magB

    cross = _np.cross(_A, _B)
    denom = _np.linalg.norm(cross) ** 2

    # If lines are parallel (denom=0) test if lines overlap.
    # If they don't overlap then there is a closest point solution.
    # If they do overlap, there are infinite closest positions, but there is a closest distance
    if not denom:
        d0 = _np.dot(_A, (b0 - a0))

        # Overlap only possible with clamping
        if clampA0 or clampA1 or clampB0 or clampB1:
            d1 = _np.dot(_A, (b1 - a0))

            # Is segment B before A?
            if d0 <= 0 >= d1:
                if clampA0 and clampB1:
                    if _np.absolute(d0) < _np.absolute(d1):
                        return a0, b0, _np.linalg.norm(a0 - b0)
                    return a0, b1, _np.linalg.norm(a0 - b1)

            # Is segment B after A?
            elif d0 >= magA <= d1:
                if clampA1 and clampB0:
                    if _np.absolute(d0) < _np.absolute(d1):
                        return a1, b0, _np.linalg.norm(a1 - b0)
                    return a1, b1, _np.linalg.norm(a1 - b1)

        # Segments overlap, return distance between parallel segments
        return None, None, _np.linalg.norm(((d0 * _A) + a0) - b0)

    # Lines criss-cross: Calculate the projected closest points
    t = b0 - a0
    detA = _np.linalg.det([t, _B, cross])
    detB = _np.linalg.det([t, _A, cross])

    t0 = detA / denom
    t1 = detB / denom

    pA = a0 + (_A * t0)  # Projected closest point on segment A
    pB = b0 + (_B * t1)  # Projected closest point on segment B

    # Clamp projections
    if clampA0 or clampA1 or clampB0 or clampB1:
        if clampA0 and t0 < 0:
            pA = a0
        elif clampA1 and t0 > magA:
            pA = a1

        if clampB0 and t1 < 0:
            pB = b0
        elif clampB1 and t1 > magB:
            pB = b1

        # Clamp projection A
        if (clampA0 and t0 < 0) or (clampA1 and t0 > magA):
            dot = _np.dot(_B, (pA - b0))
            if clampB0 and dot < 0:
                dot = 0
            elif clampB1 and dot > magB:
                dot = magB
            pB = b0 + (_B * dot)

        # Clamp projection B
        if (clampB0 and t1 < 0) or (clampB1 and t1 > magB):
            dot = _np.dot(_A, (pB - a0))
            if clampA0 and dot < 0:
                dot = 0
            elif clampA1 and dot > magA:
                dot = magA
            pA = a0 + (_A * dot)

    return pA, pB, _np.linalg.norm(pA - pB)
