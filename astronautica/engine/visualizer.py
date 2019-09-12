from blessings import Terminal
from matplotlib import use

use("GTK3Cairo")

from matplotlib import pyplot
from mpl_toolkits.mplot3d import Axes3D
import numpy as np


T = Terminal()


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

    ax = Axes3D(fig, azim=-45, elev=30)

    # ax.set_title("asdf")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    ax.set_xlim3d(-scale, scale)  # , xmin=3, xmax=3)
    ax.set_ylim3d(scale, -scale)  # , ymin=3, ymax=3)
    ax.set_zlim3d(-scale, scale)  # , zmin=3, zmax=3)

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
