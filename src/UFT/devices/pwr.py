#!/usr/bin/env python
# encoding: utf-8
"""pwr.py: API for SCPI commands for
kikusui PWR1600L though PIA4850 usb control model
"""

__version__ = "0.0.1"
__author__ = "@fanmuzhi, @boqiling"
__all__ = ["PowerSupply"]

import usbtmc
import re
import logging
import time

logger = logging.getLogger(__name__)


class PowerSupplyException(Exception):
    pass


class PowerSupply(object):

    OccupyPort = 0

    def __init__(self, device):
        self.device = device
        pass

    def __del__(self):
        pass

    def close(self):
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()

    def _checkerr(self):
        raise NotImplementedError()

    def selectChannel(self, ch):
        self.OccupyPort = ch

    def measureVolt(self):
        raise NotImplementedError()

    def measureCurr(self):
        raise NotImplementedError()

    def set(self, params):
        raise NotImplementedError()

    def setVolt(self, volt):
        raise NotImplementedError()

    def setCurr(self, curr):
        raise NotImplementedError()

    def setOVP(self, ovp):
        raise NotImplementedError()

    def setOCP(self, ocp):
        raise NotImplementedError()

    def activateOutput(self):
        self.device.OutputOn(self.OccupyPort)
        pass

    def deactivateOutput(self):
        self.device.OutputOff(self.OccupyPort)
        pass

    def isOutputOn(self):
        return self.device.isOutputOn(self.OccupyPort)
