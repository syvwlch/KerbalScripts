"""
Adds two nodes for a Hohmann transfer to rendez-vous with the current target.

Currently checks that the initial orbit is reasonably circular.
"""

from HohmannTransfer import HohmannTransfer

transfer = HohmannTransfer()

transfer.transfer_to_rendezvous()

print(transfer)

transfer.add_nodes()
