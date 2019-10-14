"""Rotation Module: Dedicated to angles and orientations in three-dimensional
    Space.
"""

from quaternion.numpy_quaternion import quaternion


class Rotation(object):
    def __init__(self, aim: quaternion, rot: quaternion):
        # Orientation.
        self.heading = aim
        # Spin per second.
        self.rotate = rot

    def serialize(self):
        flat = {
            "type": type(self).__name__,
            "data": {
                "hdg": [self.heading.w, *self.heading.vec],
                "rot": [self.rotate.w, *self.rotate.vec],
            },
        }
        return flat
