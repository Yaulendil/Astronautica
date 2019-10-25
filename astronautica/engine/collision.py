"""Module dedicated to calculating Collision Detection and Collision Response
    between Objects.

Uses Numba for JIT Compilation.
"""

from typing import List, Optional, Tuple

from numba import jit
import numpy as np

from .objects import Object

__all__ = ["distance_between_lines", "find_collisions"]


@jit(looplift=True)
def _find_collision(
    pos_a: np.ndarray,
    vel_a: np.ndarray,
    pos_b: np.ndarray,
    vel_b: np.ndarray,
    time_min: float,
    time_max: float,
    contact: float,
):
    result = 0
    error = 0

    def distance_at(time):
        a = pos_a + vel_a * time
        b = pos_b + vel_b * time
        return float(np.sqrt(np.sum(np.square(a - b))))

    dist_min: float = distance_at(time_min)
    dist_max: float = distance_at(time_max)

    # graph = {time_min: dist_min, time_max: dist_max}

    i = 0
    while contact - error > 0.001 and i < 100:
        # Repeat the following over an increasingly precise window of time.
        time_mid = (time_min + time_max) / 2
        dist_mid = distance_at(time_mid)
        i += 1

        # graph[time_mid] = dist_mid

        if dist_min < contact:
            # The objects are in contact at the start of this window. Do not
            #   interact.
            return False
            # result = False
            # break

        elif dist_mid < contact:
            # The objects are in contact halfway through this window, but not
            #   the start. Slice the first half of the window.
            result = time_mid
            error = dist_mid
            time_max = time_mid
            dist_max = dist_mid

        elif dist_max < contact:
            # The objects are in contact at the end of this window, but not at
            #   the midpoint. Slice the second half of the window.
            result = time_max
            error = dist_max
            time_min = time_mid
            dist_min = dist_mid

        else:
            # The objects are not in contact at any known point; However, they
            #   may still pass through each other between points. Check the
            #   distance differences to find which half of this window would
            #   contain the pass.
            half_0 = dist_mid - dist_min  # Change in distance over the first half
            half_1 = dist_max - dist_mid  # Change in distance over the second half

            if half_0 == -half_1:
                # Vergence is constant.
                result = False
                break

            elif half_0 == -half_1:
                # Midpoint is the closest together the objects come.
                result = False
                break

            elif dist_min < dist_mid < dist_max:
                # The objects seem to be diverging, but may have passed.

                if half_0 > half_1:
                    # First half is greater change than second half;
                    # If they pass, it happens in the second half.
                    time_min = time_mid
                    dist_min = dist_mid

                else:  # half_0 < half_1
                    # First half is smaller change than second half;
                    # If they pass, it happens in the first half.
                    time_max = time_mid
                    dist_max = dist_mid

            elif dist_min > dist_mid > dist_max or (
                dist_min > dist_mid and dist_max > dist_mid
            ):
                # The objects seem to be converging, or to have passed.

                if half_0 < half_1:
                    # First half is smaller change than second half;
                    # If they pass, it happens in the first half.
                    time_min = time_mid
                    dist_min = dist_mid

                else:  # half_0 > half_1
                    # First half is greater change than second half;
                    # If they pass, it happens in the second half.
                    time_max = time_mid
                    dist_max = dist_mid

            else:
                # No other condition could result in an impact
                result = False
                break

    # print(i, repr({k: graph[k] for k in sorted(graph.keys())}))
    return result


@jit(forceobj=True, nopython=False)
def find_collisions(
    seconds: float, objs: List[Tuple[List[Object], List[Object]]]
) -> List[Tuple[float, Tuple[Object, Object]]]:
    collisions: List[Tuple[float, Tuple[Object, Object]]] = []

    for list_a, list_b in objs:
        for obj_a in list_a[-1:0:-1]:
            list_b.pop(-1)
            start_a = obj_a.frame.position
            end_a = obj_a.frame.position + obj_a.frame.velocity * seconds

            for obj_b in list_b:
                if obj_a.frame.domain != obj_b.frame.domain:
                    continue
                start_b = obj_b.frame.position
                contact = obj_a.radius + obj_b.radius

                if (start_a - start_b).length < contact:
                    continue

                end_b = obj_b.frame.position + obj_b.frame.velocity * seconds
                nearest_a, nearest_b, proximity = distance_between_lines(
                    start_a, end_a, start_b, end_b
                )

                if proximity < contact:
                    # Objects look like they might collide.
                    impact = _find_collision(
                        obj_a.frame.position,
                        obj_a.frame.velocity,
                        obj_b.frame.position,
                        obj_b.frame.velocity,
                        0.0,
                        seconds,
                        contact,
                    )
                    if impact is not False:
                        collisions.append((impact, (obj_a, obj_b)))

    return collisions


# Implementation by Fnord on StackOverflow
# https://stackoverflow.com/a/18994296


@jit(forceobj=True, nopython=False)
def distance_between_lines(
    a0: np.ndarray,
    a1: np.ndarray,
    b0: np.ndarray,
    b1: np.ndarray,
    clampAll: bool = True,
    clampA0: bool = False,
    clampA1: bool = False,
    clampB0: bool = False,
    clampB1: bool = False,
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], float]:
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
    A = np.subtract(a1, a0)
    B = np.subtract(b1, b0)
    magA = np.linalg.norm(A)
    magB = np.linalg.norm(B)

    # print(f"\n\n{A} / {magA}; {B} / {magB}")
    _A = np.true_divide(A, magA) if magA != 0 else A
    _B = np.true_divide(B, magB) if magB != 0 else B
    # print(f"{_A}, {_B}")

    cross = np.cross(_A, _B)
    denom = np.square(np.linalg.norm(cross))

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
    t = np.subtract(b0, a0)

    # print(f"\n\ndetA = det({[t, _B, cross]}); detB = det({[t, _A, cross]})")
    detA = np.linalg.det([t, _B, cross])
    detB = np.linalg.det([t, _A, cross])
    # print(f"{detA}, {detB}")

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
