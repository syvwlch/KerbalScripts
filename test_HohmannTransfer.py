"""
Unit test the HohmannTransfer module.

Work in progress.
"""

import unittest
from unittest.mock import patch
from math import pi
import sys
import HohmannTransfer


class Test_environment(unittest.TestCase):
    """Test the environment to ensure it will match production."""

    def test_python_version(self):
        """Make sure the python version is 3.x."""
        if sys.version_info[0] < 3:
            raise Exception("Must be using Python 3.")


class Test_HohmannTransfer_init(unittest.TestCase):
    """
    Test the HohmannTransfer class __ini__ method.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def test_no_krpc_connection(self):
        """Check that __init__ raises error without a KRPC server."""
        with self.assertRaises(ConnectionRefusedError):
            HohmannTransfer.HohmannTransfer()

    @patch('HohmannTransfer.krpc.connect')
    def test_krpc_connection(self, mock_conn):
        """Check that __init__ connects to KRPC server."""
        HohmannTransfer.HohmannTransfer()
        mock_conn.assert_called_once()

    @patch('HohmannTransfer.krpc.connect')
    def test_init_target_sma_no_karg(self, mock_conn):
        """Check that __init__ w/o karg sets target_sma to inital_sma."""
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 10
        transfer = HohmannTransfer.HohmannTransfer()
        self.assertEqual(transfer.target_sma, 10)

    @patch('HohmannTransfer.krpc.connect')
    def test_init_target_sma(self, mock_conn):
        """Check that __init__ with target_sma karg sets it."""
        transfer = HohmannTransfer.HohmannTransfer(target_sma=10)
        self.assertEqual(transfer.target_sma, 10)

    @patch('HohmannTransfer.krpc.connect')
    def test_init_delay_no_karg(self, mock_conn):
        """Check that __init__ w/o karg sets delay to zero."""
        transfer = HohmannTransfer.HohmannTransfer()
        self.assertEqual(transfer.delay, 0)

    @patch('HohmannTransfer.krpc.connect')
    def test_init_delay(self, mock_conn):
        """Check that __init__ with delay karg sets it."""
        transfer = HohmannTransfer.HohmannTransfer(delay=10)
        self.assertEqual(transfer.delay, 10)


@patch('HohmannTransfer.krpc.connect')
class Test_HohmannTransfer_ro_attributes(unittest.TestCase):
    """
    Test the HohmannTransfer class read-only attributes.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def test_initial_sma(self, mock_conn):
        """Check that inital_sma is set from active vessel."""
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 10
        transfer = HohmannTransfer.HohmannTransfer()
        self.assertEqual(transfer.initial_sma, 10)

    def test_transfer_sma(self, mock_conn):
        """Check that transfer_sma is the average of initial & target smas."""
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 10
        transfer = HohmannTransfer.HohmannTransfer()
        self.assertEqual(transfer.transfer_sma, 10)
        transfer.target_sma = 30
        self.assertEqual(transfer.transfer_sma, 20)

    def test_mu(self, mock_conn):
        """Check that gravitational parameter is set from active vessel."""
        mock_conn().space_center.active_vessel.orbit.body.gravitational_parameter = 10
        transfer = HohmannTransfer.HohmannTransfer()
        self.assertEqual(transfer.mu, 10)

    def test_initial_altitude(self, mock_conn):
        """Check that initial_altitude is set from active vessel."""
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 10
        mock_conn().space_center.active_vessel.orbit.body.equatorial_radius = 1
        transfer = HohmannTransfer.HohmannTransfer()
        self.assertEqual(transfer.initial_altitude, 9)

    def test_initial_dV(self, mock_conn):
        """Check that initial_dV is set from active vessel & target_sma."""
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 2
        mock_conn().space_center.active_vessel.orbit.body.gravitational_parameter = 8
        transfer = HohmannTransfer.HohmannTransfer()
        self.assertEqual(transfer.initial_dV, 0)
        transfer.target_sma = 16
        self.assertAlmostEqual(transfer.initial_dV, 2/3)

    def test_final_dV(self, mock_conn):
        """Check that final_dV is set from active vessel & target_sma."""
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 16
        mock_conn().space_center.active_vessel.orbit.body.gravitational_parameter = 8
        transfer = HohmannTransfer.HohmannTransfer()
        self.assertEqual(transfer.final_dV, 0)
        transfer.target_sma = 2
        self.assertAlmostEqual(transfer.final_dV, -2/3)

    def test_initial_period(self, mock_conn):
        """Check that initial_period is set from active vessel."""
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 4
        mock_conn().space_center.active_vessel.orbit.body.gravitational_parameter = 1
        transfer = HohmannTransfer.HohmannTransfer()
        self.assertAlmostEqual(transfer.initial_period, 16*pi)

    def test_transfer_period(self, mock_conn):
        """Check that transfer_period is set from active vessel & target_sma."""
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 2
        mock_conn().space_center.active_vessel.orbit.body.gravitational_parameter = 1
        transfer = HohmannTransfer.HohmannTransfer()
        transfer.target_sma = 6
        self.assertAlmostEqual(transfer.transfer_period, 16*pi)

    def test_transfer_time(self, mock_conn):
        """Check that transfer_time is set from active vessel & target_sma."""
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 2
        mock_conn().space_center.active_vessel.orbit.body.gravitational_parameter = 1
        transfer = HohmannTransfer.HohmannTransfer()
        transfer.target_sma = 6
        self.assertAlmostEqual(transfer.transfer_time, 8*pi)

    def test_relative_period(self, mock_conn):
        """Check that relative_period is set from active vessel & target_sma."""
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 4
        mock_conn().space_center.active_vessel.orbit.body.gravitational_parameter = 1
        transfer = HohmannTransfer.HohmannTransfer()
        transfer.target_sma = 9
        self.assertAlmostEqual(transfer.relative_period, pi*16*54/(16-54))

    def test_initial_phase(self, mock_conn):
        """Check that initial_phase is set from active vessel."""
        mock_conn().space_center.active_vessel.flight().longitude = 20
        transfer = HohmannTransfer.HohmannTransfer()
        self.assertEqual(transfer.initial_phase, 20)

    def test_phase_change(self, mock_conn):
        """Check that phase_change is set from active vessel & target_sma."""
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 2
        mock_conn().space_center.active_vessel.orbit.body.gravitational_parameter = 1
        transfer = HohmannTransfer.HohmannTransfer()
        self.assertEqual(transfer.phase_change, 0)
        transfer.target_sma = 3
        self.assertAlmostEqual(transfer.phase_change, 43.0693606237085)


@patch('HohmannTransfer.krpc.connect')
class Test_HohmannTransfer_rw_attributes(unittest.TestCase):
    """
    Test the HohmannTransfer class read/write attributes.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def test_target_sma(self, mock_conn):
        """Check that target_sma can be set."""
        transfer = HohmannTransfer.HohmannTransfer()
        transfer.target_sma = 10
        self.assertEqual(transfer.target_sma, 10)

    def test_delay(self, mock_conn):
        """Check that target_sma can be set."""
        transfer = HohmannTransfer.HohmannTransfer()
        transfer.delay = 10
        self.assertEqual(transfer.delay, 10)

    def test_target_altitude(self, mock_conn):
        """Check that target_altitude sets target_sma."""
        mock_conn().space_center.active_vessel.orbit.body.equatorial_radius = 1
        transfer = HohmannTransfer.HohmannTransfer()
        transfer.target_altitude = 10
        self.assertEqual(transfer.target_altitude, 10)
        self.assertEqual(transfer.target_sma, 11)

    def test_target_period(self, mock_conn):
        """Check that target_period sets target_sma."""
        mock_conn().space_center.active_vessel.orbit.body.gravitational_parameter = 1
        transfer = HohmannTransfer.HohmannTransfer()
        transfer.target_period = 16*pi
        self.assertAlmostEqual(transfer.target_period, 16*pi)
        self.assertAlmostEqual(transfer.target_sma, 4)

    @unittest.expectedFailure
    def test_target_phase(self, mock_conn):
        """Check that target_phase sets delay."""
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 2
        mock_conn().space_center.active_vessel.orbit.body.gravitational_parameter = 1
        mock_conn().space_center.active_vessel.flight().longitude = 20
        transfer = HohmannTransfer.HohmannTransfer()
        transfer.target_sma = 3
        line = f'Old: {transfer.delay:5.1f} '
        transfer.target_phase = 10
        line += f'New: {transfer.delay:5.1f}\n'
        print(line)
        self.assertAlmostEqual(transfer.target_phase, 10)
        self.assertAlmostEqual(transfer.delay, 4)


@patch('HohmannTransfer.krpc.connect')
class Test_HohmannTransfer_private_methods(unittest.TestCase):
    """
    Test the HohmannTransfer class representations methods.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def test_period_from_sma(self, mock_conn):
        """Check that period_from_sma() works."""
        mock_conn().space_center.active_vessel.orbit.body.gravitational_parameter = 1
        transfer = HohmannTransfer.HohmannTransfer()
        self.assertAlmostEqual(transfer.period_from_sma(4), 16*pi)

    def test_sma_from_period(self, mock_conn):
        """Check that sma_from_period() works."""
        mock_conn().space_center.active_vessel.orbit.body.gravitational_parameter = 1
        transfer = HohmannTransfer.HohmannTransfer()
        self.assertAlmostEqual(transfer.sma_from_period(16*pi), 4)

    def test_clamp_from_0_360(self, mock_conn):
        """Check that clamp_from_0_360() works."""
        mock_conn().space_center.active_vessel.orbit.body.gravitational_parameter = 1
        transfer = HohmannTransfer.HohmannTransfer()
        self.assertEqual(transfer.clamp_from_0_360(-10), 350)
        self.assertEqual(transfer.clamp_from_0_360(20), 20)
        self.assertEqual(transfer.clamp_from_0_360(395), 35)

    def test_str(self, mock_conn):
        """Check that the __str__() method works."""
        ESTR = 'Hohmann transfer from  1000 km altitude to 2000 km altitude:\n'
        ESTR += '    1. Wait:       0 seconds to burn: 154.7 m/s prograde.\n'
        ESTR += '    2. Wait:    5771 seconds to burn: 129.8 m/s prograde.\n'
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 10**6
        mock_conn().space_center.active_vessel.orbit.body.gravitational_parameter = 10**12
        mock_conn().space_center.active_vessel.orbit.body.equatorial_radius = 1
        transfer = HohmannTransfer.HohmannTransfer()
        transfer.target_sma = 2*10**6
        tstr = str(transfer)
        self.assertEqual(tstr, ESTR)

    def test_repr(self, mock_conn):
        """Check that the __repr__() method works."""
        ESTR = 'HohmannTransfer(target_sma=2000000, delay=0)'
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 10**6
        mock_conn().space_center.active_vessel.orbit.body.gravitational_parameter = 10**12
        mock_conn().space_center.active_vessel.orbit.body.equatorial_radius = 1
        transfer = HohmannTransfer.HohmannTransfer()
        transfer.target_sma = 2*10**6
        tstr = repr(transfer)
        self.assertEqual(tstr, ESTR)


if __name__ == '__main__':
    unittest.main()
