"""Rotation Module: Dedicated to angles and orientations in three-dimensional
    Space.
"""

from quaternion.numpy_quaternion import quaternion

from .geometry import break_rotor, get_rotor, Quat


class Rotation(object):
    def __init__(self, aim: Quat = (1, 0, 0, 0), rot: Quat = (1, 0, 0, 0)):
        self.heading = (
            aim if isinstance(aim, quaternion) else quaternion(*aim)
        )  # Orientation.
        self.rotate = (
            rot if isinstance(rot, quaternion) else quaternion(*rot)
        )  # Spin per second.

    def serialize(self):
        flat = {
            "type": type(self).__name__,
            "data": {
                "hdg": [self.heading.w, *self.heading.vec],
                "rot": [self.rotate.w, *self.rotate.vec],
            },
        }
        return flat

    def increment(self, seconds: float):
        theta, vec = break_rotor(self.rotate)
        theta *= seconds
        rotate = get_rotor(theta, vec)
        self.heading = rotate * self.heading
