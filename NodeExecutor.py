"""Simple node execution script."""

from math import exp
import time
import krpc


class NodeExecutor:
    """Automatically execute the next maneuver node."""

    def __init__(self):
        """Create a connection to krpc and initialize from active vessel."""
        self.conn = krpc.connect(name='NodeExecutor')
        self.vessel = self.conn.space_center.active_vessel
        self.ap = self.vessel.auto_pilot
        self.node = self.vessel.control.nodes[0]

    @property
    def ut(self):
        """Set up a stream for universal time."""
        return self.conn.add_stream(getattr, self.conn.space_center, 'ut')

    @property
    def has_node(self):
        """Check that the active vessel has a next node."""
        return len(self.vessel.control.nodes) > 0

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
        return min(1, self.burn_time_at_max_thrust/self.minimum_burn_time)

    @property
    def burn_time(self):
        """Set the burn time based on maximum throttle."""
        return max(self.burn_time_at_max_thrust, self.minimum_burn_time)

    @property
    def burn_ut(self):
        """Set the time to start the burn."""
        return self.node.ut - self.burn_time/2

    def execute_node(self, minimum_burn_time=4):
        """Define the actual node execution logic."""
        self.minimum_burn_time = minimum_burn_time
        # warp closer to burn
        warp_time = self.burn_ut - 180
        if self.ut() < warp_time:
            print(f'Warping closer to burn.')
            self.conn.space_center.warp_to(warp_time)

        # align with burn vector
        print('Aligning to burn')
        self.ap.reference_frame = self.node.reference_frame
        self.ap.target_direction = (0, 1, 0)
        self.ap.target_roll = float('nan')
        self.ap.engage()
        time.sleep(0.1)
        self.ap.wait()

        # warp to burn
        warp_time = self.burn_ut - 5
        if self.ut() < warp_time:
            print(f'Warping to burn.')
            self.conn.space_center.warp_to(warp_time)

        while self.ut() < self.burn_ut:
            pass

        # executing node
        # obeys throttle_max to help with smaller maneuvers
        # auto-aborts if autopilot heading error exceeds 20 degrees
        # throttles down linearly for last 10% of dV
        print('Executing burn')
        dV_left = self.conn.add_stream(self.node.remaining_burn_vector,
                                       self.node.reference_frame,)
        self.vessel.control.throttle = self.maximum_throttle
        delta_v_finetune = self.delta_v * 0.1
        while True:
            throttle = self.clamp(dV_left()[1]/delta_v_finetune, 0.05, 1)
            throttle *= self.maximum_throttle
            self.vessel.control.throttle = throttle
            if self.ap.error > 20:
                print('Auto-abort!!!')
                break
            if dV_left()[1] < 0.04:
                print('Burn complete')
                break
            time.sleep(0.01)

        # kill throttle, remove the node & release autopilot
        self.vessel.control.throttle = 0.0
        self.ap.disengage()
        self.node.remove()
        return


# main loop
if __name__ == "__main__":
    hal9000 = NodeExecutor()
    if hal9000.has_node:
        hal9000.execute_node(minimum_burn_time=4)
