[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)


# Astronautica
"Real-time" PVP space combat game, played via SSH, currently primarily in the **structure** phase.

In actuality, it will be turn-based, but with turns at strict intervals in real time. Missing a turn is not necessarily a problem as most turns will not require action.

A Host instance must run separately from the Client instances that connect to the Host. The Host will manage the game world and control turns ticking over, as well as AI crewmembers.

Client instances will connect to the Host of a game session, and give directions to their vessel. The directions will be added to a List, and executed in order at the next game tick.

### Coordinates

Any entity in space has a local frame of reference, an object of the "Coordinates" class which contains:
- **Physical location**, as a Vector3 measured from the Origin of the universal frame of reference
- **Velocity**, as a Vector3 measuring the change in Position over one second
- **Heading**, as a [Quaternion](https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation) representing current angular orientation relative to the universal frame of reference
- **Rotation**, as a Quaternion representing the angular velocity, measuring the change in Heading over one second

A frame of reference can be measured from the perspective of another. This returns a **new** Coordinates object representing the properties the entity would have, if the "viewing" frame of reference were the one defining the coordinates.
