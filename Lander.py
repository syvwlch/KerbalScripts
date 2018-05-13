# This a generic version of my lander script

# initial release only handles the final touch down

from math import sqrt
import time
import krpc
from PID import PID

conn = krpc.connect(name='Launcher')

# Set up the UI
canvas = conn.ui.stock_canvas

# Get the size of the game window in pixels
screen_size = canvas.rect_transform.size

# Add a panel to contain the UI elements
panel = canvas.add_panel()

# Position the panel relative to the center of the screen
rect = panel.rect_transform
width = 400
height = 80
padding_w = 0
Padding_h = 65
rect.size = (width, height)
rect.position = (width/2+padding_w-screen_size[0]/2, screen_size[1]/2-(height/2+Padding_h))

# Add some text displaying messages to user
text = panel.add_text("...")
text.rect_transform.size = (380, 30)
text.rect_transform.position = (0, +20)
text.color = (1, 1, 1)
text.size = 18

# defining a display function to update terminal & UI at the same time


def update_UI(message='...'):
    print(message)
    text.content = message
    return


vessel = conn.space_center.active_vessel
ap = vessel.auto_pilot

# setting up variables
initial_ascent_angle = 30  # degrees off vertical
final_descent_altitude = 50  # final descent start altitude in meters
final_descent_speed = 4  # meters/second

# setting up streams
ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(), 'surface_altitude')
vertical_speed = conn.add_stream(
    getattr, vessel.flight(vessel.orbit.body.reference_frame), 'vertical_speed'
)
apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')


def hold_for_click(require_click=True):
    # wait button click to launch
    if require_click:
        update_UI('Click to start test')
        button = panel.add_button("Start")
        button.rect_transform.size = (100, 30)
        button.rect_transform.position = (135, -20)
        button_clicked = conn.add_stream(getattr, button, 'clicked')
        while True:
            if button_clicked():
                button.clicked = False
                break
            time.sleep(0.1)
        button.remove()
    return


def pop_up_a_bit(target_altitude):
    # Pre-ignition setup
    vessel.control.sas = False
    vessel.control.rcs = False
    time.sleep(1)

    # setting up autopilot
    # ap.time_to_peak=(5,10,5)
    # ap.overshoot=(0.005,0.010,0.005)
    ap.reference_frame = vessel.surface_reference_frame
    ap.target_pitch = 90 - initial_ascent_angle
    ap.target_heading = 90
    ap.target_roll = float('nan')
    ap.engage()

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
    while altitude() < target_altitude:
        time.sleep(0.1)

    # release control
    ap.disengage()
    return


def touch_down(final_descent_speed):
    #  Create PID controller.
    # p = PID(P=.25, I=0.25, D=0.025)
    p = PID(P=.25, I=0.25, D=0.025)
    # p.ClampI = 20

    # let's try to stay pointing up
    vessel.control.sas = True
    time.sleep(.1)
    vessel.control.sas_mode = conn.space_center.SASMode.retrograde

#  descent loop
    while vessel.situation is not vessel.situation.landed:
        p.setpoint(-max(0, altitude()-5)/2.5 - final_descent_speed)
        the_pids_output = p.update(vertical_speed())
        vessel.control.throttle = the_pids_output
        update_UI('Vertical V:{:03.2f}   PID returns:{:03.2f}   Throttle:{:03.2f}'
                  .format(vertical_speed(), the_pids_output, vessel.control.throttle)
                  )
        time.sleep(.1)
    vessel.control.throttle = 0.0
    return


def goodbye():
    update_UI('Enjoy your stay!')
    time.sleep(3)
    return


# main loop
if __name__ == "__main__":
    hold_for_click()

    pop_up_a_bit(final_descent_altitude)

    touch_down(final_descent_speed)

    goodbye()
