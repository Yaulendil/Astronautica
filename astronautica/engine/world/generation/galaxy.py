from secrets import randbelow
from typing import Sequence, Tuple

from numba import jit
import numpy as np
from numpy import random as npr

from engine.space.geometry import from_spherical, to_spherical


def apply_swirl(stars: np.ndarray, deg: float, factor: float) -> None:
    for star in stars:
        rho, theta, phi = to_spherical(*star)
        new = from_spherical(rho, theta, phi - deg - (deg * factor * rho))
        star[:] = new


@jit(forceobj=True)
def offset(percent: float = 15) -> float:
    return 1 + ((randbelow(percent * 2) - percent) / 100)


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

    core = generate_stars(int(stars_in_core * offset()), aradius / 12, o)
    apply_swirl(core, 20, 7.5)

    cloud = generate_stars(int(stars_in_cloud * offset()), aradius, o)

    cluster_arrays = []
    for _ in range(clusters):
        cluster_arrays.extend(
            generate_stars(
                int(stars_per_cluster * offset()),
                (h := size / 2),
                from_spherical(npr.normal(0, h), 0, randbelow(360)),
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
                        stars_per_arm_cluster * offset()
                        * (1 - ((cluster_num - 1) / clusters_per_arm))
                    ),
                    (
                        (sig := (radius / (2 + cluster_num))),
                        sig,
                        size[2] / 3,
                    ),
                    from_spherical(0.35 * cluster_num, 0, (360 / arms) * arm_num),
                )
            )

        arm = np.concatenate(arm)
        arm_arrays.append(arm)

    arm_arrays = np.concatenate(arm_arrays) if arm_arrays else np.array([])
    apply_swirl(arm_arrays, arm_turn, arm_curve)

    return [x for x in (core, cloud, cluster_arrays, arm_arrays) if len(x) > 0]
