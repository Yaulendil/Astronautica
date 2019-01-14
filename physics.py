from astropy import units#, constants
# import numpy as np

import geometry


def collide(*pair):
    # TODO: Finish this
    a, b = min(pair), max(pair)
    ratio_ab = a.mass / b.mass
    a.on_collide(b)
    b.on_collide(a)


def progress(time):
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
            distance = (end_a - end_b).length
            if distance < obj_a.radius + obj_b.radius:
                collisions.append((obj_a, obj_b))

    for obj in ObjectInSpace.idx:
        obj.coords.increment(time)

    for pair in collisions:
        collide(*pair)


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

    def on_collide(self, other):
        pass
