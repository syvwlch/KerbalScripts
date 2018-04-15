# This adds two nodes for a Hohmann transfer maneuver
# Currently assumes circular orbits, especially at the start!

# Nodes can be execute manually or with Node Executor script
# running in parallel

from math import sqrt, pi, pow
import time
import krpc

conn = krpc.connect(name='Hohmann Transfer')

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


# setting up streams
ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')

def check_initial_orbit(maximum_eccentricity=0.01,require_click=True):
    # check how circular our current orbit is
    if vessel.orbit.eccentricity > maximum_eccentricity :
        update_UI('Please circularize first!')
        while True:
            if vessel.orbit.eccentricity <= maximum_eccentricity :
                break
            time.sleep(0.1)

    # wait button click to launch
    if require_click:
        update_UI('Click to add nodes')
        button = panel.add_button("Add Nodes")
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

def Hohmann_nodes(target_apoapsis,start_time):
    # setting up first maneuver
    mu = vessel.orbit.body.gravitational_parameter
    r1 = vessel.orbit.apoapsis
    r2 = target_apoapsis + vessel.orbit.body.equatorial_radius
    end_time = start_time + pi*sqrt(pow(r1+r2,3)/(8*mu))
    dv1 = sqrt(mu/r1)*(sqrt(2*r2/(r1+r2))-1)
    dv2 = sqrt(mu/r2)*(1-sqrt(2*r1/(r1+r2)))
    node1 = vessel.control.add_node(start_time, prograde=dv1)
    node2 = vessel.control.add_node(start_time + 1000, prograde=dv2)
    nodes = (node1, node2)
    return nodes

def goodbye():
    update_UI('Nodes added. Burn safe!')
    time.sleep(3)
    return

# main loop
if __name__ == "__main__":

    check_initial_orbit()

    Hohmann_nodes(200*1000, ut() + vessel.orbit.time_to_apoapsis)

    goodbye()
