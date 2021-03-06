"""
Unit test the NodeExecutor class.

Full coverage achieved, refactoring for readability & efficiency ongoing.
"""

import unittest
from unittest.mock import patch, call
from collections import namedtuple
import sys
from NodeExecutor import NodeExecutor


class Test_environment(unittest.TestCase):
    """Test the environment to ensure it will match production."""

    def test_python_version(self):
        """Make sure the python version is 3.x."""
        self.assertGreaterEqual(sys.version_info[0], 3)


class Test_NodeExecutor_init(unittest.TestCase):
    """
    Test the NodeExecutor class __ini__ method.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def test_no_krpc_connection(self):
        """Server unreachable should raise ConnectionRefusedError."""
        try:
            NodeExecutor()
        except Exception as e:
            self.assertIsInstance(e, ConnectionRefusedError)
        return

    @patch('krpc.connect', spec=True)
    def test_krpc_connection(self, mock_conn):
        """Check that __init__ connects to KRPC server."""
        NodeExecutor()
        mock_conn.assert_called_once_with(name='NodeExecutor')

    @patch('krpc.connect', spec=True)
    def test_init_minimum_burn_duration_no_karg(self, mock_conn):
        """Check that __init__ w/o karg sets minimum_burn_duration to 4."""
        Hal9000 = NodeExecutor()
        self.assertEqual(Hal9000.minimum_burn_duration, 4)

    @patch('krpc.connect', spec=True)
    def test_init_minimum_burn_duration(self, mock_conn):
        """Check that __init__ with minimum_burn_duration karg sets it."""
        Hal9000 = NodeExecutor(minimum_burn_duration=10)
        self.assertEqual(Hal9000.minimum_burn_duration, 10)

    @patch('krpc.connect', spec=True)
    def test_init_minimum_burn_duration_negative_value(self, mock_conn):
        """Negative value for karg should raise AssertionError."""
        try:
            NodeExecutor(minimum_burn_duration=-10)
        except Exception as e:
            self.assertIsInstance(e, AssertionError)
        return


@patch('krpc.connect', spec=True)
class Test_NodeExecutor_ro_attributes(unittest.TestCase):
    """
    Test the NodeExecutor class read-only attributes.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def setUp(self):
        """Set up the mock objects."""
        node = namedtuple('node', 'delta_v ut')
        self.NODE0 = node(delta_v=10, ut=20)
        self.NODE1 = node(delta_v=30, ut=40)

        self.CONN_ATTR0 = {
            'space_center.active_vessel.control.nodes': (self.NODE0,
                                                         self.NODE1),
            'space_center.active_vessel.available_thrust': 100,
            'space_center.active_vessel.specific_impulse': 200,
            'space_center.active_vessel.mass': 300,
            'space_center.ut': 1980}

        self.CONN_ATTR1 = {
            'space_center.active_vessel.control.nodes': (self.NODE1,),
            'space_center.active_vessel.available_thrust': 200000,
            'space_center.active_vessel.specific_impulse': 800,
            'space_center.active_vessel.mass': 40000000,
            'space_center.ut': 1980}

        self.burn_duration0 = 29.9
        self.burn_duration1 = 5988.6

    def tearDown(self):
        """Delete the mock objects."""
        del(self.NODE0)
        del(self.NODE1)

        del(self.CONN_ATTR0)
        del(self.CONN_ATTR1)

        del(self.burn_duration0)
        del(self.burn_duration1)

    def test_node(self, mock_conn):
        """Check that node is the first node from active vessel."""
        control = mock_conn().space_center.active_vessel.control

        with self.subTest('zero nodes'):
            control.nodes = ()
            Hal9000 = NodeExecutor()
            self.assertEqual(Hal9000.node, None)

        with self.subTest('one node'):
            control.nodes = (self.NODE0,)
            Hal9000 = NodeExecutor()
            self.assertEqual(Hal9000.node, self.NODE0)

        with self.subTest('two nodes'):
            control.nodes = (self.NODE0, self.NODE1)
            Hal9000 = NodeExecutor()
            self.assertEqual(Hal9000.node, self.NODE0)

    def test_has_node(self, mock_conn):
        """Active vessel without nodes should set has_node to False."""
        control = mock_conn().space_center.active_vessel.control

        with self.subTest('zero nodes'):
            control.nodes = ()
            Hal9000 = NodeExecutor()
            self.assertEqual(Hal9000.has_node, False)

        with self.subTest('one node'):
            control.nodes = (self.NODE0,)
            Hal9000 = NodeExecutor()
            self.assertEqual(Hal9000.has_node, True)

        with self.subTest('two nodes'):
            control.nodes = (self.NODE0, self.NODE1)
            Hal9000 = NodeExecutor()
            self.assertEqual(Hal9000.has_node, True)

    def test_delta_v(self, mock_conn):
        """Check that delta_v is set from the node."""
        mock_conn().configure_mock(**self.CONN_ATTR0)
        Hal9000 = NodeExecutor()
        self.assertEqual(Hal9000.delta_v, self.NODE0.delta_v)

    def test_burn_duration_at_max_thrust(self, mock_conn):
        """Node should set burn_duration_at_max_thrust."""
        with self.subTest('first set of values'):
            mock_conn().configure_mock(**self.CONN_ATTR0)
            Hal9000 = NodeExecutor()
            self.assertAlmostEqual(Hal9000.burn_duration_at_max_thrust,
                                   self.burn_duration0, 1)

        with self.subTest('second set of values'):
            mock_conn().configure_mock(**self.CONN_ATTR1)
            Hal9000 = NodeExecutor()
            self.assertAlmostEqual(Hal9000.burn_duration_at_max_thrust,
                                   self.burn_duration1, 1)

    def test_maximum_throttle_and_burn_duration(self, mock_conn):
        """Setting minimum_burn_duration should set burn throttle, duration."""
        mock_conn().configure_mock(**self.CONN_ATTR0)

        with self.subTest('burn time greater than minimum'):
            Hal9000 = NodeExecutor(minimum_burn_duration=self.burn_duration0/2)
            self.assertEqual(Hal9000.maximum_throttle, 1)
            self.assertEqual(Hal9000.burn_duration,
                             Hal9000.burn_duration_at_max_thrust)

        with self.subTest('no minimum'):
            Hal9000 = NodeExecutor(minimum_burn_duration=0)
            self.assertEqual(Hal9000.maximum_throttle, 1)
            self.assertAlmostEqual(Hal9000.burn_duration,
                                   Hal9000.burn_duration_at_max_thrust)

        with self.subTest('burn time less than minimum'):
            Hal9000 = NodeExecutor(minimum_burn_duration=self.burn_duration0*2)
            self.assertAlmostEqual(Hal9000.maximum_throttle, 0.5, 3)
            self.assertEqual(Hal9000.burn_duration,
                             Hal9000.minimum_burn_duration)

    def test_burn_ut(self, mock_conn):
        """Check that burn_ut is set properly."""
        mock_conn().configure_mock(**self.CONN_ATTR0)
        Hal9000 = NodeExecutor()
        self.assertAlmostEqual(
            Hal9000.burn_ut, self.NODE0.ut - Hal9000.burn_duration/2)


@patch('krpc.connect', spec=True)
class Test_NodeExecutor_methods(unittest.TestCase):
    """
    Test the NodeExecutor public methods.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def setUp(self):
        """Set up the mock objects."""
        node = namedtuple(
            'node', 'delta_v ut reference_frame remaining_delta_v')
        self.NODE0 = node(delta_v=10, ut=2000,
                          reference_frame='RF', remaining_delta_v=0.1)
        self.CONN_ATTRS = {
            'space_center.active_vessel.control.nodes': (self.NODE0,),
            'space_center.active_vessel.available_thrust': 100,
            'space_center.active_vessel.specific_impulse': 200,
            'space_center.active_vessel.mass': 30,
            'space_center.ut': 1980}

    def tearDown(self):
        """Delete the mock objects."""
        del(self.NODE0)
        del(self.CONN_ATTRS)

    @patch('NodeExecutor.time', spec=True)
    @patch('sys.stdout', spec=True)
    def test_align_to_burn(self, mock_stdout, mock_time, mock_conn):
        """Check that align_to_burn sets up and engages the autopilot."""
        mock_conn().configure_mock(**self.CONN_ATTRS)

        Hal9000 = NodeExecutor()
        auto_pilot = mock_conn().space_center.active_vessel.auto_pilot

        Hal9000.align_to_burn()

        with self.subTest('sets the auto_pilot attributes'):
            actual_ref = auto_pilot.reference_frame
            actual_dir = auto_pilot.target_direction
            actual_rol = auto_pilot.target_roll
            self.assertEqual(actual_ref, self.NODE0.reference_frame)
            self.assertEqual(actual_dir, (0, 1, 0))
            self.assertNotEqual(actual_rol, actual_rol, 'Expected NaN')

        with self.subTest('engages auto_pilot & waits for alignment'):
            CONN_CALLS = [call.engage(), call.wait()]
            auto_pilot.assert_has_calls(CONN_CALLS)

        with self.subTest('writes message to stdout'):
            T0 = self.NODE0.ut - self.CONN_ATTRS['space_center.ut']
            STDOUT_CALLS = [call(f'Aligning at T0-{T0:.0f} seconds')]
            mock_stdout.write.assert_has_calls(STDOUT_CALLS)

    @patch('sys.stdout', spec=True)
    def test_warp_safely_to_burn(self, mock_stdout, mock_conn):
        """Check that warp_safely_to_burn calls warp_to() only if necessary."""
        mock_conn().configure_mock(**self.CONN_ATTRS)
        MARGIN = 10
        Hal9000 = NodeExecutor()
        BURN_UT = Hal9000.burn_ut
        space_center = mock_conn().space_center

        with self.subTest('node already past'):
            space_center.ut = BURN_UT
            Hal9000.warp_safely_to_burn(margin=MARGIN)
            space_center.warp_to.assert_not_called()
            mock_stdout.write.assert_not_called()

        with self.subTest('node is now'):
            space_center.ut = BURN_UT - MARGIN
            Hal9000.warp_safely_to_burn(margin=MARGIN)
            space_center.warp_to.assert_not_called()
            mock_stdout.write.assert_not_called()

        with self.subTest('node still in future'):
            space_center.ut = BURN_UT - MARGIN - 1
            Hal9000.warp_safely_to_burn(margin=MARGIN)
            space_center.warp_to.assert_called_with(BURN_UT - MARGIN)
            T0 = self.NODE0.ut - BURN_UT + MARGIN
            STDOUT_CALLS = [call(f'Warping to  T0-{T0:.0f} seconds')]
            mock_stdout.write.assert_has_calls(STDOUT_CALLS)

    def test_wait_until_ut(self, mock_conn):
        """Should not call time.sleep if ut already past."""
        Hal9000 = NodeExecutor()

        with patch('NodeExecutor.time', spec=True) as mock_time:
            mock_conn().space_center.ut = 100
            Hal9000.wait_until_ut(ut_threshold=10)
            mock_time.sleep.assert_not_called()

        with patch('time.sleep', spec=True, side_effect=StopIteration):
            mock_conn().space_center.ut = 10
            called = False
            try:
                Hal9000.wait_until_ut(ut_threshold=100)
            except StopIteration:
                called = True
            self.assertTrue(called)

    def test_burn_baby_burn(self, mock_conn):
        """Check it sets up, executes, and cleans up the burn loop."""
        mock_conn().configure_mock(**self.CONN_ATTRS)
        Hal9000 = NodeExecutor()
        dV_left = self.NODE0.delta_v
        remaining_delta_v = self.NODE0.remaining_delta_v
        mock_conn().stream().__enter__().return_value = dV_left
        with patch.object(NodeExecutor, '_print_burn_event'):
            with patch.object(NodeExecutor, '_burn_loop'):
                with patch.object(NodeExecutor, '_print_burn_error'):
                    with patch.object(NodeExecutor, '_cleanup'):
                        Hal9000.burn_baby_burn()
                        Hal9000._cleanup.assert_called_once_with()
                    Hal9000._print_burn_error.assert_called_once_with(
                        remaining_delta_v)
                Hal9000._burn_loop.assert_called_once_with()
            calls = [call('Ignition'), call('MECO')]
            Hal9000._print_burn_event.assert_has_calls(calls)

    def test_execute_node(self, mock_conn):
        """Should gradually approach node, and call burn_baby_burn()."""
        mock_conn().configure_mock(**self.CONN_ATTRS)
        Hal9000 = NodeExecutor()
        with patch.object(NodeExecutor, 'burn_baby_burn'):
            with patch.object(NodeExecutor, 'wait_until_ut'):
                with patch.object(NodeExecutor, 'warp_safely_to_burn'):
                    with patch.object(NodeExecutor, 'align_to_burn'):
                        Hal9000.execute_node()
                        calls = [call(), call()]
                        Hal9000.align_to_burn.assert_has_calls(calls)
                    calls = [call(margin=180), call(margin=5)]
                    Hal9000.warp_safely_to_burn.assert_has_calls(calls)
                Hal9000.wait_until_ut.assert_called_once_with(Hal9000.burn_ut)
            Hal9000.burn_baby_burn.assert_called_once_with()


@patch('krpc.connect', spec=True)
class Test_NodeExecutor_private_methods(unittest.TestCase):
    """
    Test the NodeExecutor class private methods.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def setUp(self):
        """Set up the mock objects."""
        node = namedtuple('node', 'delta_v ut reference_frame')
        self.NODE0 = node(delta_v=10, ut=2000, reference_frame='RF')
        self.CONN_ATTRS = {
            'space_center.active_vessel.control.nodes': (self.NODE0,),
            'space_center.active_vessel.available_thrust': 100,
            'space_center.active_vessel.specific_impulse': 200,
            'space_center.active_vessel.mass': 30,
            'space_center.ut': 1980}

    def tearDown(self):
        """Delete the mock objects."""
        del(self.NODE0)
        del(self.CONN_ATTRS)

    def test__clamp(self, mock_conn):
        """Should clamp the value between ceiling and floor."""
        Hal9000 = NodeExecutor()

        values = [[-1, 0, 2, 0], [1, 2, 0, 1],
                  [0, -1, 1, 0], [-1, -3, -2, -2], ]

        for value, floor, ceiling, result in values:
            self.assertEqual(Hal9000._clamp(value, floor, ceiling), result)

    def test__throttle_manager(self, mock_conn):
        """Should decrease throttle linearly towards end of burn."""
        mock_conn().configure_mock(**self.CONN_ATTRS)
        Hal9000 = NodeExecutor()
        control = mock_conn().space_center.active_vessel.control

        values = [[1, 1], [0.1, 1], [0.05, 0.5],
                  [0.005, 0.05], [0.001, 0.05], ]

        for value, result in values:
            Hal9000._throttle_manager(self.NODE0.delta_v * value)
            self.assertAlmostEqual(
                control.throttle, result * Hal9000.maximum_throttle)

    @patch('NodeExecutor.time', spec=True)
    @patch('sys.stdout', spec=True)
    def test__auto_stage(self, mock_stdout, mock_time, mock_conn):
        """Should autostage if thrust drops 10% or more."""
        mock_conn().configure_mock(**self.CONN_ATTRS)
        Hal9000 = NodeExecutor()
        vessel = mock_conn().space_center.active_vessel
        control = vessel.control

        VALUES = [[95, 0.79, 3.1, False],
                  [89, 0.84, 3.4, True],
                  [50, 1.00, 6.0, True],
                  [25, 1.00, 12.0, True], ]

        for new_thrust, throttle, burn_duration, calls_made in VALUES:
            with self.subTest(f'thrust_ratio: {new_thrust}%'):
                mock_conn().reset_mock()
                mock_stdout.reset_mock()
                mock_time.reset_mock()
                vessel.available_thrust = new_thrust
                self.assertEqual(Hal9000._auto_stage(100), new_thrust)
                self.assertAlmostEqual(Hal9000.maximum_throttle, throttle, 2)
                self.assertAlmostEqual(
                    Hal9000.burn_duration_at_max_thrust, burn_duration, 1)
                if calls_made:
                    control.activate_next_stage.assert_called_once_with()
                    mock_stdout.write.assert_has_calls(
                        [call(f'Staged at T0-20 seconds')])
                    mock_time.sleep.assert_has_calls([call(0.1), call(0.1)])
                else:
                    mock_stdout.write.assert_not_called()
                    mock_time.sleep.assert_not_called()

    def test__cleanup(self, mock_conn):
        """Should call disengage() on autopilot & remove() on node."""
        Hal9000 = NodeExecutor()
        vessel = mock_conn().space_center.active_vessel

        vessel.auto_pilot.disengage.assert_not_called()
        vessel.control.nodes[0].remove.assert_not_called()
        Hal9000._cleanup()
        vessel.auto_pilot.disengage.assert_called_once_with()
        vessel.control.nodes[0].remove.assert_called_once_with()

    def test__is_burn_complete(self, mock_conn):
        """Check returns True when it's time to shut down the engines."""
        Hal9000 = NodeExecutor()
        self.assertFalse(Hal9000._is_burn_complete(error=10))
        self.assertTrue(Hal9000._is_burn_complete(error=30))

    def test__print_burn_event(self, mock_conn):
        """Should print to stdout with the time to T0 appended."""
        mock_conn().configure_mock(**self.CONN_ATTRS)
        TEST_MSG = 'Test event happened'
        STDOUT_CALLS = [call(f'Test event happened at T0-20 seconds')]
        Hal9000 = NodeExecutor()
        with patch('sys.stdout', spec=True) as mock_stdout:
            Hal9000._print_burn_event(TEST_MSG)
            mock_stdout.write.assert_has_calls(STDOUT_CALLS)

    def test__burn_loop(self, mock_conn):
        """Should manage throttle during burn, with staging."""
        def _false_once_then_true():
            yield False
            while True:
                yield True

        mock_conn().configure_mock(**self.CONN_ATTRS)
        Hal9000 = NodeExecutor()
        dV_left = 100
        mock_conn().space_center.active_vessel.auto_pilot.error = 0
        mock_conn().stream().__enter__().return_value = dV_left
        with patch.object(NodeExecutor, '_is_burn_complete',
                          side_effect=_false_once_then_true(),), \
                patch.object(NodeExecutor, '_throttle_manager'), \
                patch.object(NodeExecutor, '_auto_stage'), \
                patch.object(NodeExecutor, '_wait_to_go_around_again'):
            Hal9000._burn_loop()
            Hal9000._wait_to_go_around_again.assert_called_once_with()
            Hal9000._auto_stage.assert_called_once_with(Hal9000.thrust)
            Hal9000._throttle_manager.assert_called_once_with(dV_left)
            Hal9000._is_burn_complete.assert_has_calls(
                [call(dV_left), call(dV_left)])

    def test__print_burn_error(self, mock_conn):
        """Check that the remaining deltaV is printed to stdout."""
        mock_conn().configure_mock(**self.CONN_ATTRS)
        Hal9000 = NodeExecutor()
        dV_left = 0.1
        STDOUT_CALLS = [
            call(f'{(dV_left/Hal9000.delta_v):2.2f}% of original dV left.')]
        with patch('sys.stdout', spec=True) as mock_stdout:
            Hal9000._print_burn_error(dV_left)
            mock_stdout.write.assert_has_calls(STDOUT_CALLS)

    def test__wait_to_go_around_again(self, mock_conn):
        """Check it calls time.sleep() for 10 ms."""
        Hal9000 = NodeExecutor()

        with patch('NodeExecutor.time', spec=True) as mock_time:
            Hal9000._wait_to_go_around_again()
            mock_time.sleep.assert_called_once_with(0.01)

    def test___str__(self, mock_conn):
        """Check that the __str__() method works."""
        mock_conn().configure_mock(**self.CONN_ATTRS)
        actual_str = str(NodeExecutor(minimum_burn_duration=10))
        expect_str = 'Will burn for 10.0 m/s starting in 15.0 seconds.\n'
        self.assertEqual(actual_str, expect_str)

    def test___repr__(self, mock_conn):
        """Check that the __repr__() method works."""
        actual_str = repr(NodeExecutor(minimum_burn_duration=10))
        expect_str = 'NodeExecutor(minimum_burn_duration=10)'
        self.assertEqual(actual_str, expect_str)


if __name__ == '__main__':
    unittest.main()
