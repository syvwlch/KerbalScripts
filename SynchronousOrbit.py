"""
Adds two nodes for a Hohmann transfer to synchronous orbit around current body.

Currently checks that the initial orbit is reasonably circular.
"""

from HohmannTransfer import HohmannTransfer
from HohmannTransfer import time_to_phase
import InitialSetUp

KSC_LONGITUDE = 285.425

target_longitude = KSC_LONGITUDE

#  Logger setup
MODULE_HANDLE = 'SynchronousOrbit'
logger = InitialSetUp.set_up_logger(MODULE_HANDLE + '.log')

#  KRPC server connection
try:
    conn = InitialSetUp.connect_to_krpc_server(MODULE_HANDLE)
except ConnectionRefusedError:
    logger.critical('Connection refused.')
    logger.critical('Please check that KRPC server is running in KSP.')
    conn = None

logger.info('Transfer to synchronous orbit around target.')
vessel = conn.space_center.active_vessel
body = vessel.orbit.body

ht = HohmannTransfer()
ht.set_to_body(vessel)

rotational_period = body.rotational_period
rf = body.reference_frame
current_phase = KSC_LONGITUDE - vessel.flight(rf).longitude
transfer_phase = ht.phase_change
time_to_transfer = time_to_phase(transfer_phase - current_phase,
                                 vessel.orbit.period,
                                 rotational_period,)

ht.time_to_start = conn.space_center.ut + time_to_transfer
ht.add_nodes(vessel)
