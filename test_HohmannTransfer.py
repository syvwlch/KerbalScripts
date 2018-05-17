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

    def test_zeros_as_arguments(self):
        """
        Test with one or more arguments equal to zero.

        Expected to raise a ValueError if one or both periods are zero,
        but to return zero if phase angle is zero.
        Note that if all three arguments are zero, we run into the case
        where the periods are identical.
        """
        PHASE_ANGLE = 33.2
        PERIOD = 12964.12
        with self.subTest('Test 0:X:X.'):
            self.assertAlmostEqual(
                ht.time_to_phase(0, PERIOD, 2*PERIOD), 0, 2)

        with self.subTest('Test X:0:X.'):
            with self.assertRaises(ValueError):
                ht.time_to_phase(PHASE_ANGLE, 0, PERIOD)

        with self.subTest('Test X:X:0.'):
            with self.assertRaises(ValueError):
                ht.time_to_phase(PHASE_ANGLE, PERIOD, 0)

        with self.subTest('Test 0:0:X.'):
            self.assertAlmostEqual(
                ht.time_to_phase(0, 0, PERIOD), 0, 2)

        with self.subTest('Test X:0:0.'):
            with self.assertRaises(ValueError):
                ht.time_to_phase(PHASE_ANGLE, 0, 0)

        with self.subTest('Test 0:X:0.'):
            self.assertAlmostEqual(
                ht.time_to_phase(0, PERIOD, 0), 0, 2)

        with self.subTest('Test 0:0:0.'):
            with self.assertRaises(ValueError):
                ht.time_to_phase(0, 0, 0)

    def test_integer_arguments(self):
        """Test with only integers as arguments."""
        self.assertAlmostEqual(
            ht.time_to_phase(57, 1986, 5874),
            ht.time_to_phase(57.0, 1986.0, 5874.0),
            2,
            'Expected same results when passing in integers.')

    def test_some_expected_values(self):
        """Test with some know arg:result sets."""
        PERIOD = 100
        with self.subTest('Test 180 degree phase with 2:1 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(180, 2*PERIOD, PERIOD), PERIOD, 2)

        with self.subTest('Test 180 degree phase with 1:2 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(180, PERIOD, 2*PERIOD), PERIOD, 2)

        with self.subTest('Test 90 degree phase with 2:1 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(90, 2*PERIOD, PERIOD), PERIOD/2, 2)

        with self.subTest('Test 90 degree phase with 1:2 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(90, PERIOD, 2*PERIOD), 3*PERIOD/2, 2)

        with self.subTest('Test -90 degree phase with 2:1 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(-90, 2*PERIOD, PERIOD), 3*PERIOD/2, 2)

        with self.subTest('Test -90 degree phase with 1:2 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(-90, PERIOD, 2*PERIOD), PERIOD/2, 2)

        with self.subTest('Test 270 degree phase with 2:1 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(270, 2*PERIOD, PERIOD), 3*PERIOD/2, 2)

        with self.subTest('Test 270 degree phase with 1:2 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(270, PERIOD, 2*PERIOD), PERIOD/2, 2)

        with self.subTest('Test 3690 degree phase with 2:1 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(3690, 2*PERIOD, PERIOD), PERIOD/2, 2)

        with self.subTest('Test 3690 degree phase with 1:2 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(3690, PERIOD, 2*PERIOD), 3*PERIOD/2, 2)


if __name__ == '__main__':
    unittest.main()
