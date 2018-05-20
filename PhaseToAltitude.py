"""
Adds two nodes for a Hohmann transfer to a given altitude.

Currently checks that the initial orbit is reasonably circular.
"""

from HohmannTransfer import HohmannTransfer

transfer = HohmannTransfer()

TARGET_ALTITUDE = 100*1000  # in meters
transfer.target_altitude = TARGET_ALTITUDE

DELAY = 180  # in seconds
transfer.delay = DELAY

print(transfer)

transfer.add_nodes()
