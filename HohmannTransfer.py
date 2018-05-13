"""
This adds two nodes for a Hohmann transfer maneuver
Currently assumes circular orbits, especially at the start!

Nodes can be execute manually or with Node Executor script running in parallel
"""

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


def update_UI(message='...'):
    """Update terminal & UI with message at the same time."""
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


def check_initial_orbit(maximum_eccentricity=0.01, require_click=True):
    """Check how circular the current orbit is, and then wait for click."""
    if vessel.orbit.eccentricity > maximum_eccentricity:
        update_UI('Please circularize first!')
        while True:
            if vessel.orbit.eccentricity <= maximum_eccentricity:
                break
            time.sleep(0.1)

    # wait button click to launch
    if require_click:
        update_UI('Click to add nodes')
        button = panel.add_button("Add Nodes")
        button.rect_transform.size = (100, 30)
        button.rect_transform.position = (135, -20)
        button_clicked = conn.add_stream(getattr, button, 'clicked')
        while True:
            if button_clicked():
                button.clicked = False
                break
            time.sleep(0.1)
        button.remove()
    return


def Hohmann_phase_angle(a1, a2):
    """Calculate the phase angle change during a Hohmann maneuver."""
    return 180 - 90 * sqrt(pow((a1+a2)/a2, 3)/2)


def time_to_phase(phase_angle, period1, period2):
    """Calculate how long to wait for a particular phase angle change."""
    if period1 == period2:
        return float('nan')
    else:
        period = (period1*period2)/(period1-period2)
    if period == 0:
        if phase_angle == 0:
            return 0
        else:
            return float('nan')
    else:
        time = phase_angle / 360 * period
    while time < 0:
        time = time + abs(period)
    while time > abs(period):
        time = time - abs(period)
    return time


def time_to_longitude(target_longitude):
    """Calculate time to reach a certain longitude,
    assuming a circular, equatorial orbit"""
    return time_to_phase(
        vessel.flight(vessel.orbit.body.reference_frame).longitude - target_longitude,
        vessel.orbit.period,
        vessel.orbit.body.rotational_period)


def time_to_target_phase(target_phase):
    """Calculate time to reach a certain phase angle with the target,
    assuming there is a target selected, and that it orbits the same body"""
    rf = vessel.orbit.body.reference_frame
    target = conn.space_center.target_vessel
    return time_to_phase(
        vessel.flight(rf).longitude - target.flight(rf).longitude - target_phase,
        vessel.orbit.period,
        target.orbit.period)


def Hohmann_nodes(target_altitude, start_time):
    """Add two nodes to the current vessel's flight plan,
    to set up a Hohmann maneuver for a given altitude,
    starting at a give future time, and assuming circular orbits."""
    mu = vessel.orbit.body.gravitational_parameter
    a1 = vessel.orbit.semi_major_axis
    a2 = target_altitude + vessel.orbit.body.equatorial_radius
    # setting up first maneuver
    dv1 = sqrt(mu/a1)*(sqrt(2*a2/(a1+a2))-1)
    node1 = vessel.control.add_node(start_time, prograde=dv1)
    # setting up second maneuver
    # measuring, rather than calculating
    if dv1 > 0:
        transfer_time = node1.orbit.time_to_apoapsis
    else:
        transfer_time = node1.orbit.time_to_periapsis
    dv2 = sqrt(mu/a2)*(1-sqrt(2*a1/(a1+a2)))
    node2 = vessel.control.add_node(start_time + transfer_time, prograde=dv2)
    nodes = (node1, node2)
    return nodes


def Keostationary(longitude):
    """Set up a Hohmann maneuver, to put current vessel
    in Keostationary orbit around Kerbin.
    Currently hardcoded for Kerbin's syncronous orbit altitude."""
    a1 = vessel.orbit.semi_major_axis
    a2 = 2863330 + vessel.orbit.body.equatorial_radius
    target_longitude = longitude - Hohmann_phase_angle(a1, a2)
    Hohmann_nodes(
        2863330,
        ut() + time_to_longitude(target_longitude))
    return


def rendez_vous():
    """Set up a Hohmann maneuver, to rendez-vous current vessel with current target.
    Assumes there is a target selected, and that it orbits the same body."""
    target = conn.space_center.target_vessel
    a1 = vessel.orbit.semi_major_axis
    a2 = target.orbit.semi_major_axis
    Hohmann_nodes(
        target.orbit.apoapsis_altitude,
        ut() + time_to_target_phase(-Hohmann_phase_angle(a1, a2)))
    return


def goodbye():
    """End script politely."""
    update_UI('Nodes added. Burn safe!')
    time.sleep(3)
    return


# main loop
if __name__ == "__main__":

    check_initial_orbit()

    Keostationary(285.425)  # right over the KSC
    # rendez_vous() # needs a target set first!
    # Hohmann_nodes(6060829,ut()+60*13)

    goodbye()
