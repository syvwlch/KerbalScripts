"""
This adds two nodes for a Hohmann transfer maneuver.

Currently assumes circular orbits, especially at the start!
Nodes can be execute manually or with Node Executor script running in parallel.
"""

from math import pi, sqrt, pow
import InitialSetUp

#  Logger setup
MODULE_HANDLE = 'HohmannTransfer'
logger = InitialSetUp.set_up_logger(MODULE_HANDLE + '.log')

#  KRPC server connection
try:
    conn = InitialSetUp.connect_to_krpc_server(MODULE_HANDLE)
except ConnectionRefusedError:
    logger.critical('Connection refused.')
    logger.critical('Please check that KRPC server is running in KSP.')
    conn = None

#  Constants that come in handy during Hohmann transfers.
KSC_LONGITUDE = 285.425
MAXIMUM_ECCENTRICITY = 0.01


def check_initial_orbit(maximum_eccentricity=MAXIMUM_ECCENTRICITY):
    """Check how circular the current orbit is."""
    eccentricity = conn.space_center.active_vessel.orbit.eccentricity
    if eccentricity > maximum_eccentricity:
        logger.info('Eccentricity too high for Hohmann transfers!')
        return False
    return True


def time_to_phase(phase_angle, period1, period2):
    """Calculate how long to wait for a particular phase angle change."""
    def clamp_time_to_period(phase_angle, period):
        """Clamp a phase angle to the interval between zero and abs(period)."""
        result = phase_angle / 360 * period
        while result < 0:
            result = result + abs(period)
        while result > abs(period):
            result = result - abs(period)
        return result

    def relative_period(period1, period2):
        """Calculate the relative period between two periods."""
        if period1 == period2:
            raise ValueError(
                'There is no relative periods when periods are identical!')
        elif period1 == 0:
            period = period2
        elif period2 == 0:
            period = period1
        else:
            period = (period1*period2)/(period1-period2)
        return period

    return clamp_time_to_period(
        phase_angle,
        relative_period(period1, period2))


class HohmannTransfer:
    """
    General class for all Hohmann transfers.

    Will include methods for transfers to Keostationary orbits,
    orbital rendez-vous transfers, etc...
    """

    def __init__(self, initial_sma=1, target_sma=1, mu=1):
        """Set arguments directly."""
        self.initial_sma = initial_sma
        self.target_sma = target_sma
        self.mu = mu
        if mu*initial_sma*target_sma == 0:
            raise ValueError('Mu and semi major axes cannot be zero.')

    @property
    def initial_dV(self):
        """Set deltaV for the initial maneuver of a Hohmann transfer."""
        term_1 = sqrt(self.mu/self.initial_sma)
        term_2 = sqrt(2*self.target_sma/(self.initial_sma+self.target_sma))
        return term_1 * (term_2-1)

    @property
    def final_dV(self):
        """Set deltaV for the final maneuver of a Hohmann transfer."""
        term_1 = sqrt(self.mu/self.target_sma)
        term_2 = sqrt(2*self.initial_sma/(self.initial_sma+self.target_sma))
        return term_1 * (1-term_2)

    @property
    def transfer_time(self):
        """Transit time for a Hohmann transfer."""
        term_1 = pi/sqrt(8*self.mu)
        term_2 = pow(self.initial_sma+self.target_sma, 3/2)
        return term_1 * term_2

    @property
    def phase_change(self):
        """Phase angle change during a Hohmann maneuver."""
        # Transfer orbit by construction has half of both orbit's SMAs
        transfer_sma = (self.initial_sma + self.target_sma)/2
        # From formula for orbital period, ratio is 3/2 power of SMA ratio
        orbital_period_ratio = pow(transfer_sma/self.target_sma, 3/2)
        # Transfer starts 180 degrees from target
        initial_phase_angle = 180
        # Transfer happens within half a transfer orbit
        transfer_phase_angle = 180 * orbital_period_ratio
        return initial_phase_angle - transfer_phase_angle

    def set_from_vessel(self, vessel):
        """Set mu & initial_sma from a vessel."""
        try:
            self.mu = vessel.orbit.body.gravitational_parameter
            self.initial_sma = vessel.orbit.semi_major_axis
        except AttributeError:
            raise('Could not get value from vessel.')

    def set_from_target(self, target):
        """Set mu & final_sma from a target, vessel or body."""
        try:
            self.mu = vessel.orbit.body.gravitational_parameter
            self.target_sma = target.orbit.semi_major_axis
        except AttributeError:
            print('Could not get value from target.')

    def set_from_body(self, body):
        """Set mu & target_sma for synchronous orbit around body."""
        try:
            self.mu = vessel.orbit.body.gravitational_parameter
            rotational_period = body.rotational_period
            self.target_sma = pow(self.mu*(rotational_period/(2*pi))**2, 1/3)
        except AttributeError:
            raise('Could not get value from body.')

    def add_nodes(self, vessel, time_to_start):
        """Add two maneuver nodes to vessel to set up transfer."""
        try:
            start_time = conn.space_center.ut + time_to_start
            stop_time = start_time + self.transfer_time
            vessel.control.add_node(start_time, prograde=self.initial_dV)
            vessel.control.add_node(stop_time, prograde=self.final_dV)
        except AttributeError:
            raise('Could not add nodes to vessel.')


#  If running as __main__ then rdv if there is a target,
#  or go to Keostationary if not.
if __name__ == "__main__":
    logger.info('Running HohmannTransfer as __main__.')
    if check_initial_orbit():
        if conn.space_center.target_vessel is None:
            # keostationary_transfer(KSC_LONGITUDE)
            vessel = conn.space_center.active_vessel
            body = vessel.orbit.body
            ht = HohmannTransfer()
            ht.set_from_vessel(vessel)
            ht.set_from_body(body)

            rotational_period = body.rotational_period
            rf = body.reference_frame
            current_phase = KSC_LONGITUDE - vessel.flight(rf).longitude
            transfer_phase = ht.phase_change
            time_to_transfer = time_to_phase(transfer_phase - current_phase,
                                             vessel.orbit.period,
                                             rotational_period,)

            ht.add_nodes(vessel, time_to_transfer)
        else:
            vessel = conn.space_center.active_vessel
            target = conn.space_center.target_vessel

            ht = HohmannTransfer()
            ht.set_from_vessel(vessel)
            ht.set_from_target(target)

            rf = vessel.orbit.body.reference_frame
            vessel_phase = vessel.flight(rf).longitude
            target_phase = target.flight(rf).longitude
            current_phase = target_phase - vessel_phase
            transfer_phase = ht.phase_change
            time_to_transfer = time_to_phase(transfer_phase - current_phase,
                                             vessel.orbit.period,
                                             target.orbit.period,)

            ht.add_nodes(vessel, time_to_transfer)
    logger.info('End of __main__.')
