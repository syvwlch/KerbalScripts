"""
This class creates Hohmann transfer maneuver nodes.

Currently assumes circular orbits, especially at the start!
Nodes can be execute manually or with Node Executor script running in parallel.
"""

from math import pi, sqrt, pow
import krpc


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
    """Class to create Hohmann transfers."""

    def __init__(self):
        """Create a connection to krpc and initialize from acive vessel."""
        self.conn = krpc.connect(name=__name__)
        self.vessel = self.conn.space_center.active_vessel
        self.target_sma = self.vessel.orbit.semi_major_axis
        self.time_to_start = 0

    @property
    def initial_sma(self):
        """Set the initial semi-major axis from the active vessel."""
        return self.vessel.orbit.semi_major_axis

    @property
    def transfer_sma(self):
        """Set the semi-major axis of the transfer orbit."""
        return (self.initial_sma + self.target_sma)/2

    @property
    def mu(self):
        """Set the gravitational parameter from the active vessel's orbit."""
        return self.vessel.orbit.body.gravitational_parameter

    @property
    def initial_dV(self):
        """Set deltaV for the first maneuver of the transfer."""
        term_1 = self.mu/self.initial_sma
        term_2 = 2*self.target_sma/(self.initial_sma+self.target_sma)
        return sqrt(term_1) * (sqrt(term_2)-1)

    @property
    def final_dV(self):
        """Set deltaV for the second maneuver of the transfer."""
        term_1 = self.mu/self.target_sma
        term_2 = 2*self.initial_sma/(self.initial_sma+self.target_sma)
        return sqrt(term_1) * (1-sqrt(term_2))

    @property
    def transfer_time(self):
        """Transit time for the transfer."""
        term_1 = pi/sqrt(8*self.mu)
        term_2 = pow(self.initial_sma+self.target_sma, 3/2)
        return term_1 * term_2

    @property
    def phase_change(self):
        """Phase angle change during the transfer."""
        transfer_sma = (self.initial_sma + self.target_sma)/2
        orbital_period_ratio = pow(transfer_sma/self.target_sma, 3/2)
        initial_phase_relative_to_target_orbit = 180
        transfer_phase_change = 180 * orbital_period_ratio
        return initial_phase_relative_to_target_orbit - transfer_phase_change

    def period(self, semi_major_axis):
        """Calculate the orbital period from the semi-major axis."""
        return 2*pi*sqrt*(semi_major_axis**3/self.mu)

    @property
    def initial_period(self):
        """Set initial orbital period."""
        return self.period(self.initial_sma)

    @property
    def target_period(self):
        """Set target orbital period."""
        return self.period(self.target_sma)

    @property
    def transfer_period(self):
        """Set transfer orbital period."""
        return self.period(self.transfer_sma)

    def time_to_phase(self, phase_angle, period1, period2):
        """Calculate how long to wait for a particular phase change."""
        period = (period1*period2) / (period1-period2)
        result = phase_angle / 360 * period
        while result < 0:
            result = result + abs(period)
        while result > abs(period):
            result = result - abs(period)
        return result

    def phase_to_altitude(self, altitude, delay):
        """Set target_sma from the target altitude."""
        radius = self.vessel.orbit.body.equatorial_radius
        self.target_sma = radius + altitude
        self.time_to_start = delay

    def rendezvous_with_target(self):
        """Set from a vessel and a target."""
        target = self.conn.space_center.target_vessel
        self.target_sma = target.orbit.semi_major_axis
        rf = self.vessel.orbit.body.reference_frame
        vessel_phase = self.vessel.flight(rf).longitude
        target_phase = target.flight(rf).longitude
        phase_difference = target_phase - vessel_phase
        transfer_phase = self.phase_change - phase_difference
        print(transfer_phase)
        self.time_to_start = self.time_to_phase(transfer_phase,
                                                self.vessel.orbit.period,
                                                target.orbit.period,)

    def phase_to_synchronous_orbit(self, longitude):
        """Set for synchronous orbit around the orbiting body."""
        body = self.vessel.orbit.body
        rotational_period = body.rotational_period
        self.target_sma = pow(self.mu*(rotational_period/(2*pi))**2, 1/3)
        rf = body.reference_frame
        phase_difference = longitude - self.vessel.flight(rf).longitude
        transfer_phase = self.phase_change - phase_difference
        self.time_to_start = self.time_to_phase(transfer_phase,
                                                self.vessel.orbit.period,
                                                rotational_period,)

    def add_nodes(self):
        """Add two maneuver nodes to vessel to set up transfer."""
        start_time = self.conn.space_center.ut + self.time_to_start
        stop_time = start_time + self.transfer_time
        self.vessel.control.add_node(start_time, prograde=self.initial_dV)
        self.vessel.control.add_node(stop_time, prograde=self.final_dV)
