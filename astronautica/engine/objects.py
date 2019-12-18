"""Module implementing the Base Class for all Objects which reside in Space."""
from typing import Tuple, Set

from astropy import units as u
from attr import asdict, attrs
from numba import jit
import numpy as np
from vectormath import Vector3

from .serial import Node
from .space import Coordinates
from .units import Units, UNITS_LOCAL

# from pytimer import Timer

__all__ = ["Data", "Object"]


@attrs
class Data:
    mass: float = 100
    radius: float = 10
    units: Units = UNITS_LOCAL


class Object(Node):
    __slots__ = (
        "data",
        "frame",
    )

    ALL: Set["Object"] = set()

    def __init__(self, data: dict = None, frame: Coordinates = None):
        self.data = Data(**(data or {}))
        self.frame = frame

        self.ALL.add(self)

    @property
    def mass(self):
        return self.data.mass * self.data.units.mass

    @property
    def radius(self):
        return self.data.radius

    @property
    def momentum(self):
        """p = mv"""
        return self.mass.to_value(u.kg) * self.frame.velocity

    def impulse(self, impulse):
        """Momentum is Mass times Velocity, so the change in Velocity is the
            change in Momentum, or Impulse, divided by Mass.
        """
        self.add_velocity(impulse / self.mass.to_value(u.kg))

    def add_velocity(self, dv: np.ndarray):
        """Add an Array to the Velocity value of our Coordinates.

        Primarily meant to allow Object Subclasses to define special behavior
            on changes in Velocity, such as injury due to G-forces.
        """
        self.frame.velocity += dv

    def collide_with(self, other: "Object"):
        """Simulate an impact between two objects, resulting in altered paths.

        F = ma = m(Δv/Δt) = Δp/Δt

        Force is nothing more than a change in Momentum over Time, and this
            impact is happening over the course of one second, so Force is
            equivalent to Change in Momentum (Δp or Impulse).
        """
        # t = Timer()
        # Find the Normal Vector between the objects.
        normal: Vector3 = other.frame.position - self.frame.position
        normal /= normal.length

        # Determine the Δv the objects impart on each other.
        dv_a, dv_b = get_delta_v(
            0.6,  # Coefficient of Restitution is constant for now.
            normal,
            self.frame.velocity,
            other.frame.velocity,
            self.mass.to_value(u.kg),
            other.mass.to_value(u.kg),
        )
        # print("DeltaV:    ", t(), "sec")

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
        # print("Collisions:", t(), "sec")

    def on_collide(self, other: "Object"):
        """Impart any appropriate special effects on another Object.

        This Method is called AFTER effects of the impact on velocity have been
            calculated and applied.
        """
        pass

    def clone(self: "Object") -> "Object":
        c = type(self)(asdict(self.data), self.frame.clone())
        return c

    def unlink(self):
        if self in self.ALL:
            self.ALL.remove(self)
        self.frame.detach()

    def serialize(self):
        flat = {
            "type": type(self).__name__,
            "data": asdict(self.data),
            "subs": dict(frame=self.frame.serialize()),
        }
        return flat

    @classmethod
    def from_serial(cls, data, subs):
        return cls(data, subs["frame"])


@jit
def get_delta_v(
    e: float,
    normal: np.ndarray,
    velocity_a: np.ndarray,
    velocity_b: np.ndarray,
    mass_a: float,
    mass_b: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """Given a Coefficient, a Normal, and the Velocities and Masses of two
        Objects, return the Δv values of a collision between the Objects. The
        first and second returned Vectors should be added to the Velocities of
        the first and second Objects, respectively.

    This equation is not complete, as I have purposefully left out rotation, at
        least for the time being.

    https://www.euclideanspace.com/physics/dynamics/collision/threed/index.htm
        J = -(1+e) * (
            ((vai-vbi) • n)
            /
            (1/ma + 1/mb)
        )
        vaf = vai + (J / ma)
        vbf = vbi - (J / mb)
    """
    J: np.ndarray = normal * (
        -(1 + e)
        * (np.dot((velocity_a - velocity_b), normal) / ((1 / mass_a) + (1 / mass_b)))
    )
    return J / mass_a, -J / mass_b
