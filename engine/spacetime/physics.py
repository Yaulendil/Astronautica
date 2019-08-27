import attr
import numpy as np
from vectormath import Vector3

from .collision import get_delta_v
from .geometry import Coordinates, Space


class ObjectInSpace:
    visibility: int = 5

    def __init__(
        self, x=0, y=0, z=0, size=100, mass=100, *, domain=0, space: Space
    ):
        self.radius = size  # Assume a spherical cow in a vacuum...
        self.mass = mass
        self.coords = Coordinates((x, y, z), domain=domain, space=space)

    @property
    def momentum(self):
        """p = mv"""
        return self.mass * self.coords.velocity

    def impulse(self, impulse):
        """Momentum is Mass times Velocity, so the change in Velocity is the
            change in Momentum, or Impulse, divided by Mass.
        """
        self.add_velocity(impulse / self.mass)

    def add_velocity(self, dv: np.ndarray):
        """Add an Array to the Velocity value of our Coordinates.

        Primarily meant to allow Object Subclasses to define special behavior
            on changes in Velocity, such as injury due to G-forces.
        """
        self.coords.velocity += dv

    def collide_with(self, other: "ObjectInSpace"):
        """Simulate an impact between two objects, resulting in altered paths.

        F = ma = m(Δv/Δt) = Δp/Δt

        Force is nothing more than a change in Momentum over Time, and this
            impact is happening over the course of one second, so Force is
            equivalent to Change in Momentum (Δp or Impulse).
        """
        # Find the Normal Vector between the objects.
        normal: Vector3 = other.coords.position - self.coords.position
        normal /= normal.length

        # Determine the Δv the objects impart on each other.
        dv_a, dv_b = get_delta_v(
            0.6,  # Coefficient of Restitution is constant for now.
            normal,
            self.coords.velocity,
            other.coords.velocity,
            self.mass,
            other.mass,
        )

        # Apply the Δv.
        self.add_velocity(dv_a)
        other.add_velocity(dv_b)
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

    def clone(self, space) -> "ObjectInSpace":
        c = ObjectInSpace(size=self.radius, mass=self.mass, space=space)
        c.coords = Coordinates(
            self.coords.position,
            self.coords.velocity,
            self.coords.heading,
            self.coords.rotate,
            space=space,
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
    c = Coordinates(**flat.pop("coords"))
    # Instantiate a new object of the original type and overwrite all its data
    new = t()
    new.__dict__.update(flat)
    new.coords = c
    return new
