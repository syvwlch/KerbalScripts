# This a generic version of my launch script

# initial release leaves staging to the pilot

from math import sqrt
import time
import krpc
from NodeExecutor import execute_node

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
turn_start_altitude = 1000
turn_start_angle = 80
turn_end_altitude = 60*1000
target_inclination = 0
target_altitude = 80*1000

# setting up streams
ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')

def hold_for_click(require_click=True):
    # wait button click to launch
    if require_click:
        update_UI('Click to launch')
        button = panel.add_button("Launch")
        button.rect_transform.size=(100,30)
        button.rect_transform.position = (135, -20)
        button_clicked = conn.add_stream(getattr, button, 'clicked')
        while True:
            if button_clicked():
                button.clicked = False
                break
            time.sleep(0.1)
        button.remove()
    return

def ignition():
    # Pre-ignition setup
    vessel.control.sas = False
    vessel.control.rcs = False
    vessel.control.throttle = 1.0
    time.sleep(1)

    # setting up autopilot
    ap.time_to_peak=(5,10,5)
    ap.overshoot=(0.005,0.010,0.005)
    ap.reference_frame = vessel.surface_reference_frame
    ap.target_pitch=90
    ap.target_heading=90-target_inclination
    ap.target_roll=180
    ap.engage()

    # releasing clamps & igniting first stage
    vessel.control.activate_next_stage()
    update_UI('Ignition')
    return

def ascent_angle(altitude):
    if altitude > turn_start_altitude and altitude < turn_end_altitude:
        frac = ((turn_end_altitude - altitude) /
                (turn_end_altitude - turn_start_altitude))
        turn_angle = frac * turn_start_angle
    elif altitude >= turn_end_altitude:
        turn_angle = 0
    else:
        turn_angle = 90
    return turn_angle

def ascent():
    update_UI('Gravity turn')
    turn_angle = 90
    while True:
        # ascent profile
        new_turn_angle = ascent_angle(altitude())
        if abs(new_turn_angle - turn_angle) > 0.5:
            turn_angle = new_turn_angle
            ap.target_pitch = turn_angle

        # break out when reaching target apoapsis
        if apoapsis() > target_altitude:
            update_UI('Target apoapsis reached')
            vessel.control.throttle = 0.0
            break
    return

def circularization():
    # setting up circulization maneuver
    mu = vessel.orbit.body.gravitational_parameter
    r = vessel.orbit.apoapsis
    a1 = vessel.orbit.semi_major_axis
    a2 = r
    v1 = sqrt(mu*((2./r)-(1./a1)))
    v2 = sqrt(mu*((2./r)-(1./a2)))
    delta_v = v2 - v1
    node = vessel.control.add_node(
        ut() + vessel.orbit.time_to_apoapsis, prograde=delta_v)
    return node

def goodbye():
    update_UI('Enjoy your orbit!')
    time.sleep(3)
    return

# main loop
if __name__ == "__main__":
    hold_for_click()

    ignition()

    conn.space_center.physics_war_factor = 2

    ascent()

    conn.space_center.physics_war_factor = 0

    execute_node(circularization())

    goodbye()
