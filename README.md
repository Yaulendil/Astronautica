[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)


# Astronautica
"Real-time" PVP space combat game, played via SSH, currently primarily in the **planning** phase.

In actuality, it will be turn-based, but with turns at strict intervals in real time. Missing a turn is not necessarily a problem as most turns will not require action.

A Host instance must run separately from the Client instances that connect to the Host. The Host will manage the game world and control turns ticking over, as well as AI crewmembers.

Client instances will connect to the Host of a game session, and give directions to their vessel. The directions will be added to a List, and executed in order at the next game tick.

### Coordinates

From [Wikipedia](https://en.wikipedia.org/wiki/Spherical_coordinate_system#Conventions) (slightly clipped):

coordinates|corresponding local geographical directions (Z, X, Y)|right/left-handed
---:|:---:|---
(*r*, *θ* elevation, *φ* azimuth,right)|(U, N, E)|left
| |`Note: easting (E), northing (N), upwardness (U). Local azimuth angle would be measured, e.g., counterclockwise from S to E in the case of (U, S, E).`

This pre-existing coordinate system has been chosen because:
1. An angle where *φ*=0 is straight ahead
2. Positive values of *φ* increase clockwise
3. An angle where *θ*=0 is on a flat plane
4. UNE could be the United Nations of Earth

Coordinates are stored in numpy arrays.