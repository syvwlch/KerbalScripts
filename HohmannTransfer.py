"""
This adds two nodes for a Hohmann transfer maneuver.

Currently assumes circular orbits, especially at the start!
Nodes can be execute manually or with Node Executor script running in parallel.
"""

from math import pi, sqrt, pow
import InitialSetUp

#  Logger setup
MODULE_HANDLE = 'HohmannTransfer'
logger = InitialSetUp.set_up_logger(MODULE_HANDLE + '.log')

#  KRPC server connection
try:
    conn = InitialSetUp.connect_to_krpc_server(MODULE_HANDLE)
except ConnectionRefusedError:
    logger.critical('Connection refused.')
    logger.critical('Please check that KRPC server is running in KSP.')
    conn = None

#  Constants that come in handy during Hohmann transfers.
KSC_LONGITUDE = 285.425
MAXIMUM_ECCENTRICITY = 0.01


def check_initial_orbit(conn,
                        maximum_eccentricity=MAXIMUM_ECCENTRICITY):
    """Check how circular the current orbit is."""
    eccentricity = conn.space_center.active_vessel.orbit.eccentricity
    if eccentricity > maximum_eccentricity:
        logger.info('Eccentricity too high for Hohmann transfers!')
        return False
    return True


def Hohmann_phase_angle(initial_sma, final_sma):
    """
    Calculate the phase angle change during a Hohmann maneuver.

    Takes the semi_major_axis of initial and final orbits,
    and returns the phase angle change during transfer.
    """
    # Transfer orbit by construction has half of both orbit's SMAs
    transfer_sma = (initial_sma+final_sma)/2
    # From formula for orbital period, ratio is 3/2 power of SMA ratio
    orbital_period_ratio = pow(transfer_sma/final_sma, 3/2)
    # Transfer starts 180 degrees from target
    initial_phase_angle = 180
    # Transfer happens within half a transfer orbit
    transfer_phase_angle = 180 * orbital_period_ratio
    return initial_phase_angle - transfer_phase_angle


def time_to_phase(phase_angle, period1, period2):
    """Calculate how long to wait for a particular phase angle change."""
    def clamp_time_to_period(phase_angle, period):
        """Clamp a phase angle to the interval between zero and abs(period)."""
        result = phase_angle / 360 * period
        while result < 0:
            result = result + abs(period)
        while result > abs(period):
            result = result - abs(period)
        return result

    def relative_period(period1, period2):
        """Calculate the relative period between two periods."""
        if period1 == period2:
            raise ValueError(
                'There is no relative periods when periods are identical!')
        elif period1 == 0:
            period = period2
        elif period2 == 0:
            period = period1
        else:
            period = (period1*period2)/(period1-period2)
        return period

    return clamp_time_to_period(
        phase_angle,
        relative_period(period1, period2))


def hohmann_nodes(conn, target_altitude, start_time):
    """
    Set up a Hohmann Transfer's two maneuver nodes.

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


def keostationary_transfer(conn, longitude=0):
    """
    Set up a Hohmann transfer to Keostationary orbit.

    Defaults to longitude zero.
    """
    def sma_from_orbital_period(mu, period):
        """Calculate the semi_major_axis, given Mu and the orbital period."""
        return pow(mu*(period/(2*pi))**2, 1/3)

    def time_to_longitude(target_longitude):
        """
        Calculate time to reach a longitude.

        Assumes a circular, equatorial orbit.
        """
        vessel = conn.space_center.active_vessel
        rf = vessel.orbit.body.reference_frame
        return time_to_phase(
            vessel.flight(rf).longitude - target_longitude,
            vessel.orbit.period,
            vessel.orbit.body.rotational_period)

    vessel = conn.space_center.active_vessel
    mu = vessel.orbit.body.gravitational_parameter
    rotational_period = vessel.orbit.body.rotational_period
    a1 = vessel.orbit.semi_major_axis
    a2 = sma_from_orbital_period(mu, rotational_period)
    target_longitude = longitude - Hohmann_phase_angle(a1, a2)
    logger.info('Keostationary transfer calculated.')
    hohmann_nodes(
        conn,
        a2 - vessel.orbit.body.equatorial_radius,
        conn.space_center.ut + time_to_longitude(target_longitude))
    return


def rendez_vous_transfer(conn):
    """
    Set up a Hohmann maneuver, to rendez-vous with current target.

    Assumes there is a target selected, and that it orbits the same body.
    """
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

    vessel = conn.space_center.active_vessel
    target = conn.space_center.target_vessel
    if target is None:
        raise ValueError('Tried to rendez-vous with no target set!')
    a1 = vessel.orbit.semi_major_axis
    a2 = target.orbit.semi_major_axis
    time_to_transfer = time_to_target_phase(-Hohmann_phase_angle(a1, a2))
    logger.info('Rendez-vous transfer calculated.')
    hohmann_nodes(
        conn,
        target.orbit.apoapsis_altitude,
        conn.space_center.ut + time_to_transfer)
    return


#  If running as __main__ then rdv if there is a target,
#  or go to Keostationary if not.
if __name__ == "__main__":
    logger.info('Running HohmannTransfer as __main__.')
    if check_initial_orbit(conn):
        if conn.space_center.target_vessel is None:
            keostationary_transfer(conn, KSC_LONGITUDE)
        else:
            rendez_vous_transfer(conn)
    logger.info('End of __main__.')
