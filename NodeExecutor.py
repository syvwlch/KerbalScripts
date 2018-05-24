"""Simple node execution class."""

from math import exp
import time
import krpc


class NodeExecutor:
    """Automatically execute the next maneuver node."""

    def __init__(self, minimum_burn_time=4):
        """Create a connection to krpc and initialize from active vessel."""
        self.conn = krpc.connect(name='NodeExecutor')
        self.vessel = self.conn.space_center.active_vessel
        self.minimum_burn_time = minimum_burn_time
        assert(minimum_burn_time >= 0)
        return

    @property
    def node(self):
        """Retrieve the first node in nodes[]."""
        if len(self.vessel.control.nodes) > 0:
            return self.vessel.control.nodes[0]
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

    def clamp(self, value, floor, ceiling):
        """Clamps the value between the ceiling and the floor."""
        top = max(ceiling, floor)
        bottom = min(ceiling, floor)
        return max(bottom, min(top, value))

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
        print('Aligning to burn')
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
            print(f'Warping to {margin:3.0f} seconds before burn.')
            self.conn.space_center.warp_to(warp_time)
        return

    def wait_until_ut(self, ut_threshold):
        """Wait until ut is greater than or equal to ut_threshold."""
        while self.conn.space_center.ut < ut_threshold:
            time.sleep(0.01)

    def burn_baby_burn(self):
        """Burn until dV_left is nearly zero, or autopilot.error is too great."""
        # TODO: Consider making a non-blocking version of this, or at least
        # bringing in logic to stage as necessary.

        self.wait_until_ut(self.burn_ut)
        print(f'Burn starting at T0 - {(self.node.ut-self.conn.space_center.ut):.0f} seconds')
        print(f'    {self.delta_v:3.1f} m/s to go')

        # set up stream for remaining_burn_vector
        dV_left = self.conn.add_stream(self.node.remaining_burn_vector,
                                       self.node.reference_frame,)

        # burn loop
        thrust = self.vessel.available_thrust
        while True:
            # calculate the ratio of remaining dV to starting dV
            dV_ratio = dV_left()[1] / self.delta_v

            # decrease linearly to 5% of throttle_max for last 10% of dV
            throttle = self.clamp(dV_ratio/0.10, floor=0.05, ceiling=1)
            # obey maximum_throttle to keep burn time above minimum_burn_time
            self.vessel.control.throttle = self.maximum_throttle * throttle

            # stage if needed
            thrust_ratio = self.vessel.available_thrust / thrust
            if thrust_ratio < 0.9:
                self.vessel.control.throttle = 0.0
                self.time.sleep(0.1)
                self.vessel.control.activate_next_stage()
                print('Staged')
                self.time.sleep(0.1)
                self.maximum_throttle = self.clamp(self.maximum_throttle/thrust_ratio,
                                                   floor=0,
                                                   ceiling=1,)
                self.vessel.control.throttle = self.maximum_throttle * throttle
                thrust = self.vessel.available_thrust

            # break out if autopilot steering error exceeds 20 degrees
            if self.ap.error > 20:
                print('Overshot')
                break

            # break out if dV_left rounds down to 0.0
            if dV_left()[1] < 0.04:
                print('Undershot')
                break

            # wait 10ms before looping around
            time.sleep(0.01)

        # kill throttle & stream
        self.vessel.control.throttle = 0.0
        print(f'Burn complete at T0 + {(self.conn.space_center.ut-self.node.ut):.0f} seconds')
        print(f'    {dV_left()[1]:3.1f} m/s over/under')
        dV_left.remove()
        return

    def cleanup(self):
        """Remove the node & disengage autopilot."""
        # TODO: engage SAS stability control if it exists
        self.ap = self.vessel.auto_pilot
        self.ap.disengage()
        self.node.remove()
        return

    def execute_node(self):
        """Define the node execution logic."""
        self.align_to_burn()
        self.warp_safely_to_burn(margin=180)

        self.align_to_burn()
        self.warp_safely_to_burn(margin=5)

        self.burn_baby_burn()

        self.cleanup()
        return


# main loop
if __name__ == "__main__":
    hal9000 = NodeExecutor(minimum_burn_time=4)
    while hal9000.has_node:
        hal9000.execute_node()
    print('No nodes left to execute.')
