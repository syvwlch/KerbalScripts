"""Unit test the HohmannTransfer class."""

import unittest
from unittest.mock import patch, call
from math import pi
import sys
from HohmannTransfer import HohmannTransfer


class Test_environment(unittest.TestCase):
    """Test the environment to ensure it will match production."""

    def test_python_version(self):
        """Make sure the python version is 3.x."""
        self.assertGreaterEqual(sys.version_info[0], 3)


class Test_HohmannTransfer_init(unittest.TestCase):
    """
    Test the HohmannTransfer class __ini__ method.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def test_no_krpc_connection(self):
        """Server unreachable should raise ConnectionRefusedError."""
        try:
            HohmannTransfer()
        except Exception as e:
            self.assertIsInstance(e, ConnectionRefusedError)
        return

    @patch('krpc.connect', spec=True)
    def test_krpc_connection(self, mock_conn):
        """Check that __init__ connects to KRPC server."""
        HohmannTransfer()

        mock_conn.assert_called_once_with(name='HohmannTransfer')

    @patch('krpc.connect', spec=True)
    def test_init_target_sma_no_karg(self, mock_conn):
        """Check that __init__ w/o karg sets target_sma to inital_sma."""
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 10

        transfer = HohmannTransfer()

        self.assertEqual(transfer.target_sma, 10)

    @patch('krpc.connect', spec=True)
    def test_init_target_sma(self, mock_conn):
        """Check that __init__ with target_sma karg sets it."""
        transfer = HohmannTransfer(target_sma=10)

        self.assertEqual(transfer.target_sma, 10)

    @patch('krpc.connect', spec=True)
    def test_init_delay_no_karg(self, mock_conn):
        """Check that __init__ w/o karg sets delay to zero."""
        transfer = HohmannTransfer()

        self.assertEqual(transfer.delay, 0)

    @patch('krpc.connect', spec=True)
    def test_init_delay(self, mock_conn):
        """Check that __init__ with delay karg sets it."""
        transfer = HohmannTransfer(delay=10)

        self.assertEqual(transfer.delay, 10)


@patch('krpc.connect', spec=True)
class Test_HohmannTransfer_ro_attributes(unittest.TestCase):
    """
    Test the HohmannTransfer class read-only attributes.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def test_initial_sma(self, mock_conn):
        """Check that inital_sma is set from active vessel."""
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 10

        transfer = HohmannTransfer()

        self.assertEqual(transfer.initial_sma, 10)

    def test_transfer_sma(self, mock_conn):
        """Check that transfer_sma is the average of initial & target smas."""
        mock_conn().space_center.active_vessel.orbit.semi_major_axis = 10

        transfer = HohmannTransfer(target_sma=30)

        self.assertEqual(transfer.transfer_sma, 20)

    def test_mu(self, mock_conn):
        """Check that gravitational parameter is set from active vessel."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.body.gravitational_parameter = 10

        transfer = HohmannTransfer()

        self.assertEqual(transfer.mu, 10)

    def test_initial_altitude(self, mock_conn):
        """Check that initial_altitude is set from active vessel."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.semi_major_axis = 10
        vessel.orbit.body.equatorial_radius = 1

        transfer = HohmannTransfer()

        self.assertEqual(transfer.initial_altitude, 9)

    def test_initial_dV(self, mock_conn):
        """Check that initial_dV is set from active vessel & target_sma."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.semi_major_axis = 2
        vessel.orbit.body.gravitational_parameter = 8

        transfer = HohmannTransfer(target_sma=16)

        self.assertAlmostEqual(transfer.initial_dV, 2/3)

    def test_final_dV(self, mock_conn):
        """Check that final_dV is set from active vessel & target_sma."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.semi_major_axis = 16
        vessel.orbit.body.gravitational_parameter = 8

        transfer = HohmannTransfer(target_sma=2)

        self.assertAlmostEqual(transfer.final_dV, -2/3)

    def test_initial_period(self, mock_conn):
        """Check that initial_period is set from active vessel."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.semi_major_axis = 4
        vessel.orbit.body.gravitational_parameter = 1

        transfer = HohmannTransfer()

        self.assertAlmostEqual(transfer.initial_period, 16*pi)

    def test_transfer_period(self, mock_conn):
        """Should set transfer_period from active vessel & target_sma."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.semi_major_axis = 2
        vessel.orbit.body.gravitational_parameter = 1

        transfer = HohmannTransfer(target_sma=6)

        self.assertAlmostEqual(transfer.transfer_period, 16*pi)

    def test_transfer_time(self, mock_conn):
        """Should set transfer_time from active vessel & target_sma."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.semi_major_axis = 2
        vessel.orbit.body.gravitational_parameter = 1

        transfer = HohmannTransfer(target_sma=6)

        self.assertAlmostEqual(transfer.transfer_time, 8*pi)

    def test_relative_period(self, mock_conn):
        """Should set relative_period from active vessel & target_sma."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.semi_major_axis = 4
        vessel.orbit.body.gravitational_parameter = 1

        transfer = HohmannTransfer(target_sma=9)

        self.assertAlmostEqual(transfer.relative_period, pi*16*54/(16-54))

    def test_initial_phase(self, mock_conn):
        """Check that initial_phase is set from active vessel."""
        mock_conn().space_center.active_vessel.flight().longitude = 20

        transfer = HohmannTransfer()

        self.assertEqual(transfer.initial_phase, 20)

    def test_phase_change(self, mock_conn):
        """Check that phase_change is set from active vessel & target_sma."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.semi_major_axis = 2
        vessel.orbit.body.gravitational_parameter = 1

        transfer = HohmannTransfer(target_sma=3)

        self.assertAlmostEqual(transfer.phase_change, 43.0693606237085)


@patch('krpc.connect', spec=True)
class Test_HohmannTransfer_rw_attributes(unittest.TestCase):
    """
    Test the HohmannTransfer class read/write attributes.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def test_target_sma(self, mock_conn):
        """Check that target_sma can be set."""
        transfer = HohmannTransfer()
        transfer.target_sma = 10

        self.assertEqual(transfer.target_sma, 10)

    def test_delay(self, mock_conn):
        """Check that target_sma can be set."""
        transfer = HohmannTransfer()
        transfer.delay = 10

        self.assertEqual(transfer.delay, 10)

    def test_target_altitude(self, mock_conn):
        """Check that target_altitude sets target_sma."""
        mock_conn().space_center.active_vessel.orbit.body.equatorial_radius = 1

        transfer = HohmannTransfer()
        transfer.target_altitude = 10

        self.assertEqual(transfer.target_altitude, 10)
        self.assertEqual(transfer.target_sma, 11)

    def test_target_period(self, mock_conn):
        """Check that target_period sets target_sma."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.body.gravitational_parameter = 1

        transfer = HohmannTransfer()
        transfer.target_period = 16*pi

        self.assertAlmostEqual(transfer.target_period, 16*pi)
        self.assertAlmostEqual(transfer.target_sma, 4)

    def test_target_phase(self, mock_conn):
        """Check that target_phase sets itself (clamped) as well as delay."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.semi_major_axis = 2
        vessel.orbit.body.gravitational_parameter = 1
        vessel.flight().longitude = 10

        transfer = HohmannTransfer(target_sma=3)

        target_phase_baseline = transfer.initial_phase + transfer.phase_change
        with self.subTest('Target already in position.'):
            transfer.target_phase = target_phase_baseline
            self.assertAlmostEqual(transfer.target_phase,
                                   target_phase_baseline)
            self.assertAlmostEqual(transfer.delay,
                                   0)
        with self.subTest('Target 90 degrees ahead.'):
            transfer.target_phase = 90 + target_phase_baseline
            self.assertAlmostEqual(transfer.target_phase,
                                   90 + target_phase_baseline)
            self.assertAlmostEqual(transfer.delay,
                                   0.25 * abs(transfer.relative_period))
        with self.subTest('Target 90 degrees behind.'):
            transfer.target_phase = -90 + target_phase_baseline
            self.assertAlmostEqual(transfer.target_phase,
                                   270 + target_phase_baseline)
            self.assertAlmostEqual(transfer.delay,
                                   0.75 * abs(transfer.relative_period))
        with self.subTest('Target a full turn & a third degrees ahead.'):
            transfer.target_phase = 480 + target_phase_baseline
            self.assertAlmostEqual(transfer.target_phase,
                                   120 + target_phase_baseline)
            self.assertAlmostEqual(transfer.delay,
                                   1/3 * abs(transfer.relative_period))


@patch('krpc.connect', spec=True)
class Test_HohmannTransfer_private_methods(unittest.TestCase):
    """
    Test the HohmannTransfer class representations methods.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def test_period_from_sma(self, mock_conn):
        """Check that period_from_sma() works."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.body.gravitational_parameter = 1

        transfer = HohmannTransfer()

        self.assertAlmostEqual(transfer.period_from_sma(4), 16*pi)

    def test_sma_from_period(self, mock_conn):
        """Check that sma_from_period() works."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.body.gravitational_parameter = 1

        transfer = HohmannTransfer()

        self.assertAlmostEqual(transfer.sma_from_period(16*pi), 4)

    def test_clamp_to(self, mock_conn):
        """Check that clamp_to() works."""
        transfer = HohmannTransfer()

        self.assertEqual(transfer.clamp_to(-10, 360), 350)
        self.assertEqual(transfer.clamp_to(20, 360), 20)
        self.assertEqual(transfer.clamp_to(390, 360), 30)

    def test_str(self, mock_conn):
        """Check that the __str__() method works."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.semi_major_axis = 10**6
        vessel.orbit.body.gravitational_parameter = 10**12
        vessel.orbit.body.equatorial_radius = 1

        actual_str = str(HohmannTransfer(target_sma=2*10**6))

        expect_str = 'Hohmann transfer from  1000 km altitude to '
        expect_str += '2000 km altitude:\n'
        expect_str += '    1. Wait:       0 seconds to burn: '
        expect_str += '154.7 m/s prograde.\n'
        expect_str += '    2. Wait:    5771 seconds to burn: '
        expect_str += '129.8 m/s prograde.\n'

        self.assertEqual(actual_str, expect_str)

    def test_repr(self, mock_conn):
        """Check that the __repr__() method works."""
        actual_str = repr(HohmannTransfer(target_sma=2000000.0, delay=100.0))

        expect_str = 'HohmannTransfer(target_sma=2000000.0, delay=100.0)'

        self.assertEqual(actual_str, expect_str)


@patch('krpc.connect', spec=True)
class Test_HohmannTransfer_use_cases(unittest.TestCase):
    """
    Test the HohmannTransfer class use case methods.

    Requires a patch on the KRPC server connection for:
        - active vessel
        - target vessel
        - universal time
    """

    def test_transfer_to_rendezvous_no_target(self, mock_conn):
        """Should warn but not raise AttributeError w/o target."""
        mock_conn().space_center.target_vessel = None

        transfer = HohmannTransfer()

        with self.subTest('Does not raise AttributeError'):
            with patch('sys.stdout') as mock_stdout:
                try:
                    transfer.transfer_to_rendezvous()
                except AttributeError:
                    self.fail('Should have caught the AttributeError')

        calls = [call('No target found: transfer unchanged.')]
        with self.subTest('Writes warning to stdout'):
            mock_stdout.write.assert_has_calls(calls)

    def test_transfer_to_rendezvous(self, mock_conn):
        """Should set target_sma & delay with a target."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.semi_major_axis = 4
        vessel.orbit.body.gravitational_parameter = 1
        vessel.flight().longitude = 0

        target = mock_conn().space_center.target_vessel
        target.orbit.semi_major_axis = 9
        target.flight().longitude = 20

        transfer = HohmannTransfer()
        transfer.transfer_to_rendezvous()

        self.assertAlmostEqual(transfer.target_sma, 9)
        self.assertAlmostEqual(transfer.target_phase, 20)

    def test_transfer_to_synchronous_orbit(self, mock_conn):
        """Check transfer_to_synchronous_orbit sets target_sma."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.semi_major_axis = 4
        vessel.orbit.body.gravitational_parameter = 1
        vessel.orbit.body.rotational_period = 20

        transfer = HohmannTransfer()
        transfer.transfer_to_synchronous_orbit()

        self.assertAlmostEqual(transfer.target_period, 20)

    def test_add_nodes(self, mock_conn):
        """Should call KRPC's add_node() twice with the correct kargs."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.semi_major_axis = 2
        vessel.orbit.body.gravitational_parameter = 1
        mock_conn().space_center.ut = 0

        transfer = HohmannTransfer(target_sma=3)
        transfer.add_nodes()

        expect_calls = [call(prograde=transfer.initial_dV,
                             ut=0),
                        call(prograde=transfer.final_dV,
                             ut=transfer.transfer_time)]

        control = mock_conn().space_center.active_vessel.control
        control.add_node.assert_has_calls(expect_calls)


if __name__ == '__main__':
    unittest.main()
