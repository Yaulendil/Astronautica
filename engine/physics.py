# from astropy import units  # , constants
# import numpy as np

from engine import geometry
from engine.linemath import distance_between_lines


index = []


def avg(*numbers):
    return sum(numbers) / len(numbers)


class ObjectInSpace:
    visibility = 5

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
        self.coords.add_velocity(d_velocity)

    def on_collide(self, other):
        pass

    def clone(self):
        c = ObjectInSpace(size=self.radius, mass=self.mass)
        c.coords = geometry.Coordinates(
            self.coords.position,
            self.coords.velocity,
            self.coords.heading,
            self.coords.rotate,
        )
        return c


class Sim:
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

    def distance_at(self, time: float) -> float:
        a_future = sum(self.a_virt.coords.movement(time))
        b_future = sum(self.b_virt.coords.movement(time))
        return (a_future - b_future).length

    def find_collision(self, end: float, start=0.0):
        """
        Iteratively zero in on the first time where the distance between the
        objects is less than the sum of their radii

        Returns a float of seconds at which the objects collide, or False if they do not
        """

        t0 = start  # Time 0, minimum time
        d0 = self.distance_at(t0)
        t1 = end  # Time 1, maximum time
        d1 = self.distance_at(t1)
        result = False

        # TODO: Automatically select precision such that uncertainty < object radius
        for i in range(self.precision):
            # Repeat the following over a steadily more precise window of time
            tm = avg(t0, t1)  # Time M, middle time
            dm = self.distance_at(tm)
            if d0 < self.contact:
                # The objects are in contact at the start of this window
                result = False
                break
            elif dm < self.contact:
                # The objects are in contact halfway through this window
                result = tm
                t1 = tm
                d1 = dm
            elif d1 < self.contact:
                # The objects are in contact at the end of this window
                result = t1
                t0 = tm
                d0 = dm
            else:
                # The objects are not in contact at any known point;
                # However, they may still pass through each other between points
                if d0 < dm < d1 or d0 > dm < d1:
                    # The objects seem to be diverging, but may have passed
                    half_0 = dm - d0  # Change in distance over the first half
                    half_1 = d1 - dm  # Change in distance over the second half
                    if half_0 == half_1:
                        # Divergence is constant; Objects do not pass
                        result = False
                        break
                    elif half_0 > half_1:
                        # First half is greater change than second half;
                        # If they pass, it happens in the second half
                        t0 = tm
                        d0 = dm
                    else:  # half_0 < half_1
                        # First half is smaller change than second half;
                        # If they pass, it happens in the first half
                        t1 = tm
                        d1 = dm
                # elif d0 > dm < d1:
                    # The objects pass each other during this window
                else:
                    # No other condition could result in an impact
                    return False
        return result


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


def increment(seconds):
    """TODO:
    Rather than iterating through a list of all objects, store the position and
        velocity of all objects in a numpy ndarray or Vector3Array; Then, to
        increment time, simply scale the array of velocities and add it to the
        array of positions.
    """
    for obj in index:
        obj.coords.increment(seconds)


def tick(seconds=1.0, allow_collision=True):
    """Simulate the passing of one second"""
    list_a = index.copy()
    list_b = list_a.copy()
    collisions = []

    if allow_collision:
        for obj_a in list_a:
            list_b.pop(0)
            start_a = obj_a.coords.position
            end_a = sum(obj_a.coords.movement(seconds))
            for obj_b in list_b:
                start_b = obj_b.coords.position
                end_b = sum(obj_b.coords.movement(seconds))
                proximity = distance_between_lines(start_a, end_a, start_b, end_b)
                if proximity < (obj_a.radius + obj_b.radius).length:
                    # Objects look like they might collide
                    with Sim(obj_a, obj_b) as subsim:
                        impact = subsim.find_collision(seconds)
                        if impact is not False:
                            collisions.append([impact, (obj_a, obj_b)])

    # Each entry in collisions is a list: [float, (object, object)]
    # TODO: Sort collisions list by the float

    total = 0
    for impact in collisions:
        # Convert absolute times to relative time differences
        impact[0] -= total
        total += impact[0]
    after = seconds - total

    for impact in collisions:
        # Simulate to the time of each collision, and then run the math
        increment(impact[0])
        collide(*impact[1])
    # Then, simulate the rest of the time
    increment(after)


def progress(time: int, granularity=1):
    """Simulate the passing of time"""
    if time == 0:
        return
    if time < 0:
        raise ValueError(
            "Unfortunately the laws of thermodynamics prohibit time reversal."
        )
    elif granularity <= 0:
        raise ValueError("Progression granularity must be positive and nonzero")
    for i in range(time * granularity):
        tick(1 / granularity, True)


def simulate(time):
    if time == 0:
        return
    tick(time, False)
