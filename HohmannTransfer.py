"""
This adds two nodes for a Hohmann transfer maneuver.

Currently assumes circular orbits, especially at the start!
Nodes can be execute manually or with Node Executor script running in parallel.
"""

from math import sqrt, pow
import InitialSetUp

MODULE_HANDLE = 'HohmannTransfer'
KSC_LONGITUDE = 285.425
KERBIN_SYNCHRONOUS_ALTITUDE = 2863330
MAXIMUM_ECCENTRICITY = 0.01

logger = InitialSetUp.set_up_logger(MODULE_HANDLE + '.log')
conn = InitialSetUp.connect_to_krpc_server(MODULE_HANDLE)


def check_initial_orbit(maximum_eccentricity=MAXIMUM_ECCENTRICITY):
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


def hohmann_nodes(target_altitude, start_time):
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


def keostationary_transfer(longitude=KSC_LONGITUDE,
                           synchronous_altitude=KERBIN_SYNCHRONOUS_ALTITUDE):
    """Set up a Hohmann transfer to Keostationary orbit.

    Takes altitude of synchronous orbit as a parameter, does not calculate it.
    Defaults to the KSC's longitude.
    """
    vessel = conn.space_center.active_vessel
    a1 = vessel.orbit.semi_major_axis
    a2 = synchronous_altitude + vessel.orbit.body.equatorial_radius
    target_longitude = longitude - Hohmann_phase_angle(a1, a2)
    logger.info('Keostationary transfer calculated.')
    hohmann_nodes(
        synchronous_altitude,
        conn.space_center.ut + time_to_longitude(target_longitude))
    return


def rendez_vous_transfer():
    """Set up a Hohmann maneuver, to rendez-vous with current target.

    Assumes there is a target selected, and that it orbits the same body.
    """
    vessel = conn.space_center.active_vessel
    target = conn.space_center.target_vessel
    a1 = vessel.orbit.semi_major_axis
    a2 = target.orbit.semi_major_axis
    time_to_transfer = time_to_target_phase(-Hohmann_phase_angle(a1, a2))
    logger.info('Rendez-vous transfer calculated.')
    hohmann_nodes(
        target.orbit.apoapsis_altitude,
        conn.space_center.ut + time_to_transfer)
    return


# main loop
if __name__ == "__main__":

    logger.info('Running HohmannTransfer as __main__.')

    if check_initial_orbit():
        if conn.space_center.target_vessel is None:
            keostationary_transfer()
        else:
            rendez_vous_transfer()

    logger.info('End of __main__.')
