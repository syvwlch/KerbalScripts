"""
Unit test the HohmannTransfer module.

Work in progress, currently does not have a stub for the KRPC server.
"""

import unittest
import HohmannTransfer as ht
import sys


class Test_environment(unittest.TestCase):
    """Test the environment to ensure it will match production."""

    def test_python_version(self):
        """Make sure the python version is 3.x."""
        if sys.version_info[0] < 3:
            raise Exception("Must be using Python 3.")


class Test_Hohmann_phase_angle(unittest.TestCase):
    """
    Test Hohmann_phase_angle().

    Function is expected to return the phase angle change
    during a Hohmann transfer.
    """

    def test_same_SMA(self):
        """Test with orbits with the same semi major axis."""
        SEMI_MAJOR_AXIS = 14253.1
        self.assertAlmostEqual(
            ht.Hohmann_phase_angle(SEMI_MAJOR_AXIS, SEMI_MAJOR_AXIS),
            0.0,
            2,
            'Expected zero phase.',)

    def test_same_SMA_ratio(self):
        """Test with pairs of orbits with same ratio of semi major axis."""
        SEMI_MAJOR_AXIS = 14253.1
        self.assertAlmostEqual(
            ht.Hohmann_phase_angle(SEMI_MAJOR_AXIS, 3*SEMI_MAJOR_AXIS),
            ht.Hohmann_phase_angle(SEMI_MAJOR_AXIS/3, SEMI_MAJOR_AXIS),
            2,
            'Expected same result.')

    def test_SMA_ratio_3(self):
        """Test with final orbit 3 times as high as initial orbit."""
        SEMI_MAJOR_AXIS = 14253.1
        self.assertAlmostEqual(
            ht.Hohmann_phase_angle(SEMI_MAJOR_AXIS, 3*SEMI_MAJOR_AXIS),
            82.02,
            2,
            'Expected 82 degree phase change.')

    def test_SMA_ratio_half(self):
        """Test with final orbit half as high as initial orbit."""
        SEMI_MAJOR_AXIS = 14253.1
        self.assertAlmostEqual(
            ht.Hohmann_phase_angle(SEMI_MAJOR_AXIS, 0.5*SEMI_MAJOR_AXIS),
            -150.68,
            2,
            'Expected -151 degree phase change.')


class Test_time_to_phase(unittest.TestCase):
    """
    Test time_to_phase().

    Function is expected to return the time it will take
    for the phase angle to change by the given value,
    with the two orbital periods given.
    """

    def test_same_period(self):
        """Test with the same orbital period."""
        PERIOD = 12964.12

        with self.assertRaises(ValueError):
            ht.time_to_phase(33, PERIOD, PERIOD)

    def test_period_zero(self):
        """Test with one or both periods equal to zero."""
        PERIOD = 12964.12
        with self.assertRaises(ValueError):
            ht.time_to_phase(33, 0, PERIOD)

        with self.assertRaises(ValueError):
            ht.time_to_phase(33, PERIOD, 0)

        with self.assertRaises(ValueError):
            ht.time_to_phase(33, 0, 0)

        self.assertAlmostEqual(
            ht.time_to_phase(0.0, 0.0, PERIOD),
            0,
            2,
            'Expected zero when phase angle and one period is zero.')

    def test_period_ratio_2(self):
        """Test with ratio of periods equal to 2."""
        PERIOD = 12964.12
        self.assertAlmostEqual(
            ht.time_to_phase(180.0, 2*PERIOD, PERIOD),
            PERIOD,
            2,
            'Expected one orbital period to phase 180 degrees.')

    def test_integer_arguments(self):
        """Test with only integers as arguments."""
        self.assertAlmostEqual(
            ht.time_to_phase(180, 2000, 1000),
            ht.time_to_phase(180.0, 2000.0, 1000.0),
            2,
            'Expected same results when passing in integers.')


if __name__ == '__main__':
    unittest.main()
