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

def Hohmann_transfer_time(a1,a2):
    mu = vessel.orbit.body.gravitational_parameter
    transfer_time = pi*sqrt(pow(a1+a2,3)/(8*mu))
    return transfer_time

def Hohmann_phase_angle(a1,a2):
    mu = vessel.orbit.body.gravitational_parameter
    transfer_time = Hohmann_transfer_time(a1,a2)
    period = 2 * pi * sqrt(pow(a2,3)/mu)
    phase_angle = 180 - 360 * transfer_time / period
    return phase_angle

def time_to_longitude(target_longitude):
    # assumes circular, equatorial orbit
    # assumes orbit rotates faster than body being orbited
    phase_angle = vessel.flight(vessel.orbit.body.reference_frame).longitude - target_longitude
    a = vessel.orbit.semi_major_axis
    mu = vessel.orbit.body.gravitational_parameter
    period1 = 2 * pi * sqrt(pow(a,3)/mu)
    period2 = vessel.orbit.body.rotational_period
    period = (period1*period2)/(period1-period2)
    if period == 0:
        if phase_angle == 0:
            time_to_longitude = 0
        else:
            time_to_longitude = float('nan')
    else:
        time_to_longitude = phase_angle / 360 * period
    return time_to_longitude

def Hohmann_nodes(target_altitude,start_time):
    # parameters, assuming circular orbits
    mu = vessel.orbit.body.gravitational_parameter
    a1 = vessel.orbit.semi_major_axis
    a2 = target_altitude + vessel.orbit.body.equatorial_radius
    # setting up first maneuver
    dv1 = sqrt(mu/a1)*(sqrt(2*a2/(a1+a2))-1)
    node1 = vessel.control.add_node(start_time, prograde=dv1)
    # setting up second maneuver
    if dv1 > 0:
        transfer_time = node1.orbit.time_to_apoapsis
    else:
        transfer_time = node1.orbit.time_to_periapsis
    dv2 = sqrt(mu/a2)*(1-sqrt(2*a1/(a1+a2)))
    node2 = vessel.control.add_node(start_time + transfer_time, prograde=dv2)
    nodes = (node1, node2)
    update_UI('Phase angle change: %d' % (Hohmann_phase_angle(a1,a2) % 360))
    return nodes

def goodbye():
    # update_UI('Nodes added. Burn safe!')
    time.sleep(3)
    return

# main loop
if __name__ == "__main__":

    check_initial_orbit()

    Hohmann_nodes(2863330, ut() + 60)

    goodbye()
