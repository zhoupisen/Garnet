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

    def __init__(self, port='COM0', baudrate=9600, **kvargs):
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
        OccupyPort = chnum

    def change_func(self, mode):
        raise NotImplementedError()

    def set_curr(self, curr):
        pass

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
        pass

    def input_off(self):
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    load = DCLoad(port="COM10", timeout=3)

    for i in range(1):
        load.select_channel(i)
        load.input_off()
        load.protect_on()

        load.change_func(DCLoad.ModeCURR)
        load.set_curr(0.8)

        # load.change_func(DCLoad.ModeRes)
        # load.set_res(20)     # 20 ohm

        load.input_on()

        print load.read_curr()
        print load.read_volt()

        time.sleep(2)
        load.input_off()
    print "finish."
