"""
Unit test the Launch class.

Full coverage achieved, refactoring for readability & efficiency ongoing.
"""

import unittest
from unittest.mock import patch, call
import sys
from Launcher import Launcher


class Test_environment(unittest.TestCase):
    """Test the environment to ensure it will match production."""

    def test_python_version(self):
        """Make sure the python version is 3.x."""
        self.assertGreaterEqual(sys.version_info[0], 3)


class Test_Launcher_init(unittest.TestCase):
    """
    Test the Launcher class __ini__ method.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def test_no_krpc_connection(self):
        """Server unreachable should raise ConnectionRefusedError."""
        try:
            Launcher(target_altitude=10)
        except Exception as e:
            self.assertIsInstance(e, ConnectionRefusedError)
        return

    @patch('krpc.connect', spec=True)
    def test_krpc_connection(self, mock_conn):
        """Check that __init__ connects to KRPC server."""
        Launcher(target_altitude=10)

        mock_conn.assert_called_once_with(name='Launcher')

    @patch('krpc.connect', spec=True)
    def test_init_without_arg(self, mock_conn):
        """Invoking w/o arg should raise TypeError."""
        try:
            Launcher()
        except Exception as e:
            self.assertIsInstance(e, TypeError)
        return

    @patch('krpc.connect', spec=True)
    def test_init_with_arg(self, mock_conn):
        """Invoking w/ arg should set altitude & default inclination."""
        capcom = Launcher(target_altitude=10)
        self.assertEqual(capcom.target_altitude, 10)
        self.assertEqual(capcom.target_inclination, 0)

    @patch('krpc.connect', spec=True)
    def test_init_with_optional_karg(self, mock_conn):
        """Invoking w/ karg should set altitude & inclination."""
        capcom = Launcher(target_altitude=10,
                          target_inclination=90)
        self.assertEqual(capcom.target_altitude, 10)
        self.assertEqual(capcom.target_inclination, 90)


@patch('krpc.connect', spec=True)
class Test_Launcher_private_methods(unittest.TestCase):
    """
    Test the Launcher class private methods.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def test__ascent_angle_manager(self, mock_conn):
        """Should set autopilot ascent angle from altitude."""
        capcom = Launcher(target_altitude=10)

        values = [[0, 90],
                  [1000, 90],
                  [1001, 80],
                  [25500, 40],
                  [50000, 0],
                  ]

        for altitude, ascent_angle in values:
            capcom._ascent_angle_manager(altitude=altitude)
            auto_pilot = mock_conn().space_center.active_vessel.auto_pilot
            self.assertAlmostEqual(auto_pilot.target_pitch, ascent_angle, 0)

    @patch('Launcher.time', spec=True)
    def test__auto_stage(self, mock_time, mock_conn):
        """Should return available_thrust, with side effect of staging."""
        capcom = Launcher(target_altitude=10)
        vessel = mock_conn().space_center.active_vessel
        control = vessel.control

        VALUES = [[95, False],
                  [89, True],
                  [50, True],
                  [25, True], ]

        for new_thrust, calls_made in VALUES:
            with self.subTest(f'thrust_ratio: {new_thrust}%'):
                mock_conn().reset_mock()
                mock_time.reset_mock()
                vessel.available_thrust = new_thrust
                self.assertEqual(capcom._auto_stage(100), new_thrust)
                if calls_made:
                    control.activate_next_stage.assert_called_once_with()
                    mock_time.sleep.assert_has_calls([call(0.1), call(0.1)])
                else:
                    mock_time.sleep.assert_not_called()

    def test__wait_to_go_around_again(self, mock_conn):
        """Check it calls time.sleep() for 10 ms."""
        capcom = Launcher(target_altitude=10)

        with patch('Launcher.time', spec=True) as mock_time:
            capcom._wait_to_go_around_again()
            mock_time.sleep.assert_called_once_with(0.01)

    def test___str__(self, mock_conn):
        """Check that the __str__() method works."""
        actual_str = str(Launcher(target_altitude=1000))
        expect_str = 'Will launch to 1.0km  '
        expect_str += 'and set up the circularization maneuver node.\n'
        self.assertEqual(actual_str, expect_str)

    def test___repr__(self, mock_conn):
        """Check that the __repr__() method works."""
        actual_str = repr(Launcher(target_altitude=10,
                                   target_inclination=20))
        expect_str = 'Launcher(target_altitude=10, '
        expect_str += 'target_inclination=20)'
        self.assertEqual(actual_str, expect_str)


@patch('krpc.connect', spec=True)
class Test_Launcher_public_methods(unittest.TestCase):
    """
    Test the Launcher class public methods.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def test_ignition(self, mock_conn):
        """Should engage autopilot, wait, & stage."""
        capcom = Launcher(target_altitude=10,
                          target_inclination=30)
        vessel = mock_conn().space_center.active_vessel
        vessel.control.sas = True
        vessel.control.rcs = True
        vessel.control.throttle = 0.0
        vessel.surface_reference_frame = 'RF'

        with patch('Launcher.time', spec=True) as mock_time:
            vessel.auto_pilot.engage.assert_not_called()
            vessel.control.activate_next_stage.assert_not_called()
            mock_time.sleep.assert_not_called()
            capcom.ignition()
            self.assertEqual(vessel.auto_pilot.target_pitch, 90)
            self.assertEqual(vessel.auto_pilot.target_heading, 90-30)
            self.assertEqual(vessel.auto_pilot.target_roll, 180)
            self.assertEqual(vessel.auto_pilot.reference_frame, 'RF')
            self.assertIs(vessel.control.sas, False)
            self.assertIs(vessel.control.rcs, False)
            self.assertAlmostEqual(vessel.control.throttle, 1.0)
            vessel.auto_pilot.engage.assert_called_once_with()
            vessel.control.activate_next_stage.assert_called_once_with()
            mock_time.sleep.assert_called_once_with(1)

    def test_ascent(self, mock_conn):
        """Should manage the ascent until apoapsis is reached."""
        def _80_once_then_100():
            yield 50
            while True:
                yield 100

        capcom = Launcher(target_altitude=80)
        mock_conn().stream().__enter__().side_effect = _80_once_then_100()
        vessel = mock_conn().space_center.active_vessel
        vessel.control.throttle = 1.0
        vessel.available_thrust = 20

        with patch.object(Launcher, '_ascent_angle_manager'), \
                patch.object(Launcher, '_auto_stage'), \
                patch.object(Launcher, '_wait_to_go_around_again'):
            capcom.ascent()
            capcom._ascent_angle_manager.assert_called_once_with(100)
            capcom._auto_stage.assert_called_once_with(20)
            capcom._wait_to_go_around_again.assert_called_once_with()
            self.assertAlmostEqual(vessel.control.throttle, 0.0)

    def test_setup_circularization(self, mock_conn):
        """Should add the circularization maneuver node."""
        vessel = mock_conn().space_center.active_vessel
        vessel.orbit.body.gravitational_parameter = 1
        vessel.orbit.apoapsis = 200
        vessel.orbit.semi_major_axis = 100
        mock_conn().space_center.ut = 10
        vessel.orbit.time_to_apoapsis = 20
        capcom = Launcher(target_altitude=200)
        capcom.setup_circularization()
        vessel.control.add_node.assert_called_once()
        args, kargs = vessel.control.add_node.call_args
        self.assertEqual(args, (30,))
        self.assertAlmostEqual(kargs['prograde'], 0.0707, 4)

    def test_execute_launch(self, mock_conn):
        """Should run ignition, ascent and setup_circularization."""
        capcom = Launcher(target_altitude=10)
        with patch.object(Launcher, 'ignition'), \
                patch.object(Launcher, 'ascent'), \
                patch.object(Launcher, 'setup_circularization'):
            capcom.execute_launch()
            capcom.ignition.assert_called_once_with()
            capcom.ascent.assert_called_once_with()
            capcom.setup_circularization.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
