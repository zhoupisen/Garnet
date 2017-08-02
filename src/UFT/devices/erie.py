#!/usr/bin/env python
# encoding: utf-8
"""erie.py: API for Erie board
"""

__version__ = "0.0.1"
__author__ = 'dqli'
__all__ = ["erie"]

import serial
import logging

logger = logging.getLogger(__name__)
debugOut = True


class Erie(object):

    def __init__(self, port='COM1', baudrate=9600, **kvargs):
        timeout = kvargs.get('timeout', 5)
        parity = kvargs.get('parity', serial.PARITY_NONE)
        bytesize = kvargs.get('bytesize', serial.EIGHTBITS)
        stopbits = kvargs.get('stopbits', serial.STOPBITS_ONE)
        self.ser = serial.Serial(port=port, baudrate=baudrate,
                                 timeout=timeout, bytesize=bytesize,
                                 parity=parity, stopbits=stopbits)
        if (not self.ser.isOpen()):
            self.ser.open()

    def __del__(self):
        self.ser.close()


    def _logging_(self, info):
        if debugOut == True:
            logger.info(info)

    def InputOn(self, port):
        self._logging_("Now I'm calling Erie")
        #raise NotImplementedError()

    def InputOff(self, port):
        self._logging_("Now I'm calling Erie")
        #raise NotImplementedError()

    def OutputOn(self, port):
        self._logging_("Now I'm calling Erie")
        #raise NotImplementedError()

    def OutputOff(self, port):
        self._logging_("Now I'm calling Erie")
        #raise NotImplementedError()

    def iic_write(self, port, address, length, data):
        self._logging_("Now I'm calling Erie")
        raise NotImplementedError()

    def iic_read(self, port, address, length, data):
        self._logging_("Now I'm calling Erie")
        raise NotImplementedError()

    def _transfercommand_(self):
        pass

    def _receiveresult_(self):
        pass
