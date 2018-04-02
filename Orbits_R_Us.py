# This is intendend to get my
# Orbits 'R Us four-seat tourist ferry
# up into a nice clean orbit

import time
import krpc
conn = krpc.connect(name='Hello World')

vessel = conn.space_center.active_vessel

# setting up variables
SRB_pitch = 85
target_apoapsis = 80000

# setting up streams

# setting up autopilot
vessel.auto_pilot.target_pitch_and_heading(90, 90)
vessel.auto_pilot.engage()
print('Autopilot taking control')

# setting throttle
vessel.control.throttle = 1
time.sleep(1)

# releasing clamps & firing SRBs
vessel.control.activate_next_stage()
print('SRB Ignition')

# waiting for altitude to exceed 300 meters before initiating turn
mean_altitude = conn.get_call(getattr, vessel.flight(), 'mean_altitude')
expr = conn.krpc.Expression.greater_than(
    conn.krpc.Expression.call(mean_altitude),
    conn.krpc.Expression.constant_double(300))
event = conn.krpc.add_event(expr)
with event.condition:
    event.wait()
vessel.auto_pilot.target_pitch_and_heading(SRB_pitch, 90)
print('Initiating turn')

# waiting for SRBs to flame out before ditching them
fuel_amount = conn.get_call(vessel.resources.amount, 'SolidFuel')
expr = conn.krpc.Expression.less_than(
    conn.krpc.Expression.call(fuel_amount),
    conn.krpc.Expression.constant_float(0.1))
event = conn.krpc.add_event(expr)
with event.condition:
    event.wait()
vessel.control.activate_next_stage()
print('SRB Separation')

# liquid fuel stage will start automatically, throttle already set
print('Stage 2 Ignition')

# switching to SAS prograde
vessel.auto_pilot.disengage()
vessel.auto_pilot.sas = True
time.sleep(0.1) # check if this is truly necessary
vessel.auto_pilot.sas_mode = vessel.auto_pilot.sas_mode.prograde
print('Setting SAS to point prograde')

# waiting for apoapsis to match target before initiating MECO
apoapsis_altitude = conn.get_call(getattr, vessel.orbit, 'apoapsis_altitude')
expr = conn.krpc.Expression.greater_than(
    conn.krpc.Expression.call(apoapsis_altitude),
    conn.krpc.Expression.constant_double(target_apoapsis))
event = conn.krpc.add_event(expr)
with event.condition:
    event.wait()
vessel.control.throttle = 0
print('MECO')

print('Autopilot releasing control')
print('Please circularize manually')
