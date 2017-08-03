#!/usr/bin/env python
# encoding: utf-8
"""erie.py: API for Erie board
"""

__version__ = "0.0.1"
__author__ = 'dqli'
__all__ = ["erie"]

import serial, time
import logging

logger = logging.getLogger(__name__)
debugOut = True
Group = 0
DELAY4ERIE = 3


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

    def _displaylanguage_(self, content):
        display = "  transfering language: "
        for c in content:
            tmp = ord(c)
            display += "%x " % tmp
        self._logging_(display)

    def InputOn(self, port):
        self._logging_("set load on")
        #raise NotImplementedError()

    def InputOff(self, port):
        self._logging_("set load off")
        #raise NotImplementedError()

    def OutputOn(self, port):
        self._logging_("set power on")
        cmd = 0x05
        self._transfercommand_(port, cmd)

    def OutputOff(self, port):
        self._logging_("set power off")
        #raise NotImplementedError()

    def iic_write(self, port, address, length, data):
        self._logging_("write IIC data")
        raise NotImplementedError()

    def iic_read(self, port, address, length, data):
        self._logging_("read IIC data")
        raise NotImplementedError()

    def _transfercommand_(self, port, cmd, datalen = 0, data = None):
        port += Group * 4
        header0 = 0x55
        header1 = 0x77
        content = chr(header0) + chr(header1) + chr(cmd) + chr(port)
        if (datalen != 0) & (data is not None):
            content = ""
            time.sleep(1)
            for d in data:
                content += chr(d)
        self._displaylanguage_(content)
        self.ser.write(content)

    def _receiveresult_(self):
        time.sleep(DELAY4ERIE)  # wait for response
        buff = ''
        while (self.ser.inWaiting() > 0):
            buff += self.ser.read(1)
        return buff
