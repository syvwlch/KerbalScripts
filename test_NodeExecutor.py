"""
Unit test the NodeExecutor class.

Work in progress.
"""

import unittest
from unittest.mock import patch  # call
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
        self.node0 = node(delta_v=10, ut=20)
        self.node1 = node(delta_v=30, ut=40)

    def tearDown(self):
        """Delete the mock objects."""
        del(self.node0)
        del(self.node1)

    def test_node(self, mock_conn):
        """Check that node is the first node from active vessel."""
        with self.subTest(nodes=()):
            mock_conn().space_center.active_vessel.control.nodes = ()
            Hal9000 = NodeExecutor.NodeExecutor()
            self.assertEqual(Hal9000.node, None)

        with self.subTest('One node'):
            mock_conn().space_center.active_vessel.control.nodes = (self.node0,)
            Hal9000 = NodeExecutor.NodeExecutor()
            self.assertEqual(Hal9000.node, self.node0)

        with self.subTest('Two nodes'):
            mock_conn().space_center.active_vessel.control.nodes = (self.node0, self.node1)
            Hal9000 = NodeExecutor.NodeExecutor()
            self.assertEqual(Hal9000.node, self.node0)

    def test_has_node(self, mock_conn):
        """Check that has_node is True only when the active vessel has at least one node."""
        with self.subTest('No nodes'):
            mock_conn().space_center.active_vessel.control.nodes = ()
            Hal9000 = NodeExecutor.NodeExecutor()
            self.assertEqual(Hal9000.has_node, False)

        with self.subTest('One node'):
            mock_conn().space_center.active_vessel.control.nodes = (self.node0,)
            Hal9000 = NodeExecutor.NodeExecutor()
            self.assertEqual(Hal9000.has_node, True)

        with self.subTest('Two nodes'):
            mock_conn().space_center.active_vessel.control.nodes = (self.node0, self.node1)
            Hal9000 = NodeExecutor.NodeExecutor()
            self.assertEqual(Hal9000.has_node, True)

    def test_delta_v(self, mock_conn):
        """Check that delta_v is set from the node."""
        mock_conn().space_center.active_vessel.control.nodes = (self.node0,)
        Hal9000 = NodeExecutor.NodeExecutor()
        self.assertEqual(Hal9000.delta_v, self.node0.delta_v)

    def test_burn_time_at_max_thrust(self, mock_conn):
        """Check that burn_time_at_max_thrust is set from the node and active vessel."""
        mock_conn().space_center.active_vessel.control.nodes = (self.node0,)
        mock_conn().space_center.active_vessel.available_thrust = 10
        mock_conn().space_center.active_vessel.specific_impulse = 20
        mock_conn().space_center.active_vessel.mass = 30
        Hal9000 = NodeExecutor.NodeExecutor()
        self.assertEqual(Hal9000.burn_time_at_max_thrust, 10)


if __name__ == '__main__':
    unittest.main()
