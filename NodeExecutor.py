"""Simple node execution class."""

from math import exp
import time
import krpc


class NodeExecutor(object):
    """Automatically execute the next maneuver node."""

    def __init__(self, minimum_burn_time=4):
        """Create a connection to krpc and initialize from active vessel."""
        self.conn = krpc.connect(name='NodeExecutor')
        self.vessel = self.conn.space_center.active_vessel
        self.minimum_burn_time = minimum_burn_time
        self.thrust = self.vessel.available_thrust
        assert(minimum_burn_time >= 0)
        self.approach_margins = [180, 5]
        return

    @property
    def node(self):
        """Retrieve the first node in nodes[]."""
        try:
            return self.vessel.control.nodes[0]
        except IndexError:
            return None

    @property
    def has_node(self):
        """Check that the active vessel has a next node."""
        return self.node is not None

    @property
    def delta_v(self):
        """Retrieve the node's deltaV."""
        return self.node.delta_v

    @property
    def burn_time_at_max_thrust(self):
        """Calculate burn time at max thrust using the rocket equation."""
        F = self.vessel.available_thrust
        Isp = self.vessel.specific_impulse * 9.82
        m0 = self.vessel.mass
        m1 = m0 / exp(self.delta_v/Isp)
        flow_rate = F / Isp
        return (m0 - m1) / flow_rate

    @property
    def maximum_throttle(self):
        """Set the maximum throttle to keep burn time above minimum."""
        if self.minimum_burn_time == 0:
            return 1
        return min(1, self.burn_time_at_max_thrust/self.minimum_burn_time)

    @property
    def burn_time(self):
        """Set the burn time based on maximum throttle."""
        return max(self.burn_time_at_max_thrust, self.minimum_burn_time)

    @property
    def burn_ut(self):
        """Set the time to start the burn."""
        return self.node.ut - self.burn_time/2

    def align_to_burn(self):
        """Set the autopilot to align with the burn vector."""
        print(f'Aligning at T0-{(self.node.ut-self.conn.space_center.ut):.0f} seconds')
        self.ap = self.vessel.auto_pilot
        self.ap.reference_frame = self.node.reference_frame
        self.ap.target_direction = (0, 1, 0)
        self.ap.target_roll = float('nan')
        self.ap.engage()
        time.sleep(0.1)
        self.ap.wait()
        return

    def warp_safely_to_burn(self, margin):
        """Warp to margin seconds before burn_time."""
        warp_time = self.burn_ut - margin
        if self.conn.space_center.ut < warp_time:
            print(f'Warping to  T0-{(self.node.ut-warp_time):.0f} seconds')
            self.conn.space_center.warp_to(warp_time)
        return

    def wait_until_ut(self, ut_threshold):
        """Wait until ut is greater than or equal to ut_threshold."""
        while self.conn.space_center.ut < ut_threshold:
            time.sleep(0.01)
        return

    def _clamp(self, value, floor, ceiling):
        """Clamps the value between the ceiling and the floor."""
        top = max(ceiling, floor)
        bottom = min(ceiling, floor)
        return max(bottom, min(top, value))

    def _throttle_manager(self, dV_left):
        """Set throttle value based on the dV left in the burn."""
        dV_ratio = dV_left / self.delta_v
        # decrease linearly to 5% of throttle_max for last 10% of dV
        throttle = self._clamp(dV_ratio*10, floor=0.05, ceiling=1)
        # obey maximum_throttle to keep burn time above minimum_burn_time
        self.vessel.control.throttle = self.maximum_throttle * throttle
        return

    def _print_burn_event(self, event_msg='Event happened'):
        """Print a burn event to stdout with time to T0 & remaining dV."""
        T0 = self.node.ut - self.conn.space_center.ut
        if T0 > 0:
            print(f'{event_msg} at T0-{abs(T0):.0f} seconds')
        else:
            print(f'{event_msg} at T0+{abs(T0):.0f} seconds')
        return

    def _auto_stage(self, old_thrust):
        """Return available_thrust, with side effect of staging if it drops more than 10%."""
        try:
            thrust_ratio = self.vessel.available_thrust / old_thrust
        except ZeroDivisionError:
            thrust_ratio = 1
        if thrust_ratio < 0.9:
            old_throttle = self.vessel.control.throttle
            self.vessel.control.throttle = 0.0
            time.sleep(0.1)
            self.vessel.control.activate_next_stage()
            self._print_burn_event('Staged')
            time.sleep(0.1)
            self.vessel.control.throttle = old_throttle
        return self.vessel.available_thrust

    def _cleanup(self):
        """Remove the node & disengage autopilot."""
        # TODO: engage SAS stability control if it exists
        self.vessel.auto_pilot.disengage()
        self.node.remove()
        return

    def _wait_to_go_around_again(self):
        """Block until it's time to go thru the burn loop again."""
        time.sleep(0.01)
        return

    def _burn_loop(self):
        """Run thru the burn loop."""
        with self.conn.stream(getattr, self.vessel.auto_pilot, 'error') as error:
            with self.conn.stream(getattr, self.node, 'remaining_delta_v') as dV_left:
                available_thrust = self.vessel.available_thrust
                while not error() > 20:
                    self._throttle_manager(dV_left())
                    available_thrust = self._auto_stage(available_thrust)
                    self._wait_to_go_around_again()
        self.vessel.control.throttle = 0.0
        return

    def _print_burn_error(self, dV_left):
        """Print out error on remaining_burn_vector to stdout."""
        print(f'{dV_left/self.delta_v:2.2f}% of original dV left.')

    def burn_baby_burn(self):
        """Set up the stream for dV_left, run the burn loop, and then clean up."""
        self._print_burn_event('Ignition')

        self._burn_loop()

        self._print_burn_event('MECO')
        self._print_burn_error(self.node.remaining_delta_v)

        self._cleanup()
        return

    def execute_node(self):
        """Define the node execution logic."""
        for approach_margin in self.approach_margins:
            self.align_to_burn()
            self.warp_safely_to_burn(margin=approach_margin)
        self.wait_until_ut(self.burn_ut)
        self.burn_baby_burn()
        return

    def __str__(self):
        """Create the informal string representation of the class."""
        line = f'Will burn for '
        line += f'{self.delta_v:0.1f} m/s starting in '
        line += f'{(self.burn_ut-self.conn.space_center.ut):0.1f} seconds.\n'
        return line

    def __repr__(self):
        """Create the formal string representation of the class."""
        line = f'NodeExecutor(minimum_burn_time='
        line += f'{self.minimum_burn_time})'
        return line


# main loop
if __name__ == "__main__":
    hal9000 = NodeExecutor(minimum_burn_time=4)
    while hal9000.has_node:
        hal9000.execute_node()
    print('No nodes left to execute.')
