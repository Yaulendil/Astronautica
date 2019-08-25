"""Module dedicated to calculating Collision Detection between Objects.

Uses Numba for JIT Compilation.
"""

from numba import jit
import numpy as np


@jit
def find_collision(pair, end: float, start: float = 0.0):
    """Iteratively zero in on the first time where the distance between two
        objects is less than the sum of their radii. Return a float of seconds
        at which the objects collide, or False if they do not.
    """
    contact = pair.contact
    distance_at = pair.distance_at
    precision: int = pair.precision

    time_min: float = start
    dist_min: float = distance_at(time_min)
    time_max: float = end
    dist_max: float = distance_at(time_max)

    result = False

    # TODO: Automatically select precision such that uncertainty < object radius
    for i in range(precision):
        # Repeat the following over an increasingly precise window of time.
        time_mid = (time_min + time_max) / 2
        dist_mid = distance_at(time_mid)

        if dist_min < contact:
            # The objects are in contact at the start of this window.
            return False

        elif dist_mid < contact:
            # The objects are in contact halfway through this window.
            result = time_mid
            time_max = time_mid
            dist_max = dist_mid

        elif dist_max < contact:
            # The objects are in contact at the end of this window.
            result = time_max
            time_min = time_mid
            dist_min = dist_mid

        else:
            # The objects are not in contact at any known point; However, they
            #   may still pass through each other between points. Check the
            #   distance differences to find which half of this window would
            #   contain the pass.
            if dist_min < dist_mid < dist_max or dist_min > dist_mid < dist_max:
                # The objects seem to be diverging, but may have passed.
                half_0 = dist_mid - dist_min  # Change in distance over the first half
                half_1 = dist_max - dist_mid  # Change in distance over the second half

                if half_0 == half_1:
                    # Divergence is constant; Objects do not pass.
                    return False

                elif half_0 > half_1:
                    # First half is greater change than second half;
                    # If they pass, it happens in the second half.
                    time_min = time_mid
                    dist_min = dist_mid

                else:  # half_0 < half_1
                    # First half is smaller change than second half;
                    # If they pass, it happens in the first half.
                    time_max = time_mid
                    dist_max = dist_mid

            # elif dist_min > dist_mid < dist_max:
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
    magA = np.linalg.norm(A)
    magB = np.linalg.norm(B)

    _A = A / magA
    _B = B / magB

    cross = np.cross(_A, _B)
    denom = np.linalg.norm(cross) ** 2

    # If lines are parallel (denom=0) test if lines overlap.
    # If they don't overlap then there is a closest point solution.
    # If they do overlap, there are infinite closest positions, but there is a closest distance
    if not denom:
        d0 = np.dot(_A, (b0 - a0))

        # Overlap only possible with clamping
        if clampA0 or clampA1 or clampB0 or clampB1:
            d1 = np.dot(_A, (b1 - a0))

            # Is segment B before A?
            if d0 <= 0 >= d1:
                if clampA0 and clampB1:
                    if np.absolute(d0) < np.absolute(d1):
                        return a0, b0, np.linalg.norm(a0 - b0)
                    return a0, b1, np.linalg.norm(a0 - b1)

            # Is segment B after A?
            elif d0 >= magA <= d1:
                if clampA1 and clampB0:
                    if np.absolute(d0) < np.absolute(d1):
                        return a1, b0, np.linalg.norm(a1 - b0)
                    return a1, b1, np.linalg.norm(a1 - b1)

        # Segments overlap, return distance between parallel segments
        return None, None, np.linalg.norm(((d0 * _A) + a0) - b0)

    # Lines criss-cross: Calculate the projected closest points
    t = b0 - a0
    detA = np.linalg.det([t, _B, cross])
    detB = np.linalg.det([t, _A, cross])

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
            dot = np.dot(_B, (pA - b0))
            if clampB0 and dot < 0:
                dot = 0
            elif clampB1 and dot > magB:
                dot = magB
            pB = b0 + (_B * dot)

        # Clamp projection B
        if (clampB0 and t1 < 0) or (clampB1 and t1 > magB):
            dot = np.dot(_A, (pB - a0))
            if clampA0 and dot < 0:
                dot = 0
            elif clampA1 and dot > magA:
                dot = magA
            pA = a0 + (_A * dot)

    return pA, pB, np.linalg.norm(pA - pB)
