"""
Adds two nodes for a Hohmann transfer to a given altitude.

Currently checks that the initial orbit is reasonably circular.
"""

from HohmannTransfer import HohmannTransfer

DELAY = 180
TARGET_ALTITUDE = 100*1000

ht = HohmannTransfer()
ht.target_altitude = TARGET_ALTITUDE
ht.delay = DELAY
ht.add_nodes()
