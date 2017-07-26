#!/usr/bin/env python
# encoding: utf-8
"""erie.py: API for Erie board
"""

__version__ = "0.0.1"
__author__ = 'dqli'
__all__ = ["erie"]

import serial
import re
import logging
import time

logger = logging.getLogger(__name__)


class Erie(object):

    def __init__(self):
        pass

    def __del__(self):
        pass

    def InputOn(self, port):
        logger.info("Now I'm calling Erie")
        #raise NotImplementedError()

    def InputOff(self, port):
        logger.info("Now I'm calling Erie")
        #raise NotImplementedError()

    def OutputOn(self, port):
        logger.info("Now I'm calling Erie")
        #raise NotImplementedError()

    def OutputOff(self, port):
        logger.info("Now I'm calling Erie")
        #raise NotImplementedError()

