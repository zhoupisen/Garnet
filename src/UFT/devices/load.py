#!/usr/bin/env python
# encoding: utf-8
"""API program for Agilent N3300A DC electronic Load.
RS232 communication based.
"""
__version__ = "0.0.1"
__author__ = "@fanmuzhi, @boqiling"
__all__ = ["DCLoad"]

import serial
import re
import logging
import time

logger = logging.getLogger(__name__)


class DCLoadException(Exception):
    pass


class DCLoad(object):

    OccupyPort = 0
    LoadMode = 'low'

    def __init__(self, device):
        self.device = device
        pass

    def __del__(self):
        pass

    def _write(self, msg):
        raise NotImplementedError()

    def _read(self):
        raise NotImplementedError()

    def _check_error(self):
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()

    def select_channel(self, chnum):
        self.OccupyPort = chnum

    def change_func(self, mode):
        raise NotImplementedError()

    def set_curr(self, curr):
        if curr > 1.2:
            self.LoadMode = 'high'
        else:
            self.LoadMode = 'low'

    def read_curr(self):
        raise NotImplementedError()

    def read_volt(self):
        raise NotImplementedError()

    def protect_on(self):
        raise NotImplementedError()

    def protect_off(self):
        raise NotImplementedError()

    def set_res(self, resistance):
        raise NotImplementedError()

    def input_on(self):
        self.device.InputOn(self.OccupyPort, self.LoadMode)
        pass

    def input_off(self):
        self.device.InputOff(self.OccupyPort)
        pass
