"""
Adds two nodes for a Hohmann transfer to rendez-vous with the current target.

Currently checks that the initial orbit is reasonably circular.
"""

from HohmannTransfer import HohmannTransfer
from HohmannTransfer import time_to_phase
import InitialSetUp

#  Logger setup
MODULE_HANDLE = 'RendezVous'
logger = InitialSetUp.set_up_logger(MODULE_HANDLE + '.log')

#  KRPC server connection
try:
    conn = InitialSetUp.connect_to_krpc_server(MODULE_HANDLE)
except ConnectionRefusedError:
    logger.critical('Connection refused.')
    logger.critical('Please check that KRPC server is running in KSP.')
    conn = None

logger.info('Transfer to rendez-vous with target.')
vessel = conn.space_center.active_vessel
target = conn.space_center.target_vessel

ht = HohmannTransfer()
ht.set_to_target(vessel, target)

rf = vessel.orbit.body.reference_frame
vessel_phase = vessel.flight(rf).longitude
target_phase = target.flight(rf).longitude
current_phase = target_phase - vessel_phase
transfer_phase = ht.phase_change
time_to_transfer = time_to_phase(transfer_phase - current_phase,
                                 vessel.orbit.period,
                                 target.orbit.period,)

ht.time_to_start = conn.space_center.ut + time_to_transfer
ht.add_nodes(vessel)
