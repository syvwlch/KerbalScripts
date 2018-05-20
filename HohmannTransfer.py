"""
This class creates Hohmann transfer maneuver nodes.

Currently assumes circular orbits, especially at the start!
Nodes can be execute manually or with Node Executor script running in parallel.
"""

from math import pi, sqrt, pow
import krpc


class HohmannTransfer:
    """Class to create Hohmann transfers."""

    def __init__(self):
        """Create a connection to krpc and initialize from active vessel."""
        self.conn = krpc.connect(name=__name__)
        self.vessel = self.conn.space_center.active_vessel
        self.target_sma = self.vessel.orbit.semi_major_axis
        self.delay = 0

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
    def target_altitude(self):
        """Set the target altitude."""
        body_radius = self.vessel.orbit.body.equatorial_radius
        return self.target_sma - body_radius

    @target_altitude.setter
    def target_altitude(self, target_altitude):
        """Setter for target_altitude."""
        body_radius = self.vessel.orbit.body.equatorial_radius
        self.target_sma = body_radius + target_altitude

    @property
    def initial_dV(self):
        """Set deltaV for the first maneuver of the transfer."""
        term_1 = self.mu/self.initial_sma
        term_2 = self.target_sma/self.transfer_sma
        return sqrt(term_1) * (sqrt(term_2)-1)

    @property
    def final_dV(self):
        """Set deltaV for the second maneuver of the transfer."""
        term_1 = self.mu/self.target_sma
        term_2 = self.initial_sma/self.transfer_sma
        return sqrt(term_1) * (1-sqrt(term_2))

    @property
    def transfer_time(self):
        """Transit time for the transfer."""
        term_1 = pi/sqrt(self.mu)
        term_2 = pow(self.transfer_sma, 3/2)
        return term_1 * term_2

    def period_from_sma(self, semi_major_axis):
        """Calculate the orbital period from the semi-major axis."""
        return 2*pi*sqrt(semi_major_axis**3/self.mu)

    def sma_from_orbital_period(self, orbital_period):
        """Calculate the semi-major axis fom the orbital period."""
        return pow(self.mu*(orbital_period/(2*pi))**2, 1/3)

    @property
    def initial_period(self):
        """Set initial orbital period."""
        return self.period_from_sma(self.initial_sma)

    @property
    def target_period(self):
        """Set target orbital period from target sma."""
        return self.period_from_sma(self.target_sma)

    @target_period.setter
    def target_period(self, target_period):
        """Set target sma from target orbital period."""
        self.target_sma = self.sma_from_orbital_period(target_period)

    @property
    def transfer_period(self):
        """Set transfer orbital period."""
        return self.period_from_sma(self.transfer_sma)

    @property
    def relative_period(self):
        """Set relative orbital period."""
        period1 = self.initial_period
        period2 = self.target_period
        period = (period1*period2) / (period1-period2)
        return period

    @property
    def initial_phase(self):
        """Set the initial phase from the active vessel."""
        rf = self.vessel.orbit.body.reference_frame
        return self.vessel.flight(rf).longitude

    def clamp_from_0_360(self, angle):
        """Clamp the value of an angle between zero and 360 degrees."""
        while angle < 0:
            angle += 360
        while angle > 360:
            angle -= 360
        return angle

    @property
    def phase_change(self):
        """Phase change during the transfer."""
        orbital_period_ratio = self.transfer_period / self.target_period
        phase_change = 180 * (1 - orbital_period_ratio)
        return self.clamp_from_0_360(phase_change)

    @property
    def target_phase(self):
        """Set the target phase from delay."""
        return self.delay + self.phase_change

    @target_phase.setter
    def target_phase(self, target_phase):
        """Set delay from the target phase."""
        initial_phase_difference = target_phase - self.initial_phase
        final_phase_difference = self.phase_change - initial_phase_difference
        final_phase_difference = self.clamp_from_0_360(final_phase_difference)
        self.delay = final_phase_difference / 360 * self.relative_period

    def transfer_to_rendezvous(self):
        """Set up to rendez-vous with current target vessel."""
        target = self.conn.space_center.target_vessel
        self.target_sma = target.orbit.semi_major_axis

        rf = target.orbit.body.reference_frame
        self.target_phase = target.flight(rf).longitude

    def transfer_to_synchronous_orbit(self, longitude):
        """Set up for synchronous orbit."""
        rotational_period = self.vessel.orbit.body.rotational_period
        self.target_period = rotational_period
        self.target_phase = longitude

    def add_nodes(self):
        """Add two maneuver nodes to set up transfer."""
        start_time = self.conn.space_center.ut + self.delay
        stop_time = start_time + self.transfer_time
        self.vessel.control.add_node(start_time, prograde=self.initial_dV)
        self.vessel.control.add_node(stop_time, prograde=self.final_dV)
