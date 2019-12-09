from itertools import starmap

# from sys import exit
from matplotlib.figure import Figure
from typing import Tuple

from blessings import Terminal
from matplotlib import use

use("GTK3Cairo")

from matplotlib import pyplot
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from vectormath import Vector3

from .space.geometry import from_spherical, to_spherical


T = Terminal()


def axes(
    fig: Figure,
    min_: float = -1,
    max_: float = 1,
    *,
    azim: float = 245,
    elev: float = 30,
) -> Axes3D:
    ax = Axes3D(fig, azim=azim, elev=elev)

    # ax.set_title("asdf")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    ax.set_xlim3d(min_, max_)
    ax.set_ylim3d(min_, max_)
    ax.set_zlim3d(-1, 1)

    return ax


point = lambda *points: ", ".join(map(str, np.round(points, 2)))


def plot_spherical(
    ax: Axes3D,
    x: float,
    y: float,
    z: float,
    *,
    arcs_primary: bool = False,
    label_primary: bool = False,
    arcs_secondary: bool = False,
    cartesian_trace: bool = False,
    angle_square: bool = False,
    mark_final: bool = True,
):
    rho, theta, phi = to_spherical(x, y, z)

    color_rho = "red"
    color_theta = "green"
    color_phi = "blue"
    grey = "#777777"
    seg = 15
    w = 0.1

    def mark(x_, y_, z_, label: str = None):
        ax.text(
            x_, y_, z_, (label or "  {}").format(point(x_, y_, z_)),
        )

    def plot(*points: Tuple[float, float, float], **kw):
        points = np.array(points)
        return ax.plot(points[..., 0], points[..., 1], points[..., 2], **kw)

    arc_theta = lambda d=1: starmap(
        from_spherical, ((rho * d, (theta / seg * i), phi) for i in range(seg + 1))
    )
    arc_phi = lambda d=1: starmap(
        from_spherical, ((rho * d, 0, (phi / seg * i)) for i in range(seg + 1))
    )

    # Y-axis Line.
    if arcs_primary:
        plot((0, rho, 0), (0, 0, 0), c=grey)
    elif arcs_secondary:
        plot((0, rho * 0.5, 0), (0, 0, 0), c=grey)

    # Coordinate Triangle.
    if cartesian_trace:
        plot(
            (x, y, z),  # Endpoint.
            (x, y, 0),  # Below Endpoint.
            (x, 0, 0),  # Endpoint on X-Axis.
            (0, 0, 0),  # Origin.
            c=grey,
        )

        # Right Angle.
        if angle_square:
            angle_off = min(abs(x * w), abs(y * w), abs(z * w))
            plot(
                (x, y, angle_off),
                (x, y - angle_off, angle_off),
                (x, y - angle_off, 0),
                c=grey,
            )

        # mark(x, 0, 0)  # Endpoint on X-Axis.
        # mark(x, y, 0)  # Below Endpoint.

    # SECONDARY Labels.
    if arcs_secondary:
        ax.text(0, rho * 0.52, 0, "ρ", c="black")
        ax.text(*from_spherical(rho * 0.52, (theta / 2), phi), "θ", c="black")
        ax.text(*from_spherical(rho * 0.52, 0, (phi / 2)), "φ", c="black")
        plot(*arc_theta(0.5), c=grey)  # GREY Theta Arc.
        plot(*arc_phi(0.5), c=grey)  # GREY Phi Arc.

    if arcs_primary:
        plot(*arc_theta(), c=color_theta)  # Theta Arc.
        plot(*arc_phi(), c=color_phi)  # Phi Arc.
        plot((0, 0, 0), (x, y, z), c=color_rho)
        plot(
            (0, 0, 0),  # Origin.
            Vector3(x, y, 0).normalize() * rho,  # Point where Theta=0.
            c=grey,
        )

    # PRIMARY Labels.
    if label_primary:
        ax.text(
            x,
            y,
            z,
            f"ρ ({np.round(rho, 2)})",
            c=color_rho,
            fontsize=12,
            horizontalalignment="right",
            verticalalignment="bottom",
        )
        ax.text(
            *from_spherical(rho, (theta / 2), phi),
            f"θ ({np.round(theta, 2)}°)",
            c=color_theta,
            fontsize=12,
            horizontalalignment="left",
            verticalalignment="bottom",
        )
        ax.text(
            *from_spherical(rho, 0, (phi / 2)),
            f"φ ({np.round(phi, 2)}°)",
            c=color_phi,
            fontsize=12,
            horizontalalignment="left",
            verticalalignment="bottom",
        )

    if mark_final:
        mark(x, y, z, f"{{}}\n{point(rho, theta, phi)}")  # Endpoint.


def render_test_image(
    x: float = 0.8,
    y: float = 0.6,
    z: float = 0.7,
    *,
    filename: str = "axes.png",
    # spin: bool = False,
    # scan: bool = False,
):
    """Generate an image exemplifying the Coordinates System."""
    fig: Figure = pyplot.figure(figsize=(8, 8))
    ax: Axes3D = axes(fig, azim=245, elev=30)

    plot_spherical(ax, x, y, z, arcs_primary=True, cartesian_trace=True)

    sc = np.array([getattr(ax, f"get_{d}lim")() for d in "xyz"])
    ax.auto_scale_xyz(*[[np.min(sc), np.max(sc)]] * 3)

    # ax.set_axis_off()
    fig.savefig(filename)
    return ax, fig

    # if spin or scan:
    #     # ax.set_axis_off()
    #     try:
    #         with T.hidden_cursor():
    #             final = 360
    #             for angle in range(1, final + 1):
    #                 if scan:
    #                     ax, fig = plot_spherical(
    #                         *from_spherical(1, angle / 2 - 90, angle - 1),
    #                         filename=f"img/gif/frame-{angle:0>3}.png",
    #                     )
    #                     pyplot.close(fig)
    #
    #                 if spin:
    #                     ax.view_init(30, angle - 1)
    #                     fig.savefig(f"img/gif/frame-{angle:0>3}.png")
    #
    #                 with T.location():
    #                     print(
    #                         f"Frame {angle:0>3}/{final}  {angle/final:>6.1%}  ",
    #                         end="",
    #                         flush=True,
    #                     )
    #                 # pyplot.draw()
    #                 # pyplot.pause(.1)
    #     except KeyboardInterrupt:
    #         exit(1)
    #     finally:
    #         print()


def render_galaxy(
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
