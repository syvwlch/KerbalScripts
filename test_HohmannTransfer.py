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
            'Expected zero phase when orbits are identical.',)

        self.assertAlmostEqual(
            ht.Hohmann_phase_angle(SEMI_MAJOR_AXIS, 3*SEMI_MAJOR_AXIS),
            ht.Hohmann_phase_angle(SEMI_MAJOR_AXIS/3, SEMI_MAJOR_AXIS),
            2,
            'Expected same result for given ratio of Semi Major Axis.')

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


if __name__ == '__main__':
    unittest.main()
