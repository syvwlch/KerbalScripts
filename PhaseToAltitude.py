"""
Adds two nodes for a Hohmann transfer to a given altitude.

Currently checks that the initial orbit is reasonably circular.
"""

from HohmannTransfer import HohmannTransfer
import InitialSetUp

TARGET_ALTITUDE = 100*1000
DELAY = 180

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

logger.info('Transfer to altitude of 100km.')
vessel = conn.space_center.active_vessel

ht = HohmannTransfer()
ht.set_to_altitude(vessel, TARGET_ALTITUDE)

ht.time_to_start = conn.space_center.ut + DELAY
ht.add_nodes(vessel)
