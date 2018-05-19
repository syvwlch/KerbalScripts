"""
Unit test the HohmannTransfer module.

Work in progress.
"""

import unittest
from unittest.mock import patch
import HohmannTransfer as ht
import sys

#  Constants that come in handy during Hohmann transfers.
KERBIN_EQUATORIAL_RADIUS = 600000.0
KERBIN_SYNCHRONOUS_SEMI_MAJOR_AXIS = 3463334.1352937142
KERBIN_GRAVITATIONAL_PARAMETER = 3531600035840.0


class Test_environment(unittest.TestCase):
    """Test the environment to ensure it will match production."""

    def test_python_version(self):
        """Make sure the python version is 3.x."""
        if sys.version_info[0] < 3:
            raise Exception("Must be using Python 3.")


@patch('HohmannTransfer.conn')
class Test_check_initial_orbit(unittest.TestCase):
    """
    Test check_initial_orbit().

    Function checks that initial orbit eccentricity
    is below a threshold, which defaults to 0.01.

    Requires two patches:
        - server connection (for all tests)
        - logger (for one test)
    """

    def test_default_constant(self, mock_conn):
        """Test with max eccentricity."""
        max = ht.MAXIMUM_ECCENTRICITY
        self.assertGreaterEqual(max, 0)
        self.assertLess(max, 1)

    def test_zero_eccentricity(self, mock_conn):
        """Test with zero eccentricity."""
        mock_conn.space_center.active_vessel.orbit.eccentricity = 0
        self.assertTrue(ht.check_initial_orbit())

    def test_max_eccentricity(self, mock_conn):
        """Test with max eccentricity."""
        max = ht.MAXIMUM_ECCENTRICITY
        mock_conn.space_center.active_vessel.orbit.eccentricity = max
        self.assertTrue(ht.check_initial_orbit())

    @patch('HohmannTransfer.logger')
    def test_too_much_eccentricity(self, mock_logger, mock_conn):
        """Test with too much eccentricity."""
        ERROR_MSG = 'Eccentricity too high for Hohmann transfers!'
        mock_conn.space_center.active_vessel.orbit.eccentricity = 1
        self.assertFalse(ht.check_initial_orbit())
        mock_logger.info.assert_called_once_with(ERROR_MSG)


class Test_phase_change(unittest.TestCase):
    """
    Test the phase_change() method of class HohmannTransfer.

    Method is expected to return the phase change
    during a Hohmann transfer.
    """

    def setUp(self):
        """Set up for this test case class."""
        self.MU = KERBIN_GRAVITATIONAL_PARAMETER
        self.SMA = KERBIN_SYNCHRONOUS_SEMI_MAJOR_AXIS
        self.PRECISION = 7

    def test_same_SMA(self):
        """Test with orbits with the same semi major axis."""
        transfer = ht.HohmannTransfer(self.SMA, self.SMA, self.MU)

        result = transfer.phase_change
        expected = 0.0
        fail_msg = 'Expected zero phase change for 1:1 SMAs ratio!'

        self.assertAlmostEqual(result, expected, self.PRECISION, fail_msg,)

    def test_same_SMA_ratio(self):
        """Test with pairs of orbits with the same ratio of semi major axis."""
        ratio = 2.5
        transfer1 = ht.HohmannTransfer(self.SMA, self.SMA*ratio, self.MU)
        transfer2 = ht.HohmannTransfer(self.SMA/ratio, self.SMA, self.MU)

        result = transfer1.phase_change
        expected = transfer2.phase_change
        fail_msg = 'Expected same phase change for same SMAs ratio!'

        self.assertAlmostEqual(result, expected, self.PRECISION, fail_msg,)

    def test_SMA_ratio_3(self):
        """Test with final orbit 3 times as high as initial orbit."""
        ratio = 3
        transfer = ht.HohmannTransfer(self.SMA, self.SMA*ratio, self.MU)

        result = transfer.phase_change
        expected = 82.0204102867
        fail_msg = 'Expected 82 degrees phase change for 1:3 SMAs ratio!'

        self.assertAlmostEqual(result, expected, self.PRECISION, fail_msg,)

    def test_SMA_ratio_half(self):
        """Test with final orbit half as high as initial orbit."""
        ratio = 0.5
        transfer = ht.HohmannTransfer(self.SMA, self.SMA*ratio, self.MU)

        result = transfer.phase_change
        expected = -150.68111527572904
        fail_msg = 'Expected -151 degrees phase change for 2:1 SMAs ratio!'

        self.assertAlmostEqual(result, expected, self.PRECISION, fail_msg,)


class Test_time_to_phase(unittest.TestCase):
    """
    Test time_to_phase().

    Function is expected to return the time it will take
    for the phase angle to change by the given value,
    with the two orbital periods given.
    """

    def test_same_period(self):
        """Test with the same orbital period."""
        PHASE_ANGLE = 33.2
        PERIOD = 12964.12
        with self.assertRaises(ValueError):
            ht.time_to_phase(PHASE_ANGLE, PERIOD, PERIOD)

    def test_both_periods_zero(self):
        """
        Test with both periods equal to zero.

        Expected to raise a ValueError if both periods are zero,
        and otherwise to:
        1. use the relative period if both periods are non zero, or
        2. use the non-zero period if one period is zero.
        """
        PHASE_ANGLE = 33.2
        with self.assertRaises(ValueError):
            ht.time_to_phase(PHASE_ANGLE, 0, 0)

    def test_one_period_zero(self):
        """Test with exactly one period equal to zero."""
        PERIOD = 100
        with self.subTest('Test 90 degree phase with 1:0 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(90, PERIOD, 0), PERIOD/4, 2)

        with self.subTest('Test 90 degree phase with 0:1 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(90, 0, PERIOD), PERIOD/4, 2)

    def test_integer_arguments(self):
        """Test with only integers as arguments."""
        PHASE_ANGLE = 57
        PERIOD1 = 1986
        PERIOD2 = 5874
        self.assertAlmostEqual(
            ht.time_to_phase(PHASE_ANGLE, PERIOD1, PERIOD2),
            ht.time_to_phase(float(PHASE_ANGLE),
                             float(PERIOD1),
                             float(PERIOD2),),
            2,
            'Expected same results when passing in integers.')

    def test_zero_phase(self):
        """Test with phase angle zero."""
        PERIOD = 100
        with self.subTest('Test zero phase with 2:1 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(0, 2*PERIOD, PERIOD), 0, 2)

        with self.subTest('Test zero phase with 1:2 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(0, PERIOD, 2*PERIOD), 0, 2)

    def test_180_phase(self):
        """Test with 180 degrees phase angle."""
        PERIOD = 100
        with self.subTest('Test 180 degree phase with 2:1 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(180, 2*PERIOD, PERIOD), PERIOD, 2)

        with self.subTest('Test 180 degree phase with 1:2 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(180, PERIOD, 2*PERIOD), PERIOD, 2)

    def test_90_phase(self):
        """Test with 90 degrees phase angle."""
        PERIOD = 100
        with self.subTest('Test 90 degree phase with 2:1 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(90, 2*PERIOD, PERIOD), PERIOD/2, 2)

        with self.subTest('Test 90 degree phase with 1:2 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(90, PERIOD, 2*PERIOD), 3*PERIOD/2, 2)

    def test_270_phase(self):
        """Test with 270 & -90 degrees phase angle."""
        PERIOD = 100
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

    def test_clamped_phase(self):
        """Test with phase greater than 360 degrees."""
        PERIOD = 100
        with self.subTest('Test 3690 degree phase with 2:1 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(3690, 2*PERIOD, PERIOD), PERIOD/2, 2)

        with self.subTest('Test 3690 degree phase with 1:2 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(3690, PERIOD, 2*PERIOD), 3*PERIOD/2, 2)

        with self.subTest('Test -3510 degree phase with 2:1 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(-3510, 2*PERIOD, PERIOD), PERIOD/2, 2)

        with self.subTest('Test -3510 degree phase with 1:2 period ratio.'):
            self.assertAlmostEqual(
                ht.time_to_phase(-3510, PERIOD, 2*PERIOD), 3*PERIOD/2, 2)


if __name__ == '__main__':
    unittest.main()
