"""
Adds two nodes for a Hohmann transfer to rendez-vous with the current target.

Currently checks that the initial orbit is reasonably circular.
"""

from HohmannTransfer import HohmannTransfer

ht = HohmannTransfer()
ht.rendezvous_with_target()
ht.add_nodes()
