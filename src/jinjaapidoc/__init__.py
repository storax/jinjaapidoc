__author__ = 'David Zuber'
__email__ = 'zuber.david@gmx.de'
__version__ = '0.1.0'


import logging


def setup_basic_logger():
    """Setup the basicConfig for logging

    :returns: None
    :rtype: None
    :raises: None
    """
    fmt = "%(levelname)-8s:%(name)s:%(lineno)d: %(message)s"
    logging.basicConfig(format=fmt)


setup_basic_logger()
