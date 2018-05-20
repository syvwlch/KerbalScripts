"""
Adds two nodes for a Hohmann transfer to synchronous orbit around current body.

Currently checks that the initial orbit is reasonably circular.
"""

from HohmannTransfer import HohmannTransfer

transfer = HohmannTransfer()

transfer.transfer_to_synchronous_orbit()

KSC_LONGITUDE = 285.425
transfer.target_phase = KSC_LONGITUDE

print(transfer)

transfer.add_nodes()
