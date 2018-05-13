"""
This my first lander script.

The initial release only handles the final touch down.
"""

import time
from PID import PID
import InitialSetUp

MODULE_HANDLE = 'HohmannTransfer'

logger = InitialSetUp.set_up_logger(MODULE_HANDLE + '.log')
conn = InitialSetUp.connect_to_krpc_server(MODULE_HANDLE)

# setting up variables
INITIAL_ASCENT_ANGLE = 30  # degrees off vertical
FINAL_DESCENT_ALTITUDE = 50  # final descent start altitude in meters
FINAL_DESCENT_SPEED = 4  # meters/second


def pop_up_a_bit(target_altitude):
    """
    Launch to target altitude if vessel is landed.

    Otherwise, do nothing.
    """
    vessel = conn.space_center.active_vessel
    if vessel.situation is vessel.situation.landed:
        # Pre-ignition setup
        vessel.control.sas = False
        vessel.control.rcs = False
        time.sleep(1)

        # setting up autopilot
        ap = vessel.auto_pilot
        # ap.time_to_peak=(5,10,5)
        # ap.overshoot=(0.005,0.010,0.005)
        ap.reference_frame = vessel.surface_reference_frame
        ap.target_pitch = 90 - INITIAL_ASCENT_ANGLE
        ap.target_heading = 90
        ap.target_roll = float('nan')
        ap.engage()

        with conn.stream(getattr,
                         vessel.orbit,
                         'apoapsis_altitude') as apoapsis:
            # record altitude before lift off
            liftoff_altitude = apoapsis()

            # lift off
            vessel.control.throttle = 1.0
            vessel.control.activate_next_stage()

            # MECO when ballistic arc will exceed target altitude
            while apoapsis() < liftoff_altitude + target_altitude:
                time.sleep(0.1)
            vessel.control.throttle = 0.0

        # wait to reach target mean_altitude
        with conn.stream(getattr, vessel.flight(),
                         'surface_altitude') as altitude:
            while altitude() < target_altitude:
                time.sleep(0.1)

        # release control
        ap.disengage()
    return


def touch_down(final_descent_speed):
    """Descend at speed proportional to altitude until vessel is landed."""
    vessel = conn.space_center.active_vessel

    #  Create PID controller.
    # p = PID(.25, 0.25, 0.025)
    p = PID(.25, 0.25, 0.025)
    p.ClampI = 20

    # let's try to stay pointing up
    vessel.control.sas = True
    time.sleep(.1)
    vessel.control.sas_mode = conn.space_center.SASMode.retrograde

#  descent loop
    with conn.stream(getattr,
                     vessel.flight(),
                     'surface_altitude') as altitude:
        with conn.stream(getattr,
                         vessel.flight(vessel.orbit.body.reference_frame),
                         'vertical_speed') as vertical_speed:
            while vessel.situation is not vessel.situation.landed:
                p.setpoint(-max(0, altitude()-5)/2.5 - final_descent_speed)
                the_pids_output = p.update(vertical_speed())
                vessel.control.throttle = the_pids_output
                logger.debug('Vertical V:{:03.2f}   Throttle:{:03.2f}'
                             .format(vertical_speed(),
                                     vessel.control.throttle))
                time.sleep(.1)
    vessel.control.throttle = 0.0
    return


# main loop
if __name__ == "__main__":

    pop_up_a_bit(FINAL_DESCENT_ALTITUDE)

    touch_down(FINAL_DESCENT_SPEED)
