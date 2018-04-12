# This is intendend to get my
# Orbits 'R Us four-seat tourist ferry
# up into a nice clean orbit

# Changes made to rocket for this script to work:
# 1. Added reaction wheel to main stage

import time
import krpc
conn = krpc.connect(name='RemoteAutoPilot')

# Set up the UI
canvas = conn.ui.stock_canvas

# Get the size of the game window in pixels
screen_size = canvas.rect_transform.size

# Add a panel to contain the UI elements
panel = canvas.add_panel()

# Position the panel relative to the center of the screen
rect = panel.rect_transform
rect.size = (400, 100)
rect.position = (210-(screen_size[0]/2), 300)

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
SRB_pitch_over = 5
target_inclination = 0
transition_altitude = 35*1000 # when to switch to orbital_reference_frame
target_apoapsis = 80*1000
burn_time_to_circularize = 60 # hardcoded for now, calculate eventually

# setting up streams
button_clicked = conn.add_stream(getattr, button, 'clicked')

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

# releasing clamps & firing SRBs
vessel.control.activate_next_stage()
update_UI('SRB Ignition')

# waiting for altitude to exceed 300 meters before initiating turn
mean_altitude = conn.get_call(getattr, vessel.flight(), 'mean_altitude')
expr = conn.krpc.Expression.greater_than(
    conn.krpc.Expression.call(mean_altitude),
    conn.krpc.Expression.constant_double(300))
event = conn.krpc.add_event(expr)
with event.condition:
    event.wait()
vessel.auto_pilot.target_pitch=90-SRB_pitch_over
update_UI('Initiating turn')

# waiting for SRBs to flame out before ditching them
fuel_amount = conn.get_call(vessel.resources.amount, 'SolidFuel')
expr = conn.krpc.Expression.less_than(
    conn.krpc.Expression.call(fuel_amount),
    conn.krpc.Expression.constant_float(0.1))
event = conn.krpc.add_event(expr)
with event.condition:
    event.wait()
vessel.control.activate_next_stage()
update_UI('SRB Separation')

# liquid fuel stage will start automatically, throttle already set
update_UI('Stage 2 Ignition')

# switching to new reference_frame
vessel.auto_pilot.disengage()
vessel.auto_pilot.reference_frame = vessel.surface_velocity_reference_frame
vessel.auto_pilot.target_pitch=0
vessel.auto_pilot.target_heading=0
vessel.auto_pilot.target_roll=0
vessel.auto_pilot.engage()
update_UI('Pointing prograde relative to surface')

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
update_UI('Pointing prograde relative to orbit')

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

# waiting before starting circularization burn
time_to_apoapsis = conn.get_call(getattr, vessel.orbit, 'time_to_apoapsis')
expr = conn.krpc.Expression.less_than(
    conn.krpc.Expression.call(time_to_apoapsis),
    conn.krpc.Expression.constant_double(burn_time_to_circularize/2))
event = conn.krpc.add_event(expr)
with event.condition:
    event.wait()
vessel.control.throttle = 1
update_UI('Initiating circularization burn')

# stop circularization burn when apoapsis & periapsis swap around orbit
period = conn.get_call(getattr, vessel.orbit, 'period')
time_to_periapsis = conn.get_call(getattr, vessel.orbit, 'time_to_periapsis')
expr = conn.krpc.Expression.or_(
    conn.krpc.Expression.less_than(
        conn.krpc.Expression.divide(
            conn.krpc.Expression.call(time_to_periapsis),
            conn.krpc.Expression.call(period)),
        conn.krpc.Expression.constant_double(.25)),
    conn.krpc.Expression.greater_than(
        conn.krpc.Expression.divide(
            conn.krpc.Expression.call(time_to_periapsis),
            conn.krpc.Expression.call(period)),
        conn.krpc.Expression.constant_double(.75)))
event = conn.krpc.add_event(expr)
with event.condition:
    event.wait()
vessel.control.throttle = 0
update_UI('MECO')

# handing control back
update_UI('Autopilot releasing control')
