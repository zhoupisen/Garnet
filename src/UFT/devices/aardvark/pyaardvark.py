#!/usr/bin/env python
# encoding: utf-8

"""i2c_aapter.py: API for aardvark i2c aapter.
the device can be found at http://www.totalphase.com/products/aardvark_i2cspi/
And rewrite the I2C part of original API aardvark_py.py
"""

__version__ = "1.1.0"
__author__ = "@dqli"
__all__ = ["Adapter"]

import time
import logging
from array import array

logger = logging.getLogger(__name__)

DEFAULT_REG_VAL = 0xFF


class USBI2CAdapterException(Exception):
    pass


def raise_i2c_ex():
    raise USBI2CAdapterException("IIC access wrong")


def array_u08(n):  return array('B', '\0' * n)


def array_u16(n):  return array('H', '\0\0' * n)


def array_u32(n):  return array('I', '\0\0\0\0' * n)


def array_u64(n):  return array('K', '\0\0\0\0\0\0\0\0' * n)


def array_s08(n):  return array('b', '\0' * n)


def array_s16(n):  return array('h', '\0\0' * n)


def array_s32(n):  return array('i', '\0\0\0\0' * n)


def array_s64(n):  return array('L', '\0\0\0\0\0\0\0\0' * n)


class Adapter(object):
    '''USB-I2C Aapter API Class
    '''

    OccupyPort = 0
    slave_addr = 0

    def __init__(self, device):
        self.device = device
        pass

    def __del__(self):
        pass

    def select_channel(self, chnum):
        self.OccupyPort = chnum

    def write(self, wata):
        '''write ata to slave address
        ata can be byte or array of byte
        '''
        #if (type(wata) == int):
        #    ata_out = array('B', [wata])
        #    length = 1
        #elif (type(wata) == list):
        #    ata_out = array('B', wata)
        #    length = len(wata)
        #else:
        #    raise TypeError("i2c ata to be written is not valid")
        length = len(wata)
        ata_out=wata
        ret = self.device.iic_write(self.OccupyPort, self.slave_addr, length, ata_out)

        if (ret != 0):
            raise_i2c_ex()

    def read(self, reg_addr, length):
        '''read 1 byte from slave address
        '''
        # read 1 byte each time for easy
        # length = 2
        #ata_in = array_u08(length)
        ata_in = [reg_addr]
        ret = self.device.iic_read(self.OccupyPort, self.slave_addr, length, ata_in)

        #if (ret != 0):
            #raise_i2c_ex()
        #val = ata_in
        return ret

    def write_reg(self, reg_addr, wata):
        '''
        Write ata list to slave device
        If write to slave device's register, ata_list = [reg_addr, wata]
        reg_addr: register address offset
        wata: ata to be write to SMBus register
        '''
        # ata_out must be unsigned char
        if (type(wata) == int):
            ata_out = [reg_addr, wata]
        elif (type(wata) == list):
            ata_out = [reg_addr] + wata
        else:
            raise TypeError("i2c ata to be written is not valid")
        self.write(ata_out)

    def read_reg(self, reg_addr, length=1):
        '''
        Read ata from slave device's register
        write the [reg_addr] to slave device first, then read back.
        :rtype : object
        reg_addr: register address offset
        '''
        val = DEFAULT_REG_VAL
        #self.write(reg_addr)

        # read register ata
        val = self.read(reg_addr, length)
        return val

    def sleep(self, ms):
        '''sleep for specified number of milliseconds
        '''
        time.sleep(ms*0.001)


if __name__ == "__main__":
    pass