"""
This adds two nodes for a Hohmann transfer maneuver.

Currently assumes circular orbits, especially at the start!
Nodes can be execute manually or with Node Executor script running in parallel.
"""

import logging
from math import sqrt, pow
#  import time
import krpc


def set_up_logger(log_filename):
    """Set up the logger."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.ERROR)
    file_formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_formatter = logging.Formatter('%(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    return logger


def connect_to_krpc_server(client_name):
    """Connect to the krpc server."""
    conn = krpc.connect(name=client_name)
    return conn


MODULE_HANDLE = 'HohmannTransfer'

logger = set_up_logger(MODULE_HANDLE + '.log')
conn = connect_to_krpc_server(MODULE_HANDLE)


def check_initial_orbit(maximum_eccentricity=0.01):
    """Check how circular the current orbit is, and then wait for click."""
    vessel = conn.space_center.active_vessel
    if vessel.orbit.eccentricity > maximum_eccentricity:
        logger.info('Please circularize first!')
        return False
    return True


def Hohmann_phase_angle(a1, a2):
    """Calculate the phase angle change during a Hohmann maneuver."""
    return 180 - 90 * sqrt(pow((a1+a2)/a2, 3)/2)


def time_to_phase(phase_angle, period1, period2):
    """Calculate how long to wait for a particular phase angle change."""
    if period1 == period2:
        return float('nan')
    else:
        period = (period1*period2)/(period1-period2)
    if period == 0:
        if phase_angle == 0:
            return 0
        else:
            return float('nan')
    else:
        time = phase_angle / 360 * period
    while time < 0:
        time = time + abs(period)
    while time > abs(period):
        time = time - abs(period)
    return time


def time_to_longitude(target_longitude):
    """Calculate time to reach a certain longitude.

    Assumes a circular, equatorial orbit.
    """
    vessel = conn.space_center.active_vessel
    rf = vessel.orbit.body.reference_frame
    return time_to_phase(
        vessel.flight(rf).longitude - target_longitude,
        vessel.orbit.period,
        vessel.orbit.body.rotational_period)


def time_to_target_phase(target_phase):
    """Calculate time to reach a certain phase angle with the target.

    Assumes there is a target selected, and that it orbits the same body.
    """
    vessel = conn.space_center.active_vessel
    rf = vessel.orbit.body.reference_frame
    target = conn.space_center.target_vessel
    vessel_longitude = vessel.flight(rf).longitude
    target_longitude = target.flight(rf).longitude
    return time_to_phase(
        vessel_longitude - target_longitude - target_phase,
        vessel.orbit.period,
        target.orbit.period)


def Hohmann_nodes(target_altitude, start_time):
    """Set up a Hohmann Transfer's two maneuver nodes.

    Add two nodes to the current vessel's flight plan,
    to set up a Hohmann transfer for a given altitude,
    starting at a give future time, and assuming circular orbits.
    """
    vessel = conn.space_center.active_vessel
    mu = vessel.orbit.body.gravitational_parameter
    a1 = vessel.orbit.semi_major_axis
    a2 = target_altitude + vessel.orbit.body.equatorial_radius
    # setting up first maneuver
    dv1 = sqrt(mu/a1)*(sqrt(2*a2/(a1+a2))-1)
    node1 = vessel.control.add_node(start_time, prograde=dv1)
    # setting up second maneuver
    # measuring, rather than calculating
    if dv1 > 0:
        transfer_time = node1.orbit.time_to_apoapsis
    else:
        transfer_time = node1.orbit.time_to_periapsis
    dv2 = sqrt(mu/a2)*(1-sqrt(2*a1/(a1+a2)))
    vessel.control.add_node(start_time + transfer_time, prograde=dv2)
    logger.info('Hohmann transfer nodes added.')
    return


def Keostationary(longitude):
    """Set up a Hohmann transfer to Keostationary orbit.

    Currently hardcoded for Kerbin's syncronous orbit altitude.
    """
    vessel = conn.space_center.active_vessel
    a1 = vessel.orbit.semi_major_axis
    a2 = 2863330 + vessel.orbit.body.equatorial_radius
    target_longitude = longitude - Hohmann_phase_angle(a1, a2)
    logger.info('Keostationary transfer calculated.')
    Hohmann_nodes(
        2863330,
        conn.space_center.ut + time_to_longitude(target_longitude))
    return


def rendez_vous():
    """Set up a Hohmann maneuver, to rendez-vous with current target.

    Assumes there is a target selected, and that it orbits the same body.
    """
    vessel = conn.space_center.active_vessel
    target = conn.space_center.target_vessel
    a1 = vessel.orbit.semi_major_axis
    a2 = target.orbit.semi_major_axis
    time_to_transfer = time_to_target_phase(-Hohmann_phase_angle(a1, a2))
    logger.info('Rendez-vous transfer calculated.')
    Hohmann_nodes(
        target.orbit.apoapsis_altitude,
        conn.space_center.ut + time_to_transfer)
    return


# main loop
if __name__ == "__main__":

    logger.info('Running HohmannTransfer as __main__.')

    if check_initial_orbit():
        Keostationary(285.425)  # 285.425 is right over the KSC
        # rendez_vous()  # needs a target set first!

    logger.info('End of __main__.')
