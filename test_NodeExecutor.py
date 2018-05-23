"""
Unit test the NodeExecutor class.

Work in progress.
"""

import unittest
from unittest.mock import patch  # call
import sys
import NodeExecutor


class Test_environment(unittest.TestCase):
    """Test the environment to ensure it will match production."""

    def test_python_version(self):
        """Make sure the python version is 3.x."""
        self.assertGreaterEqual(sys.version_info[0], 3)


@patch('krpc.connect', spec=True)
class Test_NodeExecutor_init(unittest.TestCase):
    """
    Test the NodeExecutor class __ini__ method.

    Requires a patch on the KRPC server connection for:
        - active vessel
    """

    def test_no_krpc_connection(self, mock_conn):
        """Check that __init__ raises error without a KRPC server."""
        mock_conn.side_effect = ConnectionRefusedError

        with self.assertRaises(ConnectionRefusedError):
            NodeExecutor.NodeExecutor()

    def test_krpc_connection(self, mock_conn):
        """Check that __init__ connects to KRPC server."""
        NodeExecutor.NodeExecutor()

        mock_conn.assert_called_once_with(name='NodeExecutor')

    def test_init_target_sma_no_karg(self, mock_conn):
        """Check that __init__ w/o karg sets target_sma to inital_sma."""
        Hal9000 = NodeExecutor.NodeExecutor()

        self.assertEqual(Hal9000.minimum_burn_time, 4)

    def test_init_target_sma(self, mock_conn):
        """Check that __init__ with target_sma karg sets it."""
        Hal9000 = NodeExecutor.NodeExecutor(minimum_burn_time=10)

        self.assertEqual(Hal9000.minimum_burn_time, 10)


if __name__ == '__main__':
    unittest.main()
