# from astropy import units  # , constants
# import numpy as np

import geometry


class ObjectInSpace:
    idx = []

    def __init__(self, x=0, y=0, z=0, size=100, mass=100):
        self.idx.append(self)
        self.radius = size  # Assume a spherical cow in a vacuum...
        self.mass = mass
        self.coords = geometry.Coordinates([x, y, z])

    @property
    def momentum(self):
        # p=mv
        return self.mass * self.coords.velocity

    def impulse(self, force):
        pass

    def on_collide(self, other):
        pass


def impact_force(self: ObjectInSpace, other: ObjectInSpace):
    relative_motion = other.coords.velocity - self.coords.velocity
    relative_momentum = other.momentum - self.momentum
    # Direction of imparted force
    direction = other.coords.position - self.coords.position
    # TODO: Get the component of relative_momentum which is the same direction as 'direction'
    # TODO: Then turn it into an impulse vector (if theres any difference) and return that
    return 0


def collide(a, b):
    # TODO: Finish this
    # Determine the impulses the objects impart on each other
    a_tx_b = impact_force(b, a)
    b_tx_a = impact_force(a, b)

    # Apply the impulses
    a.impulse(b_tx_a)
    b.impulse(a_tx_b)
    # Now, the objects should have velocities such that on the next tick, they will not intersect
    # If for some reason they do still intersect, they will not collide again until they separate
    # This is obviously not realistic, but is less noticeable than the classic "glitchy stutters"

    # Run any special collision code the objects have; Projectile damage goes here
    a.on_collide(b)
    b.on_collide(a)


def progress(time: int):
    list_a = ObjectInSpace.idx.copy()
    list_b = list_a.copy()
    collisions = []

    for obj_a in list_a:
        list_b.pop(0)
        start_a, motion_a = obj_a.coords.movement(time)
        end_a = start_a + motion_a
        for obj_b in list_b:
            start_b, motion_b = obj_b.coords.movement(time)
            end_b = start_b + motion_b
            # TODO: Collision detection that doesnt suck
            if (
                (end_a - end_b).length
                < obj_a.radius + obj_b.radius
                <= (start_a - start_b).length
            ):
                # Objects intersect, and did not intersect a moment ago
                collisions.append((obj_a, obj_b))

    for obj in ObjectInSpace.idx:
        obj.coords.increment(time)

    for pair in collisions:
        collide(*pair)
