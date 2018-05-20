"""
This module contains the HohmannTransfer class.

Currently assumes circular orbits, especially at the start!
Nodes can be execute manually or with Node Executor script running in parallel.
"""

from math import pi, sqrt, pow
import krpc


class HohmannTransfer:
    """
    Create Hohmann transfers which can be executed in KSP.

    A Hohmann transfer consists of two impulsive orbital maneuvers to move
    a vessel from one circular orbit around a body to another circular orbit
    around the same body, at a different altitude via an elliptical transfer
    orbit.

    When you create an instance with no arguments, it starts out being
    the null transfer, which does not change your orbit:
        from HohmannTransfer import HohmannTransfer
        transfer = HohmannTransfer()

    You can set the target altitude and the delay before the first burn:
        transfer.target_altitude = 100*1000  # in meters
        transfer.delay = 180  # in seconds

    The transfer will provide the deltaV of both burns, as well as
    the time spent between the two burns:
        print(transfer)

    You can then add maneuver nodes to the active vessel for both burns:
        transfer.add_nodes()

    You can also specify the target semi-major axis and/or the delay during
    instance creation, like so:
        transfer = HohmannTransfer(target_sma=TARGET_SMA, delay=DELAY)

    The following attributes are read/write:
        - target_sma
        - delay
        - target_altitude
        - target_period
        - target_phase

    The following attributes are read-only:
        - initial_sma
        - transfer_sma
        - mu
        - initial_altitude
        - initial_dV
        - final_dV
        - initial_period
        - transfer_period
        - relative_period
        - initial_phase
        - phase_change

    The following methods can be used as shortcuts for common use cases:
        - transfer_to_synchronous_orbit()
        - transfer_to_rendezvous()

    See the relevant docstrings for details.
    """

    def __init__(self, target_sma=0, delay=0):
        """Create a connection to krpc and initialize from active vessel."""
        self.conn = krpc.connect(name=__name__)
        self.vessel = self.conn.space_center.active_vessel
        if target_sma == 0:
            self.target_sma = self.vessel.orbit.semi_major_axis
        else:
            self.target_sma = target_sma
        self.delay = delay

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
    def initial_altitude(self):
        """Set the initial altitude."""
        body_radius = self.vessel.orbit.body.equatorial_radius
        return self.initial_sma - body_radius

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
    def transfer_time(self):
        """Transit time for the transfer."""
        return self.transfer_period / 2

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

    def __str__(self):
        """Create the informal string representation of the class."""
        line = f'Hohmann transfer from '
        line += f'{self.initial_altitude/1000:5.0f} km altitude to'
        line += f'{self.target_altitude/1000:5.0f} km altitude:\n'
        line += f'    1. Wait: {self.delay:7.0f} seconds to '
        line += f'burn: {self.initial_dV:5.1f} m/s prograde.\n'
        line += f'    2. Wait: {self.transfer_time:7.0f} seconds to '
        line += f'burn: {self.final_dV:5.1f} m/s prograde.\n'
        return line

    def __repr__(self):
        """Create the formal string representation of the class."""
        line = f'HohmannTransfer(target_sma='
        line += f'{self.target_sma}, delay='
        line += f'{self.delay})'
        return line

    def transfer_to_rendezvous(self):
        """
        Set up to rendez-vous with current target vessel.

        Once the instance has been initialized, use this method to set up a
        rendez-vous with the current target vessel:
            from HohmannTransfer import HohmannTransfer
            transfer = HohmannTransfer()
            transfer.transfer_to_rendezvous()

        This will automatically set both the target_sma and the delay for you.

        If you call this method without a target vessel, it does not change
        the transfer, but prints a warning to the console.

        """
        try:
            target = self.conn.space_center.target_vessel
            self.target_sma = target.orbit.semi_major_axis

            rf = target.orbit.body.reference_frame
            self.target_phase = target.flight(rf).longitude
        except AttributeError:
            print('No target found: transfer unchanged.')

    def transfer_to_synchronous_orbit(self):
        """
        Set up a transfer to synchronous orbit.

        Once the instance has been initialized, use this method to set up a
        transfer to synchronous orbit:
            from HohmannTransfer import HohmannTransfer
            transfer = HohmannTransfer()
            transfer.transfer_to_synchronous_orbit()

        This will automatically set the target_sma for you.

        If you wish to end up over a particular longitude, you can set the
        target_phase to that value, and it will set the delay for you:
            KSC_LONGITUDE = 285.425
            transfer.target_phase = KSC_LONGITUDE
        """
        rotational_period = self.vessel.orbit.body.rotational_period
        self.target_period = rotational_period

    def add_nodes(self):
        """Add two maneuver nodes to set up transfer."""
        start_time = self.conn.space_center.ut + self.delay
        stop_time = start_time + self.transfer_time
        self.vessel.control.add_node(start_time, prograde=self.initial_dV)
        self.vessel.control.add_node(stop_time, prograde=self.final_dV)
