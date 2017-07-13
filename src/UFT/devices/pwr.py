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

    def __init__(self):
        pass

    def __del__(self):
        pass

    def close(self):
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()

    def _checkerr(self):
        raise NotImplementedError()

    def selectChannel(self, node, ch):
        OccupyPort = ch

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
        pass

    def deactivateOutput(self):
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    ps = PowerSupply()
    logger.debug("Communicate to Node 5:")
    ps.selectChannel(node=5, ch=1)
    logger.debug("Set voltage and current:")
    setting = {"volt": 12.0, "curr": 2, "ovp": 13.0, "ocp": 3.0}
    ps.set(setting)
    ps.activateOutput()
    time.sleep(2)
    logger.debug(ps.measureVolt())
    logger.debug(ps.measureCurr())
    time.sleep(2)
    ps.deactivateOutput()
