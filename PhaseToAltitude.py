"""
Adds two nodes for a Hohmann transfer to a given altitude.

Currently checks that the initial orbit is reasonably circular.
"""

from HohmannTransfer import HohmannTransfer

DELAY = 180  # in seconds
transfer = HohmannTransfer(delay=DELAY)

TARGET_ALTITUDE = 100*1000  # in meters
transfer.target_altitude = TARGET_ALTITUDE

print(transfer)

transfer.add_nodes()
