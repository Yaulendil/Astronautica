from numba import jit
import numpy as np

from . import geometry


class ObjectInSpace:
    visibility: int = 5

    def __init__(self, x=0, y=0, z=0, size=100, mass=100, *, domain=0, priv=False):
        self.radius = size  # Assume a spherical cow in a vacuum...
        self.mass = mass
        self.coords = geometry.Coordinates((x, y, z), domain=domain, priv=priv)

    @property
    def momentum(self):
        """p = mv"""
        return self.mass * self.coords.velocity

    def impulse(self, impulse):
        """
        Momentum is mass times velocity, so the change in velocity is
        the change in momentum, or impulse, divided by mass of object
        """
        d_velocity = impulse / self.mass
        self.coords.add_velocity(d_velocity)

    def collide(self, other: "ObjectInSpace"):
        """Simulate an impact between two objects, resulting in altered paths.

        F = ma = m(Δv/Δt) = Δp/Δt

        Force is nothing more than a change in Momentum over Time, and this
            impact is happening over the course of one second, so Force is
            equivalent to Change in Momentum (Δp or Impulse).

        These equations are not complete, as I have purposefully left out
            rotation, at least for the time being.

        http://www.euclideanspace.com/physics/dynamics/collision/threed/index.htm
        |J| = (e+1) * (vai - vbi) / (1/Ma +n•([Ia]^-1(n × ra)) x ra + 1/Mb +n•([Ib]^-1(n × rb)) × rb)
        """

        # Determine the impulse the objects impart on each other.
        coeff_restitution = 0.6  # e  # Constant for the moment.
        n = other.coords.position - self.coords.position
        vai = self.coords.velocity
        vbi = other.coords.velocity

        impulse = (-(1 + coeff_restitution) * np.dot((vai - vbi), n)) / (
            (1 / self.mass) + (1 / other.mass)
        )  # |J|
        impulse *= n  # J

        # Apply the impulses
        self.impulse(-impulse)
        other.impulse(impulse)
        # Now, the objects should have velocities such that on the next tick,
        #   they will not intersect. If for some reason they do still intersect,
        #   they will not interact again until they separate; This is obviously
        #   not realistic, but is less noticeable than the classic "stuttery
        #   glitching".

        # Run any special collision code the objects have; Projectile damage goes here
        self.on_collide(other)
        other.on_collide(self)

    def on_collide(self, other: "ObjectInSpace"):
        """Impart any appropriate special effects on another Object.

        This Method is called AFTER effects of the impact on velocity have been
            calculated and applied.
        """
        pass

    def clone(self) -> "ObjectInSpace":
        c = ObjectInSpace(size=self.radius, mass=self.mass, priv=True)
        c.coords = geometry.Coordinates(
            self.coords.position,
            self.coords.velocity,
            self.coords.heading,
            self.coords.rotate,
            priv=True,
        )
        return c

    def serialize(self):
        flat = {
            "class": str(type(self)),
            "radius": self.radius,
            "mass": self.mass,
            "coords": self.coords.serialize(),
        }
        return flat


def reconstruct(flat: dict, keep_scans=False):
    """
    Reconstruct an object of unknown type from serialized data
    This is NOT best practices...but for now it will do
    TODO: Make this not terrible
    """
    if keep_scans:
        # # Keep saved telemetry
        # for i in range(len(flat.get("scans", []))):
        #     # Construct a model of each scanned object
        #     flat["scans"][i] = reconstruct(flat["scans"][i])
        pass
    elif "scans" in flat:
        # Throw away any saved telemetry
        del flat["scans"]
    # Find the original class
    t = eval(flat.pop("class").split("'")[1])
    # Reconstruct the Coordinates object
    c = geometry.Coordinates(**flat.pop("coords"))
    # Instantiate a new object of the original type and overwrite all its data
    new = t()
    new.__dict__.update(flat)
    new.coords = c
    return new


class _Sim:
    """
    A simplified representation of two objects which can be rocked
    back and forth in time to closely examine their interactions.

    In this "sub-simulation", no acceleration takes place, and rotation is ignored.

    It is only meant to find exactly WHEN a collision takes place, so that
    the main simulation can pass the correct amount of time, and then fully
    simulate the collision on its own terms. It is a locator above all else.
    """

    def __init__(self, a: ObjectInSpace, b: ObjectInSpace, precision=4):
        self.a_real = a
        self.b_real = b
        self.a_virt = self.a_real.clone()
        self.b_virt = self.b_real.clone()
        self.contact = a.radius + b.radius
        self.precision = precision

    def reset(self):
        self.a_virt = self.a_real.clone()
        self.b_virt = self.b_real.clone()

    @jit
    def distance_at(self, time: float) -> float:
        a = self.a_virt.coords.pos_after(time)
        b = self.b_virt.coords.pos_after(time)

        return (a - b).length
