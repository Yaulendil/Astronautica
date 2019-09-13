from itertools import starmap
from typing import Tuple

from blessings import Terminal
from matplotlib import use

use("GTK3Cairo")

from matplotlib import pyplot
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

from .physics.geometry import cart3_polar3, polar3_cart3


T = Terminal()


def axes(
    fig,
    min_: float = -1.5,
    max_: float = 1.5,
    *,
    azim: float = 155,
    # azim: float = 200,
    elev: float = 30,
) -> Axes3D:
    ax = Axes3D(fig, azim=azim, elev=elev)  # , proj_type="ortho")

    # ax.set_title("asdf")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    ax.set_xlim3d(min_, max_)
    ax.set_ylim3d(max_, min_)
    ax.set_zlim3d(min_, max_)

    return ax


def test(x: float = 0.8, y: float = 0.6, z: float = 0.7):
    """Generate an image exemplifying the Coordinates System."""
    fig = pyplot.figure(figsize=(8, 8))
    ax = axes(fig, 0, 1)

    xyz = np.array((x, y, z))
    rho, theta, phi = cart3_polar3(x, y, z)

    color_rho = "red"
    color_theta = "green"
    color_phi = "blue"
    grey = "#777777"
    seg = 15
    w = 0.025

    def mark(x_, y_, z_):
        ax.text(x_, y_, z_, f"{(x_, y_, z_)!r}")

    def plot(*points: Tuple[float, float, float], **kw):
        points = np.array(points)
        return ax.plot(points[..., 0], points[..., 1], points[..., 2], **kw)

    # Axis Line.
    ax.plot((0, rho), (0, 0), (0, 0), c=grey)

    arc_theta = lambda d=1: starmap(
        polar3_cart3, ((rho * d, (theta / seg * i), phi) for i in range(seg + 1))
    )
    arc_phi = lambda d=1: starmap(
        polar3_cart3, ((rho * d, 0, (phi / seg * i)) for i in range(seg + 1))
    )

    # GREY Labels.
    ax.text(rho * 0.52, 0, 0, "ρ", c=grey)
    ax.text(*polar3_cart3(rho * 0.52, (theta / 2), phi), "θ", c=grey)
    ax.text(*polar3_cart3(rho * 0.52, 0, (phi / 2)), "φ", c=grey)

    plot(*arc_theta(0.5), c=grey)  # GREY Theta Arc.
    plot(*arc_phi(0.5), c=grey)  # GREY Phi Arc.
    plot(*arc_theta(), c=color_theta)  # Theta Arc.
    plot(*arc_phi(), c=color_phi)  # Phi Arc.

    # Right Angle.
    plot((x, y, 1.5 * w), (x - w, y - w, 1.5 * w), (x - w, y - w, 0), c="black")

    # Coordinate Triangle.
    plot((0, 0, 0), (x, y, z), (x, y, 0), (0, 0, 0), c=grey)
    plot((0, 0, 0), tuple(xyz), c=color_rho)

    mark(x, y, z)  # Endpoint.
    mark(x, y, 0)  # Below Endpoint.

    # COLORED Labels.
    ax.text(
        *xyz,
        f"ρ ({np.round(rho, 2)}°)",
        c=color_rho,
        fontsize=20,
        horizontalalignment="right",
        verticalalignment="bottom",
    )
    ax.text(
        *polar3_cart3(rho, (theta / 2), phi),
        f"θ ({np.round(theta, 2)}°)",
        c=color_theta,
        fontsize=20,
        horizontalalignment="left",
    )
    ax.text(
        *polar3_cart3(rho, 0, (phi / 2)),
        f"φ ({np.round(phi, 2)}°)",
        c=color_phi,
        fontsize=20,
        horizontalalignment="left",
    )

    fig.savefig("axes.png")


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
                        f"Frame {angle:0>3}/360  {angle/360:>6.1%}  ",
                        end="",
                        flush=True,
                    )
                # pyplot.draw()
                # pyplot.pause(.1)
        print()

    pyplot.close(fig)
