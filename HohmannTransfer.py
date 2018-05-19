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


class HohmannTransfer:
    """
    General class for all Hohmann transfers.

    Will include methods for transfers to Keostationary orbits,
    orbital rendez-vous transfers, etc...
    """

    def __init__(self):
        """Set arguments directly."""
        self.initial_sma = 1
        self.target_sma = 1
        self.mu = 1
        self.time_to_start = 0

    @property
    def initial_dV(self):
        """Set deltaV for the initial maneuver of a Hohmann transfer."""
        try:
            term_1 = self.mu/self.initial_sma
            term_2 = 2*self.target_sma/(self.initial_sma+self.target_sma)
            return sqrt(term_1) * (sqrt(term_2)-1)
        except AttributeError:
            raise('Semi-major axes cannot be zero.')

    @property
    def final_dV(self):
        """Set deltaV for the final maneuver of a Hohmann transfer."""
        try:
            term_1 = self.mu/self.target_sma
            term_2 = 2*self.initial_sma/(self.initial_sma+self.target_sma)
            return sqrt(term_1) * (1-sqrt(term_2))
        except AttributeError:
            raise('Semi-major axes cannot be zero.')

    @property
    def transfer_time(self):
        """Transit time for a Hohmann transfer."""
        try:
            term_1 = pi/sqrt(8*self.mu)
            term_2 = pow(self.initial_sma+self.target_sma, 3/2)
            return term_1 * term_2
        except AttributeError:
            raise('Gravitational parameter cannot be zero.')

    @property
    def phase_change(self):
        """Phase angle change during a Hohmann maneuver."""
        try:
            transfer_sma = (self.initial_sma + self.target_sma)/2
            orbital_period_ratio = pow(transfer_sma/self.target_sma, 3/2)
        except AttributeError:
            raise('Semi-major axes cannot be zero.')
        initial_phase_relative_to_target_orbit = 180
        transfer_phase_change = 180 * orbital_period_ratio
        return initial_phase_relative_to_target_orbit - transfer_phase_change

    def set_to_altitude(self, vessel, altitude):
        """Set from a vessel and a target altitude."""
        try:
            self.mu = vessel.orbit.body.gravitational_parameter
            self.initial_sma = vessel.orbit.semi_major_axis
            radius = vessel.orbit.body.equatorial_radius
            self.target_sma = radius + altitude
        except AttributeError:
            raise('Could not get value from vessel.')

    def set_to_target(self, vessel, target):
        """Set from a vessel and a target."""
        try:
            self.mu = vessel.orbit.body.gravitational_parameter
            self.initial_sma = vessel.orbit.semi_major_axis
            self.target_sma = target.orbit.semi_major_axis
        except AttributeError:
            print('Could set to target.')

    def set_to_body(self, vessel, body):
        """Set for synchronous orbit around a body."""
        try:
            self.mu = body.gravitational_parameter
            self.initial_sma = vessel.orbit.semi_major_axis
            rotational_period = body.rotational_period
            self.target_sma = pow(self.mu*(rotational_period/(2*pi))**2, 1/3)
        except AttributeError:
            raise('Could not get value from body.')

    def add_nodes(self, vessel):
        """Add two maneuver nodes to vessel to set up transfer."""
        try:
            start_time = self.time_to_start
            stop_time = start_time + self.transfer_time
            vessel.control.add_node(start_time, prograde=self.initial_dV)
            vessel.control.add_node(stop_time, prograde=self.final_dV)
        except AttributeError:
            raise('Could not add nodes to vessel.')
