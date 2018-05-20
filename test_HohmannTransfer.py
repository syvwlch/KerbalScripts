"""
Unit test the HohmannTransfer module.

Work in progress.
"""

import unittest
from unittest.mock import patch
import HohmannTransfer
import sys


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


if __name__ == '__main__':
    unittest.main()
