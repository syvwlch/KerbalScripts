# Simple node execution script

import math
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

button = panel.add_button("Execute")
button.rect_transform.size=(100,30)
button.rect_transform.position = (135, -20)

# Add some text displaying messages to user
text = panel.add_text("Retrieving next maneuver node")
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

# setting up streams
ut = conn.add_stream(getattr, conn.space_center, 'ut')
button_clicked = conn.add_stream(getattr, button, 'clicked')

# retrieve the next node
node = vessel.control.nodes[0]
delta_v = node.delta_v
update_UI('Click to execute node')

# wait for button click
while True:
    if button_clicked():
        button.clicked = False
        break
    time.sleep(0.1)
button.remove()

# calculating burn time (using rocket equation)
F = vessel.available_thrust
Isp = vessel.specific_impulse * 9.82
m0 = vessel.mass
m1 = m0 / math.exp(delta_v/Isp)
flow_rate = F / Isp
burn_time = (m0 - m1) / flow_rate

# point to maneuver
vessel.auto_pilot.reference_frame = node.reference_frame
vessel.auto_pilot.target_direction = (0, 1, 0)
vessel.auto_pilot.engage()
vessel.auto_pilot.wait()

update_UI('Warping to node')

# warp to burn
burn_ut =  node.ut - (burn_time/2.)
lead_time = 5
conn.space_center.warp_to(burn_ut - lead_time)

# executing burn
update_UI('Executing burn')
vessel.control.throttle = 1.0
time.sleep(burn_time - 0.1)

# fine tuning burn to at least 0.1 m/s
update_UI('Fine tuning burn')
vessel.control.throttle = 0.05
remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
while remaining_burn()[1] > .1:
    pass
vessel.control.throttle = 0.0

# wait for button click to remove the node
button = panel.add_button("Delete")
button.rect_transform.size=(100,30)
button.rect_transform.position = (135, -20)
button_clicked = conn.add_stream(getattr, button, 'clicked')
update_UI('Click to delete node')
# wait for button click
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
