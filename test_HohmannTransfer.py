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
        SEMI_MAJOR_AXIS_1 = 100000

        self.assertAlmostEqual(
            ht.Hohmann_phase_angle(SEMI_MAJOR_AXIS_1, SEMI_MAJOR_AXIS_1),
            0.0,
            7,
            'Expected zero phase change when orbits are identical.',)


if __name__ == '__main__':
    unittest.main()
