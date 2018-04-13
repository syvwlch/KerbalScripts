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

button = panel.add_button("Launch")
button.rect_transform.size=(100,30)
button.rect_transform.position = (135, -20)

# Add some text displaying messages to user
text = panel.add_text("Autopilot ready")
text.rect_transform.size = (380, 30)
text.rect_transform.position = (0, +20)
text.color = (1, 1, 1)
text.size = 18

# defining a display function to update terminal & UI at the same time
def update_UI(message='Testing UI'):
    print(message)
    text.content = message
    return

vessel = conn.space_center.active_vessel

# setting up variables
initial_pitch_over = 15
target_inclination = 0
transition_altitude = 35*1000 # when to switch to orbital_reference_frame
target_apoapsis = 100*1000
burn_time_to_circularize = 90 # hardcoded for now, calculate eventually

# setting up streams
button_clicked = conn.add_stream(getattr, button, 'clicked')
ut = conn.add_stream(getattr, conn.space_center, 'ut')

# wait for button click
while True:
    if button_clicked():
        break
    time.sleep(0.1)

# roll is less critical, and tends to oscillate
vessel.auto_pilot.time_to_peak=(5,10,5)
vessel.auto_pilot.overshoot=(0.005,0.010,0.005)

# setting up autopilot
vessel.auto_pilot.reference_frame = vessel.surface_reference_frame
vessel.auto_pilot.target_pitch=90
vessel.auto_pilot.target_heading=90-target_inclination
vessel.auto_pilot.target_roll=0
vessel.auto_pilot.engage()
update_UI('Autopilot taking control')

# setting throttle
vessel.control.throttle = 1
time.sleep(1)

# releasing clamps & igniting first stage
vessel.control.activate_next_stage()
update_UI('Ignition')

# waiting for altitude to exceed 200 meters before initial pitch over
mean_altitude = conn.get_call(getattr, vessel.flight(), 'mean_altitude')
expr = conn.krpc.Expression.greater_than(
    conn.krpc.Expression.call(mean_altitude),
    conn.krpc.Expression.constant_double(300))
event = conn.krpc.add_event(expr)
with event.condition:
    event.wait()
vessel.auto_pilot.target_pitch=90-initial_pitch_over
update_UI('Initial pitch over')

# poiting prograde relative to atmosphere at 5km altitude
expr = conn.krpc.Expression.greater_than(
    conn.krpc.Expression.call(mean_altitude),
    conn.krpc.Expression.constant_double(5000))
event = conn.krpc.add_event(expr)
with event.condition:
    event.wait()
vessel.auto_pilot.disengage()
vessel.auto_pilot.reference_frame = vessel.surface_velocity_reference_frame
vessel.auto_pilot.target_pitch=0
vessel.auto_pilot.target_heading=0
vessel.auto_pilot.target_roll=0
vessel.auto_pilot.engage()
update_UI('Initiating gravity turn')

# waiting for altitude to match target before switching reference_frame
expr = conn.krpc.Expression.greater_than(
    conn.krpc.Expression.call(mean_altitude),
    conn.krpc.Expression.constant_double(transition_altitude))
event = conn.krpc.add_event(expr)
with event.condition:
    event.wait()
vessel.auto_pilot.disengage()
vessel.auto_pilot.reference_frame = vessel.orbital_reference_frame
vessel.auto_pilot.target_pitch=0
vessel.auto_pilot.target_heading=0
vessel.auto_pilot.target_roll=180 # Swaps around between frames!
vessel.auto_pilot.engage()
update_UI('Transitioning to orbital reference frame')

# waiting for apoapsis to match target before coasting
apoapsis_altitude = conn.get_call(getattr, vessel.orbit, 'apoapsis_altitude')
expr = conn.krpc.Expression.greater_than(
    conn.krpc.Expression.call(apoapsis_altitude),
    conn.krpc.Expression.constant_double(target_apoapsis))
event = conn.krpc.add_event(expr)
with event.condition:
    event.wait()
vessel.control.throttle = 0
vessel.auto_pilot.disengage()
vessel.auto_pilot.reference_frame = vessel.surface_reference_frame
vessel.auto_pilot.target_pitch=0
vessel.auto_pilot.target_heading=90-target_inclination
vessel.auto_pilot.target_roll=0 # Swaps around between frames!
vessel.auto_pilot.engage()
update_UI('Coasting to apoapsis')

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

# execute node
execute_node(node)

# handing control back
update_UI('Autopilot releasing control')
