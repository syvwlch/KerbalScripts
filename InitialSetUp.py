"""
Takes care of the core setup tasks all scripts will need.

Currently holds a function to set up a logger,
and another to connect to the server.
"""

import logging
import krpc


def set_up_logger(log_filename):
    """Set up the logger."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.ERROR)
    file_formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_formatter = logging.Formatter('%(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    return logger


def connect_to_krpc_server(client_name):
    """Connect to the krpc server."""
    conn = krpc.connect(name=client_name)
    return conn
