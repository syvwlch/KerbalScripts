# This is intendend to get my
# Orbits 'R Us four-seat tourist ferry
# up into a nice clean orbit

# Changes made to rocket for this script to work:
# 1. Disabled roll control on the first stage fins, to reduce oscillations

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

# Add some text displaying messages to user
text = panel.add_text("Booting Autopilot")
text.rect_transform.position = (0, 20)
text.color = (1, 1, 1)
text.size = 16

# defining a display function to update terminal & UI at the same time
def update_UI(message='Testing UI'):
    print(message)
    text.content = message
    return

vessel = conn.space_center.active_vessel

# setting up variables
SRB_pitch = 85
target_apoapsis = 80000
burn_time_to_apoapsis = 30

# setting up streams

# setting up autopilot
vessel.auto_pilot.target_pitch_and_heading(90, 90)
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
vessel.auto_pilot.target_pitch_and_heading(SRB_pitch, 90)
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

# switching to SAS prograde
vessel.auto_pilot.disengage()
vessel.auto_pilot.sas = True
time.sleep(0.1) # check if this is truly necessary
vessel.auto_pilot.sas_mode = vessel.auto_pilot.sas_mode.prograde
update_UI('Setting SAS to point prograde')

# waiting for apoapsis to match target before initiating MECO
apoapsis_altitude = conn.get_call(getattr, vessel.orbit, 'apoapsis_altitude')
expr = conn.krpc.Expression.greater_than(
    conn.krpc.Expression.call(apoapsis_altitude),
    conn.krpc.Expression.constant_double(target_apoapsis))
event = conn.krpc.add_event(expr)
with event.condition:
    event.wait()
vessel.control.throttle = 0
update_UI('Coasting to apoapsis')

# waiting before starting circularization burn
time_to_apoapsis = conn.get_call(getattr, vessel.orbit, 'time_to_apoapsis')
expr = conn.krpc.Expression.less_than(
    conn.krpc.Expression.call(time_to_apoapsis),
    conn.krpc.Expression.constant_double(burn_time_to_apoapsis))
event = conn.krpc.add_event(expr)
with event.condition:
    event.wait()
vessel.control.throttle = 1
update_UI('Initiating circularization burn')

# implement automatic staging between stage 2 and stage 3
update_UI('Please stage manually')

# stop circularization burn
periapsis_altitude = conn.get_call(getattr, vessel.orbit, 'periapsis_altitude')
expr = conn.krpc.Expression.greater_than(
    conn.krpc.Expression.call(periapsis_altitude),
    conn.krpc.Expression.constant_double(target_apoapsis))
event = conn.krpc.add_event(expr)
with event.condition:
    event.wait()
vessel.control.throttle = 0
update_UI('MECO')

# handing control back
vessel.auto_pilot.sas = False
update_UI('Autopilot releasing control')
