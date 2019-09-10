from engine import objects


class Slug(objects.Object):
    """A simple Tungsten slug. Fired at high velocities to rip through an enemy vessel."""

    def on_collide(self, other):
        d_v = other.coords.velocity - self.coords.velocity
        # Kinetic Energy = (mass * speed^2) / 2
        e_kinetic = self.mass * (d_v.length ** 2) / 2
        # TODO:
        # - Figure out how much of the energy should be transferred
        # - Combine that with projectile radius to calculate pressure and penetration
        # - Damage the other object, if applicable


class Missile(objects.Object):
    """An explosive device attached to a thruster and a guidance system. Very deadly."""

    visibility = 12
    # TODO: Make it explode
    # TODO: Make it accelerate
    # TODO: Make it aim towards a target


class Torpedo(objects.Object):
    """A powerful explosive attached to a thruster. Terribly dangerous, but hard to use."""

    visibility = 8
    # TODO: Make it explode
    # TODO: Make it accelerate


class Mine(objects.Object):
    """An enormous explosive device left adrift, in the hopes that an enemy will hit it."""

    visibility = 3
    # TODO: Make it explode
