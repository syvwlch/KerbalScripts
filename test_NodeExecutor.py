"""
Unit test the NodeExecutor class.

Work in progress.
"""

import unittest
from unittest.mock import patch, call
from collections import namedtuple
import sys
import NodeExecutor


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
        """Check that __init__ raises ConnectionRefusedError if it can't reach KRPC server."""
        try:
            NodeExecutor.NodeExecutor()
        except Exception as e:
            self.assertIsInstance(e, ConnectionRefusedError)
        return

    @patch('krpc.connect', spec=True)
    def test_krpc_connection(self, mock_conn):
        """Check that __init__ connects to KRPC server."""
        NodeExecutor.NodeExecutor()
        mock_conn.assert_called_once_with(name='NodeExecutor')

    @patch('krpc.connect', spec=True)
    def test_init_minimum_burn_time_no_karg(self, mock_conn):
        """Check that __init__ w/o karg sets minimum_burn_time to 4."""
        Hal9000 = NodeExecutor.NodeExecutor()
        self.assertEqual(Hal9000.minimum_burn_time, 4)

    @patch('krpc.connect', spec=True)
    def test_init_minimum_burn_time(self, mock_conn):
        """Check that __init__ with minimum_burn_time karg sets it."""
        Hal9000 = NodeExecutor.NodeExecutor(minimum_burn_time=10)
        self.assertEqual(Hal9000.minimum_burn_time, 10)

    @patch('krpc.connect', spec=True)
    def test_init_minimum_burn_time_negative_value(self, mock_conn):
        """Check that __init__ raises AssertionError with negative value for karg."""
        try:
            NodeExecutor.NodeExecutor(minimum_burn_time=-10)
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

        control = namedtuple('control', 'nodes')
        self.CONTROL0 = control(nodes=(self.NODE0, self.NODE1))
        self.CONTROL1 = control(nodes=(self.NODE1,))

        vessel = namedtuple('vessel', 'control available_thrust specific_impulse mass')
        self.VESSEL0 = vessel(control=self.CONTROL0,
                              available_thrust=100,
                              specific_impulse=200,
                              mass=300,)
        self.BURN_TIME0 = 29.9
        self.VESSEL1 = vessel(control=self.CONTROL1,
                              available_thrust=200000,
                              specific_impulse=800,
                              mass=40000000,)
        self.BURN_TIME1 = 5988.6

    def tearDown(self):
        """Delete the mock objects."""
        del(self.NODE0)
        del(self.NODE1)

        del(self.CONTROL0)
        del(self.CONTROL1)

        del(self.VESSEL0)
        del(self.VESSEL1)

        del(self.BURN_TIME0)
        del(self.BURN_TIME1)

    def test_node(self, mock_conn):
        """Check that node is the first node from active vessel."""
        with self.subTest('zero nodes'):
            mock_conn().space_center.active_vessel.control.nodes = ()
            Hal9000 = NodeExecutor.NodeExecutor()
            self.assertEqual(Hal9000.node, None)

        with self.subTest('one node'):
            mock_conn().space_center.active_vessel.control.nodes = (self.NODE0,)
            Hal9000 = NodeExecutor.NodeExecutor()
            self.assertEqual(Hal9000.node, self.NODE0)

        with self.subTest('two nodes'):
            mock_conn().space_center.active_vessel.control.nodes = (self.NODE0, self.NODE1)
            Hal9000 = NodeExecutor.NodeExecutor()
            self.assertEqual(Hal9000.node, self.NODE0)

    def test_has_node(self, mock_conn):
        """Check that has_node is True only when the active vessel has at least one node."""
        with self.subTest('No nodes'):
            mock_conn().space_center.active_vessel.control.nodes = ()
            Hal9000 = NodeExecutor.NodeExecutor()
            self.assertEqual(Hal9000.has_node, False)

        with self.subTest('One node'):
            mock_conn().space_center.active_vessel.control.nodes = (self.NODE0,)
            Hal9000 = NodeExecutor.NodeExecutor()
            self.assertEqual(Hal9000.has_node, True)

        with self.subTest('Two nodes'):
            mock_conn().space_center.active_vessel.control.nodes = (self.NODE0, self.NODE1)
            Hal9000 = NodeExecutor.NodeExecutor()
            self.assertEqual(Hal9000.has_node, True)

    def test_delta_v(self, mock_conn):
        """Check that delta_v is set from the node."""
        mock_conn().space_center.active_vessel = self.VESSEL0
        Hal9000 = NodeExecutor.NodeExecutor()
        self.assertEqual(Hal9000.delta_v, self.NODE0.delta_v)

    def test_burn_time_at_max_thrust(self, mock_conn):
        """Check that burn_time_at_max_thrust is set from the node and active vessel."""
        with self.subTest('first set of values'):
            mock_conn().space_center.active_vessel = self.VESSEL0
            Hal9000 = NodeExecutor.NodeExecutor()
            self.assertAlmostEqual(Hal9000.burn_time_at_max_thrust, self.BURN_TIME0, 1)

        with self.subTest('second set of values'):
            mock_conn().space_center.active_vessel = self.VESSEL1
            Hal9000 = NodeExecutor.NodeExecutor()
            self.assertAlmostEqual(Hal9000.burn_time_at_max_thrust, self.BURN_TIME1, 1)

    def test_maximum_throttle_and_burn_time(self, mock_conn):
        """Check that maximum_throttle & burn_time are set from minimum_burn_time."""
        mock_conn().space_center.active_vessel = self.VESSEL0

        with self.subTest('burn time greater than minimum'):
            Hal9000 = NodeExecutor.NodeExecutor(minimum_burn_time=self.BURN_TIME0/2)
            self.assertEqual(Hal9000.maximum_throttle, 1)
            self.assertEqual(Hal9000.burn_time, Hal9000.burn_time_at_max_thrust)

        with self.subTest('no minimum'):
            Hal9000 = NodeExecutor.NodeExecutor(minimum_burn_time=0)
            self.assertEqual(Hal9000.maximum_throttle, 1)
            self.assertAlmostEqual(Hal9000.burn_time, Hal9000.burn_time_at_max_thrust)

        with self.subTest('burn time less than minimum'):
            Hal9000 = NodeExecutor.NodeExecutor(minimum_burn_time=self.BURN_TIME0*2)
            self.assertAlmostEqual(Hal9000.maximum_throttle, 0.5, 3)
            self.assertEqual(Hal9000.burn_time, Hal9000.minimum_burn_time)

    def test_burn_ut(self, mock_conn):
        """Check that burn_ut is set properly."""
        mock_conn().space_center.active_vessel = self.VESSEL0
        Hal9000 = NodeExecutor.NodeExecutor()
        self.assertAlmostEqual(Hal9000.burn_ut, self.NODE0.ut - Hal9000.burn_time/2)


@patch('krpc.connect', spec=True)
class Test_NodeExecutor_methods(unittest.TestCase):
    """
    Test the NodeExecutor class methods.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def setUp(self):
        """Set up the mock objects."""
        node = namedtuple('node', 'delta_v ut reference_frame')
        self.NODE0 = node(delta_v=10, ut=2000, reference_frame='RF')

        control = namedtuple('control', 'nodes')
        self.CONTROL0 = control(nodes=(self.NODE0,))

        vessel = namedtuple('vessel', 'control available_thrust specific_impulse mass')
        self.VESSEL0 = vessel(control=self.CONTROL0,
                              available_thrust=100,
                              specific_impulse=200,
                              mass=300,)

    def tearDown(self):
        """Delete the mock objects."""
        del(self.NODE0)
        del(self.CONTROL0)
        del(self.VESSEL0)

    @patch('sys.stdout')
    def test_align_to_burn(self, mock_stdout, mock_conn):
        """Check that align_to_burn sets up and engages the autopilot."""
        mock_conn().space_center.active_vessel.control = self.CONTROL0
        Hal9000 = NodeExecutor.NodeExecutor()

        Hal9000.align_to_burn()

        with self.subTest('sets the auto_pilot attributes'):
            actual_ref = mock_conn().space_center.active_vessel.auto_pilot.reference_frame
            self.assertEqual(actual_ref, self.NODE0.reference_frame)
            actual_dir = mock_conn().space_center.active_vessel.auto_pilot.target_direction
            self.assertEqual(actual_dir, (0, 1, 0))
            actual_rol = mock_conn().space_center.active_vessel.auto_pilot.target_roll
            self.assertNotEqual(actual_rol, actual_rol)

        with self.subTest('engages auto_pilot & waits for alignment'):
            CONN_CALLS = [call.auto_pilot.engage(), call.auto_pilot.wait()]
            mock_conn().space_center.active_vessel.assert_has_calls(CONN_CALLS)

        with self.subTest('writes message to stdout'):
            STDOUT_CALLS = [call.write('Aligning to burn')]
            mock_stdout.assert_has_calls(STDOUT_CALLS)

    @patch('sys.stdout')
    def test_warp_safely_to_burn(self, mock_stdout, mock_conn):
        """Check that warp_safely_to_burn calls warp_to() only if necessary."""
        mock_conn().space_center.active_vessel = self.VESSEL0
        MARGIN = 10
        Hal9000 = NodeExecutor.NodeExecutor()
        BURN_UT = Hal9000.burn_ut

        with self.subTest('node already past'):
            mock_conn().space_center.ut = BURN_UT
            Hal9000.warp_safely_to_burn(margin=MARGIN)
            mock_conn().space_center.warp_to.assert_not_called()
            mock_stdout.write.assert_not_called()

        with self.subTest('node is now'):
            mock_conn().space_center.ut = BURN_UT - MARGIN
            Hal9000.warp_safely_to_burn(margin=MARGIN)
            mock_conn().space_center.warp_to.assert_not_called()
            mock_stdout.write.assert_not_called()

        with self.subTest('node still in future'):
            mock_conn().space_center.ut = BURN_UT - MARGIN - 1
            Hal9000.warp_safely_to_burn(margin=MARGIN)
            mock_conn().space_center.warp_to.assert_called_with(BURN_UT - MARGIN)
            calls = [call(f'Warping to {MARGIN:3.0f} seconds before burn.')]
            mock_stdout.write.assert_has_calls(calls)

    def test_wait_until_ut(self, mock_conn):
        """Check that wait_until_ut doesn't call time.sleep if ut is now or already past."""
        Hal9000 = NodeExecutor.NodeExecutor()

        with patch('time.sleep') as mock_sleep:
            mock_conn().space_center.ut = 100
            Hal9000.wait_until_ut(ut_threshold=10)
            mock_sleep().assert_not_called()

        with patch('time.sleep', side_effect=StopIteration):
            mock_conn().space_center.ut = 10
            called = False
            try:
                Hal9000.wait_until_ut(ut_threshold=100)
            except StopIteration:
                called = True
            self.assertTrue(called)


if __name__ == '__main__':
    unittest.main()
