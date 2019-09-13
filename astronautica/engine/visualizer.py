from itertools import starmap
from sys import exit
from typing import Tuple

from blessings import Terminal
from matplotlib import use

use("GTK3Cairo")

from matplotlib import pyplot
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

from .physics.geometry import (
    cart3_polar3,
    polar3_cart3,
)  # , cartesian_to_spherical, spherical_to_cartesian


T = Terminal()


def axes(
    fig,
    min_: float = -1,
    max_: float = 1,
    *,
    # azim: float = 155,
    azim: float = 245,
    elev: float = 30,
) -> Axes3D:
    ax = Axes3D(fig, azim=azim, elev=elev)  # , proj_type="ortho")

    # ax.set_title("asdf")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    ax.set_xlim3d(min_, max_)
    ax.set_ylim3d(min_, max_)
    ax.set_zlim3d(-1, 1)

    return ax


def make_test(x: float = 0.8, y: float = 0.6, z: float = 0.7, *, filename="axes.png"):
    fig = pyplot.figure(figsize=(4, 4))
    ax = axes(fig)  # , 0, 1)

    rho, theta, phi = cart3_polar3(x, y, z)

    color_rho = "red"
    color_theta = "green"
    color_phi = "blue"
    grey = "#777777"
    seg = 25
    w = 0.1

    def mark(x_, y_, z_):
        ax.text(x_, y_, z_, f"{np.round((x_, y_, z_), 2)}")

    def plot(*points: Tuple[float, float, float], **kw):
        points = np.array(points)
        return ax.plot(points[..., 0], points[..., 1], points[..., 2], **kw)

    # Axis Line.
    plot((0, rho, 0), (0, 0, 0), c=grey)

    arc_theta = lambda d=1: starmap(
        polar3_cart3, ((rho * d, (theta / seg * i), phi) for i in range(seg + 1))
    )
    arc_phi = lambda d=1: starmap(
        polar3_cart3, ((rho * d, 0, (phi / seg * i)) for i in range(seg + 1))
    )

    # # SECONDARY Labels.
    # ax.text(0, rho * 0.52, 0, "ρ", c="black")
    # ax.text(*polar3_cart3(rho * 0.52, (theta / 2), phi), "θ", c="black")
    # ax.text(*polar3_cart3(rho * 0.52, 0, (phi / 2)), "φ", c="black")
    # plot(*arc_theta(0.5), c=grey)  # GREY Theta Arc.
    # plot(*arc_phi(0.5), c=grey)  # GREY Phi Arc.

    plot(*arc_theta(), c=color_theta)  # Theta Arc.
    plot(*arc_phi(), c=color_phi)  # Phi Arc.

    # Right Angle.
    plot(
        (x, y, z * w),
        (x * (1 - w), y * (1 - w), z * w),
        (x * (1 - w), y * (1 - w), 0),
        c="black",
    )

    # Coordinate Triangle.
    plot((0, 0, 0), (x, y, z), (x, y, 0), (0, 0, 0), c=grey)
    plot((0, 0, 0), (x, y, z), c=color_rho)

    mark(x, y, z)  # Endpoint.
    mark(x, y, 0)  # Below Endpoint.

    # COLORED Labels.
    ax.text(
        x, y, z,
        f"ρ ({np.round(rho, 2)})",
        c=color_rho,
        fontsize=12,
        horizontalalignment="right",
        verticalalignment="bottom",
    )
    ax.text(
        *polar3_cart3(rho, (theta / 2), phi),
        f"θ ({np.round(theta, 2)}°)",
        c=color_theta,
        fontsize=12,
        horizontalalignment="left",
    )
    ax.text(
        *polar3_cart3(rho, 0, (phi / 2)),
        f"φ ({np.round(phi, 2)}°)",
        c=color_phi,
        fontsize=12,
        horizontalalignment="left",
    )

    fig.savefig(filename)
    return ax, fig


def test(
    x: float = 0.8,
    y: float = 0.6,
    z: float = 0.7,
    *,
    spin: bool = False,
    scan: bool = False,
):
    """Generate an image exemplifying the Coordinates System."""
    ax, fig = make_test(x, y, z)

    if spin or scan:
        # # ax.set_axis_off()
        try:
            with T.hidden_cursor():
                for angle in range(1, 361):
                    if scan:
                        ax, fig = make_test(
                            *polar3_cart3(1, angle / 2 - 90, angle - 1),
                            filename=f"img/gif/frame-{angle:0>3}.png",
                        )
                        pyplot.close(fig)

                    if spin:
                        ax.view_init(30, angle - 1)
                        fig.savefig(f"img/gif/frame-{angle:0>3}.png")

                    with T.location():
                        print(
                            f"Frame {angle:0>3}/360  {angle/360:>6.1%}  ",
                            end="",
                            flush=True,
                        )
                    # pyplot.draw()
                    # pyplot.pause(.1)
        except KeyboardInterrupt:
            exit(1)
        finally:
            print()


def render(
    data: np.ndarray,
    scale=1.5,
    size: float = 4,
    # size: float = 6,
    # size: float = 8,
    # size: float = 10,
    *,
    filename: str = None,
    make_frames: bool = False,
) -> None:
    print(f"Rendering {len(data)} stars...")
    fig = pyplot.figure(figsize=(size, size))

    ax = axes(fig, -scale, scale)
    ax.scatter(
        tuple(data[..., 0]), tuple(data[..., 1]), tuple(data[..., 2]), c="#000000", s=1
    )

    # pyplot.show()
    if filename:
        fig.savefig(filename)  # , bbox_inches='tight')

    if make_frames:
        ax.set_axis_off()
        with T.hidden_cursor():
            for angle in range(1, 361):
                ax.view_init(30, angle - 1)
                fig.savefig(f"gif/frame-{angle:0>3}.png")
                with T.location():
                    print(
                        f"Frame {angle:0>3}/1080  {angle/1080:>6.1%}  ",
                        end="",
                        flush=True,
                    )
                # pyplot.draw()
                # pyplot.pause(.1)
        print()

    pyplot.close(fig)
