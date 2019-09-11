from itertools import cycle
from secrets import randbelow
from sys import exit
from typing import Sequence, Tuple

from numba import jit
import numpy as np
from numpy import random as npr

# from ..physics.geometry import cart3_polar3, polar3_cart3

from math import radians, degrees

# noinspection NonAsciiCharacters
@jit(nopython=True)
def polar_convert(ρ: float, θ: float, φ: float) -> Tuple[float, float, float]:
    # TODO: REMOVE
    """Given polar coordinates in the conventions of Physics, convert to
        conventions of Navigation.
    """
    # Physics conventions: +θ = North of East from 0° to 360°, +φ = Down from Zenith
    #   # North: θ = 90°
    #   # South: θ = 270°
    #   # Zenith: φ = 0°
    # Navigational format: +θ = West of South from -180° to 180°, +φ = Up from Horizon
    #   # North: θ = 0°
    #   # South: θ = -180° OR 180°
    #   # Zenith: φ = 90°

    θ = 180 - ((90 + θ) % 360)
    φ = 90 - φ
    if φ == 90 or φ == -90:
        θ = 0
    return ρ, φ, θ


@jit(nopython=True)
def rad_deg(theta: float) -> float:
    # TODO: REMOVE
    """Convert Radians to Degrees."""
    return np.round(degrees(theta), 5)


@jit(nopython=True)
def deg_rad(theta: float) -> float:
    # TODO: REMOVE
    """Convert Degrees to Radians."""
    return np.round(radians(theta), 5)


# noinspection NonAsciiCharacters
@jit(nopython=True)
def cart3_polar3(x: float, y: float, z: float) -> Tuple[float, float, float]:
    # TODO: REMOVE
    """Convert three-dimensional Cartesian Coordinates to Polar."""
    ρ = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    φ = rad_deg(np.arccos(z / ρ))
    θ = rad_deg(np.arctan2(y, x))
    return polar_convert(ρ, θ, φ)
    # return ρ, θ, φ


# noinspection NonAsciiCharacters
@jit(nopython=True)
def polar3_cart3(ρ: float, θ: float, φ: float) -> Tuple[float, float, float]:
    # TODO: REMOVE
    """Convert three-dimensional Polar Coordinates to Cartesian."""
    θ = np.pi / 2 - deg_rad(θ)
    φ = deg_rad(φ)
    x = ρ * np.cos(φ) * np.sin(θ)
    y = ρ * np.sin(φ) * np.sin(θ)
    z = ρ * np.cos(θ)
    return x, y, z


# @jit(nopython=True)
def apply_swirl(stars: np.ndarray, deg: float, factor: float) -> None:
    for star in stars:
        rho, theta, phi = cart3_polar3(*star)
        new = polar3_cart3(rho, theta, phi + deg + (deg * factor * rho))
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
    cluster_arrays = (
        np.concatenate(
            [
                generate_stars(stars_per_cluster, size / 2, center)
                for center in [
                    polar3_cart3(npr.normal(0, size / 2), 0, randbelow(360))
                    for _ in range(clusters)
                ]
            ]
        )
        if clusters
        else np.array([])
    )

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
                    polar3_cart3(0.35 * cluster_num, 0, (360 / arms) * arm_num),
                )
            )

        arm = np.concatenate(arm)
        apply_swirl(arm, arm_turn, arm_curve)
        arm_arrays.append(arm)
    else:
        arm_arrays = np.concatenate(arm_arrays) if arm_arrays else np.array([])

    return list(filter(np.ndarray.any, ([core, cloud, cluster_arrays, arm_arrays])))


## v ## IGNORE THIS ## v ##
if __name__ == "__main__":
    from blessings import Terminal
    from matplotlib import use

    use("GTK3Cairo")

    from matplotlib import pyplot
    from mpl_toolkits.mplot3d import Axes3D

    T = Terminal()

    # fig = pyplot.figure(figsize=(5.6, 4.2))
    # fig = pyplot.figure(figsize=(6.4, 4.8))
    fig = pyplot.figure(figsize=(8, 8))

    ax = Axes3D(fig, azim=-45, elev=30)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    scale = 1.5
    ax.set_xlim3d(-scale, scale)  # , xmin=3, xmax=3)
    ax.set_ylim3d(-scale, scale)  # , ymin=3, ymax=3)
    ax.set_zlim3d(-scale, scale)  # , zmin=3, zmax=3)

    galaxy = generate_galaxy((1.4, 1, 0.2), arms=5)
    print(f"Generated {sum(map(len, galaxy))} stars.")

    for color, group in zip(
        cycle(("#bb0000", "#bbbb00", "#00bb00", "#00bbbb", "#0000bb", "#bb00bb")),
        galaxy,
    ):
        ax.scatter(group[..., 0], group[..., 1], group[..., 2], c="#000000", s=2)

    # pyplot.show()
    fig.savefig("demo.png")  # , bbox_inches='tight')
    ax.set_axis_off()

    try:
        with T.hidden_cursor():
            for angle in range(1, 361):
                ax.view_init(30, angle - 1)
                fig.savefig(f"gif/frame-{angle:0>3}.png")
                with T.location():
                    print(
                        f"Frame {angle:0>3}/360  {angle/360:>6.1%}  ",
                        end="",
                        flush=True,
                    )
                # pyplot.draw()
                # pyplot.pause(.1)
    except KeyboardInterrupt:
        print()
        exit(1)
    else:
        print()
