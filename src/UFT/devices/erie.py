#!/usr/bin/env python
# encoding: utf-8
"""erie.py: API for Erie board
"""

__version__ = "0.0.1"
__author__ = 'dqli'
__all__ = ["erie"]

import serial, time
import logging
from UFT.devices import aardvark

logger = logging.getLogger(__name__)
debugOut = False
Group = 0
DELAY4ERIE = 0.1
FirmwareVersion = [1, 1]


class Erie(object):

    LastSending = ""
    LastReceiving = ""

    def __init__(self, port='COM1', baudrate=115200, **kvargs):
        timeout = kvargs.get('timeout', 10)
        parity = kvargs.get('parity', serial.PARITY_NONE)
        bytesize = kvargs.get('bytesize', serial.EIGHTBITS)
        stopbits = kvargs.get('stopbits', serial.STOPBITS_ONE)
        self.ser = serial.Serial(port=port, baudrate=baudrate,
                                 timeout=timeout, bytesize=bytesize,
                                 parity=parity, stopbits=stopbits)
        if (not self.ser.isOpen()):
            self.ser.open()
            self._cleanbuffer_()

        self.GetVersion()

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

    def _erroroutinfor_(self):
        display = "  last sending command : "
        for c in self.LastSending:
            tmp = ord(c)
            display += "%x " % tmp
        logger.info(display)
        display = "  last receiving data : "
        for c in self.LastReceiving:
            tmp = ord(c)
            display += "%x " % tmp
        logger.info(display)

    def GetVersion(self):
        self._logging_("Get firmware version")
        cmd = 0x0C
        self._transfercommand_(0x00, cmd)
        ret = self._receiveresult_()
        if ret[2] != 0x0C or ret[6] != 0x00:
            raise Exception("UART communication failure")
        if ret[7] != FirmwareVersion[0] or ret[8] != FirmwareVersion[1]:
            raise Exception("Wrong Erie firmware version: " + str(ret[7]) + "." + str(ret[8]))

    def SetProType(self, port, type):
        self._logging_("set product type")
        cmd = 0x00;
        self._transfercommand_(port, cmd, 0x01, [type])
        ret = self._receiveresult_()
        if ret[2] != 0x00 or ret[6] != 0x00:
            raise Exception("UART communication failure")

    def InputOn(self, port, loadmode):
        cmd = 0x0A
        if loadmode == 'low':
            self._logging_("set load on low current")
            self._transfercommand_(port, cmd, 0x01, [0x00])
        else:
            self._logging_("set load on low current")
            self._transfercommand_(port, cmd, 0x01, [0x01])

        ret = self._receiveresult_()
        if ret[2] != 0x0A or ret[6] != 0x00:
            raise Exception("UART communication failure")

    def InputOff(self, port):
        self._logging_("set load off")
        cmd = 0x0B
        self._transfercommand_(port, cmd)
        ret = self._receiveresult_()
        if ret[2] != 0x0B or ret[6] != 0x00:
            raise Exception("UART communication failure")

    def OutputOn(self, port):
        self._logging_("set power on")
        cmd = 0x05
        self._transfercommand_(port, cmd)
        ret = self._receiveresult_()
        if ret[2] != 0x05 or ret[6] != 0x00:
            raise Exception("UART communication failure")

    def OutputOff(self, port):
        self._logging_("set power off")
        cmd = 0x06
        self._transfercommand_(port, cmd)
        ret = self._receiveresult_()
        if ret[2] != 0x06 or ret[6] != 0x00:
            raise Exception("UART communication failure")

    def LedOn(self, port):
        self._logging_("set LED on")
        cmd = 0x08
        self._transfercommand_(port, cmd)
        ret = self._receiveresult_()
        if ret[2] != 0x08 or ret[6] != 0x00:
            raise Exception("UART communication failure")

    def LedOff(self, port):
        self._logging_("set LED off")
        cmd = 0x09
        self._transfercommand_(port, cmd)
        ret = self._receiveresult_()
        if ret[2] != 0x09 or ret[6] != 0x00:
            raise Exception("UART communication failure")

    def ResetDUT(self, port):
        self._logging_("reset DUT")
        cmd = 0x0d
        self._transfercommand_(port, cmd)
        time.sleep(5)
        ret = self._receiveresult_()
        if ret[2] != 0x0d or ret[6] != 0x00:
            raise Exception("UART communication failure")

    def ShutdownDUT(self, port):
        self._logging_("shutdown DUT")
        cmd = 0x0e
        self._transfercommand_(port, cmd)
        time.sleep(3)
        ret = self._receiveresult_()
        if ret[2] != 0x0e or ret[6] != 0x00:
            raise Exception("UART communication failure")

    def GetPresentPin(self, port):
        self._logging_("Get Present Pin Status")
        cmd = 0x03
        self._transfercommand_(port, cmd)
        ret = self._receiveresult_()
        if ret[2] != 0x03 or ret[6] != 0x00:
            raise Exception("UART communication failure")
        if ret[7] == 0:
            return True
        else:
            return False

    def GetGTGPin(self, port):
        self._logging_("Get GTG Pin Status")
        cmd = 0x04
        self._transfercommand_(port, cmd)
        ret = self._receiveresult_()
        if ret[2] != 0x04 or ret[6] != 0x00:
            raise Exception("UART communication failure")
        if ret[7] == 1:
            return True
        else:
            return False

    def iic_write(self, port, address, length, data):
        if length != 2:
            raise Exception("IIC length does not support")
        self._logging_("write IIC data")
        cmd = 0x02
        self._transfercommand_(port, cmd, 0x03, [address] + data)
        try:
            ret = self._receiveresult_()
        except Exception:
            ret = self._receiveresult_()

        if ret[2] != 0x02 or ret[6] != 0x00:
            raise aardvark.USBI2CAdapterException("UART communication failure")
        return 0

    def iic_read(self, port, address, length, data):
        if length != 1:
            raise Exception("IIC length does not support")
        val = []
        self._logging_("read IIC data")
        cmd = 0x01
        self._transfercommand_(port, cmd, 0x02, [address] + data)
        ret = self._receiveresult_()
        if ret[2] != 0x01 or ret[6] != 0x00:
            raise aardvark.USBI2CAdapterException("UART communication failure")
        val.append(ret[7])
        return val

    def _cleanbuffer_(self):
        self.ser.flushInput()
        self.ser.flushOutput()

    def _transfercommand_(self, port, cmd, datalen = 0, data = None):
        port += Group * 4
        header0 = 0x55
        header1 = 0x77
        content = chr(header0) + chr(header1) + chr(cmd) + chr(port)
        content += chr(datalen & 0xFF)
        content += chr((datalen >> 8) & 0xFF)

        if (datalen != 0) & (data is not None):
            for d in data:
                content += chr(d)

        self.LastSending = content
        self._displaylanguage_(content)
        self._cleanbuffer_()
        self.ser.write(content)

    def _receiveresult_(self):
        time.sleep(DELAY4ERIE)  # wait for response
        buff = []
        content = ""
        while (self.ser.inWaiting() > 0):
            tmp = self.ser.read(1)
            buff.append(ord(tmp))
            content += tmp

        self.LastReceiving = content
        self._displaylanguage_(content)
        if len(buff) < 7:
            self._erroroutinfor_()
            raise Exception("UART communication failure")
        if buff[0] != 0x55 or buff[1] != 0x77:
            self._erroroutinfor_()
            raise Exception("UART communication failure")
        return buff
