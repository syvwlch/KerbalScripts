"""
Unit test the HohmannTransfer module.

Work in progress, currently does not have a stub for the KRPC server.
"""

import unittest
import HohmannTransfer as ht


class TestCalculationFunctions(unittest.TestCase):
    """Test those functions with only numbers as inputs and outputs."""

    def test_Hohmann_phase_angle(self):
        """Test the phase angle change during a Hohmann maneuver."""
        SEMI_MAJOR_AXIS = 164783

        self.assertAlmostEqual(
            ht.Hohmann_phase_angle(SEMI_MAJOR_AXIS, SEMI_MAJOR_AXIS),
            0.00,
            2,
            'Expected zero phase when orbits have same semi major axis.',)

        self.assertAlmostEqual(
            ht.Hohmann_phase_angle(SEMI_MAJOR_AXIS, 3*SEMI_MAJOR_AXIS),
            ht.Hohmann_phase_angle(SEMI_MAJOR_AXIS/3, SEMI_MAJOR_AXIS),
            2,
            'Expected same result for given ratio of semi major axis.')

        self.assertAlmostEqual(
            ht.Hohmann_phase_angle(SEMI_MAJOR_AXIS, 3*SEMI_MAJOR_AXIS),
            116.36,
            2,
            'Expected 116 degree phase change when final orbit is 3x.')

        self.assertAlmostEqual(
            ht.Hohmann_phase_angle(SEMI_MAJOR_AXIS, 0.5*SEMI_MAJOR_AXIS),
            -150.68,
            2,
            'Expected -151 degree phase change when final orbit is 0.5x.')

    def test_time_to_phase(self):
        """Test the time before a phase angle is reached."""
        PERIOD = 1000

        with self.assertRaises(ValueError) as context:
            ht.time_to_phase(33, PERIOD, PERIOD)
        self.assertEqual(
            context.exception.message,
            'Phase angle cannot change when periods are identical!',)

        with self.assertRaises(ValueError) as context:
            ht.time_to_phase(33, 0.0, PERIOD)
        self.assertEqual(
            context.exception.message,
            'Cannot calculate phase time when one period is zero!',)

        with self.assertRaises(ValueError) as context:
            ht.time_to_phase(33, PERIOD, 0.0)
        self.assertEqual(
            context.exception.message,
            'Cannot calculate phase time when one period is zero!',)

        self.assertAlmostEqual(
            ht.time_to_phase(0.0, 0.0, PERIOD),
            0.00,
            2,
            'Expected zero when phase angle and one period is zero.')

        self.assertAlmostEqual(
            ht.time_to_phase(180, 2*PERIOD, PERIOD),
            PERIOD,
            2,
            'Expected one orbital period to phase when period ratio is 2:1.')


if __name__ == '__main__':
    unittest.main()
