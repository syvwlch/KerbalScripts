"""
Adds two nodes for a Hohmann transfer to synchronous orbit around current body.

Currently checks that the initial orbit is reasonably circular.
"""

from HohmannTransfer import HohmannTransfer

KSC_LONGITUDE = 285.425
target_longitude = KSC_LONGITUDE

ht = HohmannTransfer()
ht.transfer_to_synchronous_orbit(target_longitude)

ht.add_nodes()
