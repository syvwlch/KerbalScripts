# Simple node execution script

from math import exp
import time
import krpc

conn = krpc.connect(name='NodeExecutor')

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
Padding_h = 65 + height
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

# setting up streams & aliases
ut = conn.add_stream(getattr, conn.space_center, 'ut')
vessel = conn.space_center.active_vessel
ap  = vessel.auto_pilot

# defining a function to retrieve the next node
def get_node(require_click=True):
    # retrieve the next node
    if len(vessel.control.nodes) == 0 :
        update_UI('No node found!')
        while True:
            if len(vessel.control.nodes) > 0 :
                break
            time.sleep(0.1)
    node = vessel.control.nodes[0]

    # wait for button click to execute node
    if require_click:
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
    return node

# defining the actual node execution logic
def execute_node(node):
    abort=False

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
    ap.reference_frame = node.reference_frame
    ap.target_direction = (0, 1, 0)
    ap.engage()
    ap.wait()

    # warp to burn
    burn_ut =  node.ut - (burn_time/2.)
    lead_time = 5
    if ut() < burn_ut - lead_time:
        update_UI('Warping to node')
        conn.space_center.warp_to(burn_ut - lead_time)
    while ut() < burn_ut :
        pass

    # executing 98% of node dV
    # abortable
    # auto-aborts if autopilot heading error exceeds 20 degrees
    update_UI('Executing burn')
    remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
    vessel.control.throttle = 1.0
    button = panel.add_button("Abort")
    button.rect_transform.size=(100,30)
    button.rect_transform.position = (135, -20)
    button_clicked = conn.add_stream(getattr, button, 'clicked')
    while True:
        if button_clicked() or ap.error > 20:
            abort = True
        if remaining_burn()[1] < delta_v * 0.02:
            update_UI('Fine tuning burn')
            vessel.control.throttle = 0.05
        if remaining_burn()[1] < delta_v * 0.001 or abort:
            break
        time.sleep(0.1)
    vessel.control.throttle = 0.0

    # remove the abort button
    button.remove()

    # wait for button click to remove the node & release autopilot
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
    ap.disengage()
    node.remove()

    # say goodbye
    update_UI('Have a safe flight!')
    return

# main loop
if __name__ == "__main__":
    while True:
        execute_node(get_node())
