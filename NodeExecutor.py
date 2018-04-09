# Simple node execution script

from math import exp
import time
import krpc
conn = krpc.connect(name='Node Executor')

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
text = panel.add_text("Retrieving next maneuver node")
text.rect_transform.size = (380, 30)
text.rect_transform.position = (0, +20)
text.color = (1, 1, 1)
text.size = 18

# defining a display function to update terminal & UI at the same time
def update_UI(message='...'):
    print(message)
    text.content = message
    return

# setting up streams & aliases
ut = conn.add_stream(getattr, conn.space_center, 'ut')
vessel = conn.space_center.active_vessel

# retrieve the next node
if len(vessel.control.nodes) == 0 :
    update_UI('No node found!')
    while True:
        if len(vessel.control.nodes) > 0 :
            break
        time.sleep(0.1)
node = vessel.control.nodes[0]

# wait for button click to execute node
update_UI('Click to execute node')
button = panel.add_button("Execute")
button.rect_transform.size=(100,30)
button.rect_transform.position = (135, -20)
button_clicked = conn.add_stream(getattr, button, 'clicked')
while True:
    if button_clicked():
        button.clicked = False
        break
    time.sleep(0.1)
button.remove()

# calculating burn time (using rocket equation)
delta_v = node.delta_v
F = vessel.available_thrust
Isp = vessel.specific_impulse * 9.82
m0 = vessel.mass
m1 = m0 / exp(delta_v/Isp)
flow_rate = F / Isp
burn_time = (m0 - m1) / flow_rate

# point to maneuver
update_UI('Aligning to burn')
vessel.auto_pilot.reference_frame = node.reference_frame
vessel.auto_pilot.target_direction = (0, 1, 0)
vessel.auto_pilot.engage()
vessel.auto_pilot.wait()

# warp to burn
burn_ut =  node.ut - (burn_time/2.)
lead_time = 5
update_UI('Warping to node')
conn.space_center.warp_to(burn_ut - lead_time)

# executing 98% of the burn
update_UI('Executing burn')
vessel.control.throttle = 1.0
time.sleep(burn_time * 0.98)

# fine tuning burn to max of 0.1 m/s or 0.1% of node dV
update_UI('Fine tuning burn')
vessel.control.throttle = 0.05
remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
while remaining_burn()[1] > max(0.1, delta_v * 0.001):
    pass
vessel.control.throttle = 0.0

# wait for button click to remove the node
update_UI('Click to delete node')
button = panel.add_button("Delete")
button.rect_transform.size=(100,30)
button.rect_transform.position = (135, -20)
button_clicked = conn.add_stream(getattr, button, 'clicked')
while True:
    if button_clicked():
        button.clicked = False
        break
    time.sleep(0.1)
button.remove()
node.remove()

# pointing prograde before handing control back
update_UI('Pointing prograde')
vessel.auto_pilot.reference_frame = vessel.orbital_reference_frame
vessel.auto_pilot.target_direction = (0, 1, 0)
vessel.auto_pilot.wait()

update_UI('Have a safe flight!')
time.sleep(3)
