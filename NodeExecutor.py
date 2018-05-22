"""Simple node execution script."""

from math import exp
import time
import krpc


class NodeExecutor:
    """Automatically execute the next maneuver node."""
    def __init__(self, minimum_burn_time=4):
        """Create a connection to krpc and initialize from active vessel."""
        self.conn = krpc.connect(name='NodeExecutor')
        self.minimum_burn_time = minimum_burn_time

    @property
    def vessel(self):
        """Retrieve the active vessel."""
        self.vessel = self.conn.space_center.active_vessel

    @property
    def autopilot(self):
        """Retrieve the autopilot."""
        self.ap = self.vessel.auto_pilot

    @property
    def ut(self):
        """Set up a stream for universal time."""
        return self.conn.add_stream(getattr, conn.space_center, 'ut')

    @property
    def has_node(self):
        """Check that the active vessel has a next node."""
        return len(self.vessel.control.nodes) > 0

    @property
    def node(self):
        """Retrieve the next node."""
        return self.vessel.control.nodes[0]

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

    def clamp(value, floor, ceiling):
        """Clamps the value between the ceiling and the floor."""
        top = max(ceiling, floor)
        bottom = min(ceiling, floor)
        return max(bottom, min(top, value))

    @property
    def maximum_throttle(self):
        """Set the maximum throttle to keep burn time above minimum."""
        return min(1, self.burn_time/burn_time_min)

    @property
    def maximum_throttle(self):
        """Set the maximum throttle to keep burn time above minimum."""
        return min(1, self.burn_time/burn_time_min)
        burn_time = max(self.burn_time, burn_time_min)

    @property
    def maximum_throttle(self):
        """Set the maximum throttle to keep burn time above minimum."""
        return min(1, self.burn_time/burn_time_min)
        burn_ut = self.ut - (burn_time/2)

    def execute_node(node):
        """Define the actual node execution logic."""
        # setting a max throttle to keep burn time above minimum
        throttle_max = min(1, self.burn_time/burn_time_min)
        burn_time = max(self.burn_time, burn_time_min)
        burn_ut = self.ut - (burn_time/2)

        # warp closer to burn
        lead_time = 300
        if ut() < burn_ut - lead_time:
            print(f'Warping to {lead_time:3.0} seconds before burn.')
            conn.space_center.warp_to(burn_ut - lead_time)

        # align with burn vector
        print('Aligning to burn')
        ap.reference_frame = node.reference_frame
        ap.target_direction = (0, 1, 0)
        ap.target_roll = float('nan')
        ap.engage()
        time.sleep(0.1)
        ap.wait()

        # warp closer to burn
        lead_time = 5
        if ut() < burn_ut - lead_time:
            print(f'Warping to {lead_time:3.0} seconds before burn.')
            conn.space_center.warp_to(burn_ut - lead_time)

        while ut() < burn_ut:
            pass

        # executing node
        # obeys throttle_max to help with smaller maneuvers
        # auto-aborts if autopilot heading error exceeds 20 degrees
        # throttles down linearly for last 20% of dV
        print('Executing burn')
        dV_left = conn.add_stream(node.dV_left_vector, node.reference_frame)
        vessel.control.throttle = throttle_max
        delta_v_finetune = delta_v * 0.2
        while True:
            throttle = throttle_max * clamp(dV_left()[1]/delta_v_finetune, 0.01, 1)
            vessel.control.throttle = throttle
            if ap.error > 20:
                print('Auto-abort!!!')
                break
            if dV_left()[1] < 0.04:
                print('Burn complete')
                break
            time.sleep(0.01)

        # kill throttle, remove the node & release autopilot
        vessel.control.throttle = 0.0
        ap.disengage()
        node.remove()
        return


# main loop
if __name__ == "__main__":
    if has_node():
        execute_node(get_node())
