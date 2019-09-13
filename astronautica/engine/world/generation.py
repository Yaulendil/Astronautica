from secrets import randbelow
from typing import Sequence, Tuple

from numba import jit
import numpy as np
from numpy import random as npr

from ..physics.geometry import to_spherical, from_spherical

# from math import radians, degrees
#
# # noinspection NonAsciiCharacters
# @jit(nopython=True)
# def polar_convert(ρ: float, θ: float, φ: float) -> Tuple[float, float, float]:
#     # TODO: REMOVE
#     """Given polar coordinates in the conventions of Physics, convert to
#         conventions of Navigation.
#     """
#     # Physics conventions: +θ = North of East from 0° to 360°, +φ = Down from Zenith
#     #   # North: θ = 90°
#     #   # South: θ = 270°
#     #   # Zenith: φ = 0°
#     # Navigational format: +θ = West of South from -180° to 180°, +φ = Up from Horizon
#     #   # North: θ = 0°
#     #   # South: θ = -180° OR 180°
#     #   # Zenith: φ = 90°
#
#     θ = 180 - ((90 + θ) % 360)
#     φ = 90 - φ
#     if φ == 90 or φ == -90:
#         θ = 0
#     return ρ, φ, θ
#
#
# @jit(nopython=True)
# def rad_deg(theta: float) -> float:
#     # TODO: REMOVE
#     """Convert Radians to Degrees."""
#     return np.round(degrees(theta), 5)
#
#
# @jit(nopython=True)
# def deg_rad(theta: float) -> float:
#     # TODO: REMOVE
#     """Convert Degrees to Radians."""
#     return np.round(radians(theta), 5)
#
#
# # noinspection NonAsciiCharacters
# @jit(nopython=True)
# def cart3_polar3(x: float, y: float, z: float) -> Tuple[float, float, float]:
#     # TODO: REMOVE
#     """Convert three-dimensional Cartesian Coordinates to Polar."""
#     ρ = np.sqrt(x ** 2 + y ** 2 + z ** 2)
#     φ = rad_deg(np.arccos(z / ρ))
#     θ = rad_deg(np.arctan2(y, x))
#     return polar_convert(ρ, θ, φ)
#     # return ρ, θ, φ
#
#
# # noinspection NonAsciiCharacters
# @jit(nopython=True)
# def polar3_cart3(ρ: float, θ: float, φ: float) -> Tuple[float, float, float]:
#     # TODO: REMOVE
#     """Convert three-dimensional Polar Coordinates to Cartesian."""
#     θ = np.pi / 2 - deg_rad(θ)
#     φ = deg_rad(φ)
#     x = ρ * np.cos(φ) * np.sin(θ)
#     y = ρ * np.sin(φ) * np.sin(θ)
#     z = ρ * np.cos(θ)
#     return x, y, z


# @jit(nopython=True)
def apply_swirl(stars: np.ndarray, deg: float, factor: float) -> None:
    for star in stars:
        rho, theta, phi = to_spherical(*star)
        new = from_spherical(rho, theta, phi - deg - (deg * factor * rho))
        star[:] = new


@jit(forceobj=True)
def generate_stars(count: int, sigma, center) -> np.ndarray:
    return np.array(
        [
            (
                npr.normal(center[0], sigma[0]),
                npr.normal(center[1], sigma[1]),
                npr.normal(center[2], sigma[2]),
            )
            for _ in range(count)
        ]
    )


def generate_galaxy(
    size: Tuple[float, float, float],
    stars_in_core: int = 150,
    stars_in_cloud: int = 50,
    clusters: int = 4,
    stars_per_cluster: int = 20,
    arms: int = 4,
    arm_turn: float = 20,
    arm_curve: float = 1.75,
    clusters_per_arm: int = 8,
    stars_per_arm_cluster: int = 40,
) -> Sequence[np.ndarray]:
    o = (0, 0, 0)
    radius = sum(sorted(size, reverse=True)[:2]) / 2
    aradius = np.array((radius, radius, radius))
    size = np.array(size)

    core = generate_stars(stars_in_core, aradius / 12, o)
    apply_swirl(core, 20, 7.5)

    cloud = generate_stars(stars_in_cloud, aradius, o)

    cluster_arrays = []
    # for center in [
    #     polar3_cart3(npr.normal(0, size / 2), 0, randbelow(360))
    for _ in range(clusters):
        cluster_arrays.extend(
            generate_stars(
                stars_per_cluster,
                size / 2,
                from_spherical(npr.normal(0, size / 2), 0, randbelow(360)),
            )
        )
    cluster_arrays = np.concatenate(cluster_arrays) if cluster_arrays else np.array([])

    arm_arrays = []
    for arm_num in range(arms):
        arm = []
        for cluster_num in range(1, clusters_per_arm + 1):
            arm.append(
                generate_stars(
                    int(
                        stars_per_arm_cluster
                        * (1 - ((cluster_num - 1) / clusters_per_arm))
                    ),
                    (
                        radius / (2 + cluster_num),
                        radius / (2 + cluster_num),
                        size[2] / 3,
                    ),
                    from_spherical(0.35 * cluster_num, 0, (360 / arms) * arm_num),
                )
            )

        arm = np.concatenate(arm)
        apply_swirl(arm, arm_turn, arm_curve)
        arm_arrays.append(arm)
    else:
        arm_arrays = np.concatenate(arm_arrays) if arm_arrays else np.array([])

    return [x for x in (core, cloud, cluster_arrays, arm_arrays) if len(x) > 0]
