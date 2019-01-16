# from astropy import units  # , constants
# import numpy as np

import geometry


index = []


class ObjectInSpace:
    def __init__(self, x=0, y=0, z=0, size=100, mass=100):
        index.append(self)
        self.radius = size  # Assume a spherical cow in a vacuum...
        self.mass = mass
        self.coords = geometry.Coordinates([x, y, z])

    @property
    def momentum(self):
        """p = mv"""
        return self.mass * self.coords.velocity

    def impulse(self, impulse):
        """
        Momentum is mass times velocity, so the change in velocity is
        the change in momentum, or impulse, divided by the object mass
        """
        d_velocity = impulse / self.mass
        self.coords.velocity += d_velocity

    def on_collide(self, other):
        pass


def impact_force(self: ObjectInSpace, other: ObjectInSpace):
    """F = ma = m(Δv/Δt) = Δp/Δt
    Force is nothing more than a change in Momentum over Time, and this impact is happening
    over the course of one second, so Force is equivalent to Change in Momentum (Δp or Impulse)
    """
    relative_motion = other.coords.velocity - self.coords.velocity
    relative_momentum = other.momentum - self.momentum
    # Direction of imparted force
    direction = other.coords.position - self.coords.position
    return 0


def collide(a: ObjectInSpace, b: ObjectInSpace):
    """Simulate an impact between two objects, resulting in altered paths"""

    # Determine the impulses the objects impart on each other
    action, reaction = impact_force(a, b)

    # Apply the impulses
    a.impulse(action)
    b.impulse(reaction)
    # Now, the objects should have velocities such that on the next tick, they will not intersect.
    # If for some reason they do still intersect, they will not interact again until they separate;
    # This is obviously not realistic, but is less noticeable than the classic "stuttery glitching"

    # Run any special collision code the objects have; Projectile damage goes here
    a.on_collide(b)
    b.on_collide(a)


def tick(seconds=1, allow_collision=True):
    """Simulate the passing of one second"""
    list_a = index.copy()
    list_b = list_a.copy()
    collisions = []

    if allow_collision:
        for obj_a in list_a:
            list_b.pop(0)
            start_a, motion_a = obj_a.coords.movement(seconds)
            end_a = start_a + motion_a
            for obj_b in list_b:
                start_b, motion_b = obj_b.coords.movement(seconds)
                end_b = start_b + motion_b
                # TODO: Collision detection that doesnt suck
                if (
                    (end_a - end_b).length
                    < obj_a.radius + obj_b.radius
                    <= (start_a - start_b).length
                ):
                    # Objects intersect, and did not intersect a moment ago
                    collisions.append((obj_a, obj_b))

    for obj in index:
        obj.coords.increment(seconds)

    if allow_collision:
        for pair in collisions:
            collide(*pair)


def progress(time: int, granularity=1):
    """Simulate the passing of time"""
    if time == 0:
        return
    if time < 0:
        raise ValueError("Unfortunately the laws of thermodynamics prohibit time reversal.")
    elif granularity <= 0:
        raise ValueError("Progression granularity must be positive and nonzero")
    # TODO: Implement proper scaling for rotations in geometry.py before enabling granularity
    for i in range(time):
        tick(1, True)


def simulate(time):
    if time == 0:
        return
    tick(time, False)
