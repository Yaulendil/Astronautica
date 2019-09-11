from sys import exit
from typing import Tuple

import numpy as np
from numpy import random as npr


def apply_swirl(stars, factor: float = 0.1) -> None:
    ...


def generate_stars(count: int, sigma=(1, 1, 1)) -> np.ndarray:
    sig_x, sig_y, sig_z = sigma
    return np.array(
        [
            (npr.normal(scale=sig_x), npr.normal(scale=sig_y), npr.normal(scale=sig_z))
            for _ in range(count)
        ]
    )


def generate_galaxy(size: Tuple[float, float, float], stars: int) -> np.ndarray:
    # radius = sum(size) / len(size)
    radius = sum(sorted(size, reverse=True)[:2]) / 2
    size = np.array(size)
    return generate_stars(stars, size)


## v ## IGNORE THIS ## v ##
if __name__ == "__main__":
    from blessings import Terminal
    from matplotlib import use

    use("GTK3Cairo")

    from matplotlib import pyplot
    from mpl_toolkits.mplot3d import Axes3D

    T = Terminal()

    fig = pyplot.figure(figsize=(6.4, 4.8))
    ax = Axes3D(fig, azim=-45, elev=40)

    scale = 2
    ax.set_xlim3d(-scale, scale)  # , xmin=3, xmax=3)
    ax.set_ylim3d(-scale, scale)  # , ymin=3, ymax=3)
    ax.set_zlim3d(-scale, scale)  # , zmin=3, zmax=3)
    ax.set_axis_off()

    galaxy = generate_galaxy((1.4, 1, 0.2), 500)
    ax.scatter(galaxy[..., 0], galaxy[..., 1], galaxy[..., 2])

    # pyplot.show()
    fig.savefig("demo.png")  # , bbox_inches='tight')

    try:
        with T.hidden_cursor():
            for angle in range(1, 361):
                ax.view_init(30, angle - 1)
                fig.savefig(f"gif/frame-{angle:0>3}.png")
                with T.location():
                    print(
                        f"Frame {angle:0>3}/360  {angle/360:>2.1%}  ",
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
