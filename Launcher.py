"""Simple launch class."""

from math import sqrt
import time
import krpc
from NodeExecutor import NodeExecutor


class Launcher(object):
    """Automatically launch to target_altitude and set up the circulization node."""

    def __init__(self, target_altitude, target_inclination=0):
        """Create a connection to krpc and initialize from active vessel."""
        self.conn = krpc.connect(name='Launcher')
        self.vessel = self.conn.space_center.active_vessel
        self.target_altitude = target_altitude
        self.target_inclination = target_inclination
        # setting up streams
        self.altitude = self.conn.add_stream(getattr, self.vessel.flight(), 'mean_altitude')
        self.apoapsis = self.conn.add_stream(getattr, self.vessel.orbit, 'apoapsis_altitude')
        return

    def ignition(self):
        """Perform ignition."""
        # Pre-ignition setup
        self.vessel.control.sas = False
        self.vessel.control.rcs = False
        self.vessel.control.throttle = 1.0
        time.sleep(1)

        # setting up autopilot
        ap = self.vessel.auto_pilot
        ap.time_to_peak = (5, 10, 5)
        ap.overshoot = (0.005, 0.010, 0.005)
        ap.reference_frame = self.vessel.surface_reference_frame
        ap.target_pitch = 90
        ap.target_heading = 90 - self.target_inclination
        ap.target_roll = 180
        ap.engage()

        # releasing clamps & igniting first stage
        self.vessel.control.activate_next_stage()
        return

    def ascent(self):
        """Perform the ascent until apoapsis reaches target_altitude."""
        def _ascent_angle(altitude):
            """Calculate the ascent angle at the current altitude."""
            TURN_START_ALTITUDE = 1000
            TURN_START_ANGLE = 80
            TURN_END_ALTITUDE = 60*1000

            if altitude > TURN_START_ALTITUDE and altitude < TURN_END_ALTITUDE:
                frac = ((TURN_END_ALTITUDE - altitude) /
                        (TURN_END_ALTITUDE - TURN_START_ALTITUDE))
                turn_angle = frac * TURN_START_ANGLE
            elif altitude >= TURN_END_ALTITUDE:
                turn_angle = 0
            else:
                turn_angle = 90
            return turn_angle

        turn_angle = 90
        thrust = self.vessel.available_thrust
        while True:
            # ascent profile
            new_turn_angle = _ascent_angle(self.altitude())
            if abs(new_turn_angle - turn_angle) > 0.5:
                turn_angle = new_turn_angle
                self.vessel.auto_pilot.target_pitch = turn_angle

            if self.vessel.available_thrust < 0.9 * thrust:
                self.vessel.control.throttle = 0.0
                time.sleep(0.5)
                self.vessel.control.activate_next_stage()
                time.sleep(0.5)
                self.vessel.control.throttle = 1.0
                thrust = self.vessel.available_thrust

            # break out when reaching target apoapsis
            if self.apoapsis() > self.target_altitude:
                self.vessel.control.throttle = 0.0
                break
        return

    def circularization(self):
        """Set up circulization maneuver."""
        mu = self.vessel.orbit.body.gravitational_parameter
        r = self.vessel.orbit.apoapsis
        a1 = self.vessel.orbit.semi_major_axis
        a2 = r
        v1 = sqrt(mu*((2./r)-(1./a1)))
        v2 = sqrt(mu*((2./r)-(1./a2)))
        delta_v = v2 - v1
        self.vessel.control.add_node(
            self.conn.space_center.ut + self.vessel.orbit.time_to_apoapsis,
            prograde=delta_v, )
        return

    def execute(self):
        """Define the launch execution logic."""
        self.ignition()
        self.ascent()
        self.circularization()
        return

    def __str__(self):
        """Create the informal string representation of the class."""
        line = f'Will launch to {(self.target_altitude/1000):.1f}km '
        line += f' and set up the circularization maneuver node.\n'
        return line

    def __repr__(self):
        """Create the formal string representation of the class."""
        line = f'Launcher(target_altitude='
        line += f'{self.target_altitude}, target_inclination='
        line += f'{self.target_inclination})'
        return line


# main loop
if __name__ == "__main__":
    launcher = Launcher(target_altitude=80*1000, target_inclination=0)
    launcher.execute()
    del(launcher)

    node_doer = NodeExecutor(minimum_burn_time=4)
    node_doer.execute_node()
