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
        """Set target orbital period."""
        return self.period_from_sma(self.target_sma)

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
    def phase_change(self):
        """Phase change during the transfer."""
        orbital_period_ratio = self.transfer_period / self.target_period
        return 180 * (1 - orbital_period_ratio)

    def clamp_from_0_to_360(self, angle):
        """Clamp the value of an angle between zero and 360 degrees."""
        while angle < 0:
            angle += 360
        while angle > 360:
            angle -= 360
        return angle

    def time_to_phase(self, target_phase):
        """Calculate how long to wait for a particular phase change."""
        rf = self.vessel.orbit.body.reference_frame
        vessel_phase = self.vessel.flight(rf).longitude
        phase_angle = self.phase_change + vessel_phase - target_phase
        phase_angle = self.clamp_from_0_to_360(phase_angle)
        return phase_angle / 360 * self.relative_period

    def transfer_to_altitude(self, altitude, delay):
        """Set target_sma & time_to_start from altitude & delay."""
        radius = self.vessel.orbit.body.equatorial_radius
        self.target_sma = radius + altitude

        self.time_to_start = delay

    def transfer_to_rendezvous(self):
        """Set target_sma & time_to_start from current target vessel."""
        target = self.conn.space_center.target_vessel
        self.target_sma = target.orbit.semi_major_axis

        rf = self.vessel.orbit.body.reference_frame
        target_phase = target.flight(rf).longitude
        self.time_to_start = self.time_to_phase(target_phase)

    def transfer_to_synchronous_orbit(self, longitude):
        """Set target_sma & time_to_start for synchronous orbit."""
        rotational_period = self.vessel.orbit.body.rotational_period
        self.target_sma = self.sma_from_orbital_period(rotational_period)

        self.time_to_start = self.time_to_phase(longitude)

    def add_nodes(self):
        """Add two maneuver nodes to set up transfer."""
        start_time = self.conn.space_center.ut + self.time_to_start
        stop_time = start_time + self.transfer_time
        self.vessel.control.add_node(start_time, prograde=self.initial_dV)
        self.vessel.control.add_node(stop_time, prograde=self.final_dV)
