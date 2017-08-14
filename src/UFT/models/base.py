#!/usr/bin/env python
# encoding: utf-8
"""Base Model for Cororado PGEM I2C functions
"""
__version__ = "0.1"
__author__ = "@fanmuzhi, @boqiling"
__all__ = ["PGEMBase"]

import logging
import struct
import re
import time
from dut import DUT

logger = logging.getLogger(__name__)

# EEPROM dict for coronado
EEP_MAP = [{"name": "MODEL", "addr": 0x000, "length": 16, "type": "str"},
           {"name": "ES_FWREV0", "addr": 0x010, "length": 1, "type": "int"},
           {"name": "ES_FWREV1", "addr": 0x011, "length": 1, "type": "int"},
           {"name": "ES_HWREV", "addr": 0x012, "length": 1, "type": "int"},
           {"name": "CAPPN", "addr": 0x020, "length": 16, "type": "str"},
           {"name": "SN", "addr": 0x030, "length": 8, "type": "str"},
           {"name": "PCBVER", "addr": 0x040, "length": 2, "type": "str"},
           {"name": "MFDATE", "addr": 0x042, "length": 4, "type": "str"},
           {"name": "MFNAME", "addr": 0x046, "length": 2, "type": "str"},
           {"name": "CINIT", "addr": 0x050, "length": 2, "type": "int"},
           {"name": "MINTEMP", "addr": 0x060, "length": 1, "type": "int"},
           {"name": "MAXTEMP", "addr": 0x061, "length": 1, "type": "int"},
           {"name": "ES_CHRGE_TIMEOUT", "addr": 0x080, "length": 2, "type": "int"},
           {"name": "MIN_ES_OPERATING_TEMP", "addr": 0x082, "length": 1, "type": "int"},
           {"name": "MAX_ES_OPERATING_TEMP", "addr": 0x083, "length": 1, "type": "int"},
           {"name": "ES_TECH", "addr": 0x084, "length": 1, "type": "int"},
           {"name": "SPECCAP", "addr": 0x085, "length": 2, "type": "int"},
           {"name": "PID", "addr": 0x087, "length": 2, "type": "int"},
           {"name": "VPD_REV", "addr": 0x0FD, "length": 1, "type": "int"},
           {"name": "VPD_CRC", "addr": 0x0FE, "length": 2, "type": "int"},
           {"name": "LASTCAP", "addr": 0x100, "length": 1, "type": "int"},
           {"name": "MINCAP", "addr": 0x101, "length": 1, "type": "int"},
           {"name": "MAXCAP", "addr": 0x102, "length": 1, "type": "int"},
           {"name": "MINVCAP", "addr": 0x103, "length": 1, "type": "int"},
           {"name": "MAXVCAP", "addr": 0x104, "length": 1, "type": "int"},
           {"name": "MCAPINT", "addr": 0x105, "length": 1, "type": "int"},
           {"name": "ES_RUNTIME0", "addr": 0x200, "length": 1, "type": "int"},
           {"name": "ES_RUNTIME1", "addr": 0x201, "length": 1, "type": "int"},
           {"name": "T_LASTPF", "addr": 0x202, "length": 4, "type": "int"},
           {"name": "PWRCYCS", "addr": 0x206, "length": 2, "type": "int"},
           {"name": "RUNLOG_IDX", "addr": 0x300, "length": 2, "type": "int"}
           ]

# PGEM ID write to saphire.
PGEM_ID = {0: "A", 1: "B", 2: "C", 3: "D"}

BARCODE_PATTERN = re.compile(
    r'^(?P<SN>(?P<PN>AGIGA\d{4}-\d{3}\w{3})(?P<VV>\d{2})(?P<YY>[1-2][0-9])'
    r'(?P<WW>[0-4][0-9]|5[0-3])(?P<ID>\d{8})-(?P<RR>\d{2}))$')


class PGEMException(Exception):
    """PGEM Exception
    """
    pass


class PGEMBase(DUT):
    """PGEM Base Class, All models should be inheret from this base class.
    """

    def __init__(self, device, barcode, **kvargs):
        # slot number for dut on fixture location.
        # from 0 to 3, totally 4 slots in UFT
        self.slotnum = kvargs.get("slot", 0)

        # I2C adapter device
        self.device = device

        # barcode
        self.barcode = barcode
        r = BARCODE_PATTERN.search(barcode)
        if r:
            self.barcode_dict = r.groupdict()
            self.partnumber = self.barcode_dict["PN"]
            self.revision = self.barcode_dict["RR"]
        else:
            raise PGEMException("Unvalide barcode.")

    @staticmethod
    def _query_map(mymap, **kvargs):
        """method to search the map (the list of dict, [{}, {}])
        :params mymap:  the map to search
                kvargs: query conditon key=value, key should be in the dict.
        :return: the dict match the query contdtion or None.
        """
        r = mymap
        for k, v in kvargs.items():
            r = filter(lambda row: row[k] == v, r)
        return r

    def read_vpd_byname(self, reg_name):
        """method to read eep_data according to eep_name
        eep is one dict in eep_map, for example:
        {"name": "CINT", "addr": 0x02B3, "length": 1, "type": "int"}
        :param reg_name: register name, e.g. "PCA"
        :return value of the register
        """
        eep = self._query_map(EEP_MAP, name=reg_name)[0]
        start = eep["addr"]  # start_address
        length = eep["length"]  # length
        typ = eep["type"]  # type
        datas=[]
        self.device.slave_addr = 0x14
        for i in range(length):
            self.device.write_reg(0x00,(start+i) & 0xFF)
            self.device.write_reg(0x01,((start+i)>>8) & 0xFF)
            #print start+i
            self.device.sleep(5)
            temp=self.device.read_reg(0x02)
            datas.append(temp[0])

        if (typ == "word"):
            val = 0
            for i in range(0, len(datas)):
                val += datas[i] << 8 * i
        if (typ == "str"):
            val = ''.join(chr(i) for i in datas)
        if (typ == "int"):
            val = 0
            for i in range(0, len(datas)):
                val += datas[i] << 8 * i
        return val

    def read_vpd_byaddress(self, address):
        """method to read eep_data according to eep_address
        :return value of the register
        added by pzho
        """
        self.device.write_reg(0x00,address & 0xFF)
        self.device.write_reg(0x01,(address>>8) & 0xFF)
        val = self.device.read_reg(0x02)
        return val

    def dump_vpd(self):
        ret = []
        self.device.slave_addr = 0x14
        for i in range(0x000, 0xFFF):
            ret.append(self.read_vpd_byaddress(i)[0])
        logger.info(ret)
        return ret

    def read_vpd(self):
        """method to read out EEPROM info from dut
        :return a dict of vpd names and values.
        """
        dut = {}
        for eep in EEP_MAP:
            reg_name = eep["name"]
            dut.update({reg_name.lower(): self.read_vpd_byname(reg_name)})
        # set self.values to write to database later.
        for k, v in dut.items():
            setattr(self, k, v)
        #print dut
        return dut

    @staticmethod
    def load_bin_file(filepath):
        """read a file and transfer to a binary list
        :param filepath: file path to load
        """
        datas = []
        f = open(filepath, 'rb')
        s = f.read()
        for x in s:
            rdata = struct.unpack("B", x)[0]
            datas.append(rdata)
        return datas

    def write_vpd_byaddress(self, address, data):
        self.device.write_reg(0x00,address & 0xFF)
        self.device.write_reg(0x01,(address>>8) & 0xFF)
        self.device.sleep(5)
        self.device.write_reg(0x02,data & 0xFF)

    def write_vpd(self, filepath, write_id):
        """method to write barcode information to PGEM EEPROM
        :param filepath: the ebf file location.
        """
        buffebf = self.load_bin_file(filepath)
        # [ord(x) for x in string]
        id = [ord(x) for x in self.barcode_dict['ID']]
        yyww = [ord(x) for x in (self.barcode_dict['YY'] +
                                 self.barcode_dict['WW'])]
        vv = [ord(x) for x in self.barcode_dict['VV']]

        # id == SN == Product Serial Number
        eep = self._query_map(EEP_MAP, name="SN")[0]
        buffebf[eep["addr"]: eep["addr"] + eep["length"]] = id

        # yyww == MFDATE == Manufacture Date YY WW
        eep = self._query_map(EEP_MAP, name="MFDATE")[0]
        buffebf[eep["addr"]: eep["addr"] + eep["length"]] = yyww

        # vv == ENDUSR == Manufacturer Name
        eep = self._query_map(EEP_MAP, name="MFNAME")[0]
        buffebf[eep["addr"]: eep["addr"] + eep["length"]] = vv

        self.device.slave_addr = 0x14
        # can be start with 0x41, 0x00 for ensurance.
        self.device.write_reg(0x40,0x45) # enable EEP write

        for i in range(0x00, len(buffebf)):
            self.write_vpd_byaddress(i, buffebf[i])
            self.device.sleep(5)
            #print str(i)
            #print buffebf[i]
        # readback to check
        #print self.barcode_dict
        assert self.barcode_dict["ID"] == self.read_vpd_byname("SN")
        assert (self.barcode_dict["YY"] + self.barcode_dict["WW"]) == \
               self.read_vpd_byname("MFDATE")
        assert self.barcode_dict["VV"] == self.read_vpd_byname("MFNAME")


    def control_led(self, status="off"):
        """method to control the LED on DUT chip PCA9536DP
        :param status: status=1, LED off, default. staus=0, LED on.
        """
        LOGIC = {"on": 0, "off": 1}
        status = LOGIC.get(status)
        logger.debug("LED: {0}".format(status))
        if (status is None):
            raise PGEMException("wrong LED status is set")

        self.device.slave_addr = 0x41
        REG_OUTPUT = 0x01
        REG_CONFIG = 0x03

        # config PIO to output
        wdata = [REG_CONFIG, 0x00]
        self.device.write(wdata)

        # set LED status
        out = status << 1
        wdata = [REG_OUTPUT, out]
        self.device.write(wdata)


    def check_temp(self):
        """check temperature on SE97B of DUT.
        :return: temperature value
        """
        self.device.slave_addr = 0x14
        # check temp value
        val1 = self.device.read_reg(0x24, length=1)[0]
        val2 = self.device.read_reg(0x25, length=1)[0]
        temp=0.0
        if val1&0x04==0x04:
            temp=0.25
        if val1&0x08==0x08:
            temp = temp + 0.5
        if val1&0x10==0x10:
            temp = temp + 1
        if val1&0x20==0x20:
            temp = temp + 2
        if val1&0x40==0x40:
            temp = temp + 4
        if val1&0x80==0x80:
            temp = temp + 8
        if val2&0x01==0x01:
            temp = temp + 16
        if val2&0x02==0x02:
            temp = temp + 32
        if val2&0x04==0x04:
            temp = temp + 64
        if val2&0x08==0x08:
            temp = temp + 128
        logger.debug("temp value: {0}".format(temp))
        return temp

    def meas_vcap(self):
        self.device.slave_addr = 0x14
        # check temp value
        val = self.device.read_reg(0x27, length=1)[0]
        temp = float(val)/10
        logger.debug("Vcap value: {0}".format(temp))
        return temp

    def meas_vin(self):
        self.device.slave_addr = 0x14
        # check temp value
        val = self.device.read_reg(0x26, length=1)[0]
        temp = float(val)/10
        logger.debug("Vcap value: {0}".format(temp))
        return temp
    def meas_chg_time(self):
        self.device.slave_addr = 0x14
        # check temp value
        val = self.device.read_reg(0x28, length=1)[0]
        temp = int(val)
        logger.debug("CHG_TIME value: {0}".format(temp))
        return temp

    def read_hwready(self):
        self.device.slave_addr = 0x14
        # check temp value
        val = self.device.read_reg(0x20, length=1)[0]
        logger.debug("HWready value: {0}".format(val))
        #logger.info("HWready value: {0}".format(val))
        if val==0xA5:
            return True
        else:
            return False

    def read_PGEMSTAT(self, bit=None):
        self.device.slave_addr = 0x14
        if(bit==None):
            val = self.device.read_reg(0x23, 0x01)
        else:
            val = self.device.read_reg(0x23, 0x01)[bit]
        return val

    def read_GTG(self, bit=None):
        self.device.slave_addr = 0x14
        if(bit==None):
            val = self.device.read_reg(0x21, 0x01)
        else:
            val = self.device.read_reg(0x21, 0x01)[bit]
        return val

    def read_GTG_WARN(self, bit=None):
        self.device.slave_addr = 0x14
        if(bit==None):
            val = self.device.read_reg(0x22, 0x01)
        else:
            val = self.device.read_reg(0x22, 0x01)[bit]
        return val

    def reset_minmax(self):
        self.device.slave_addr = 0x14
        self.device.write_reg(0x05, 0xE6)
        logger.info("reset min max")
        time.sleep(5)

    def flush_ee(self):
        self.device.slave_addr = 0x14
        self.device.write_reg(0x41, 0x3A)
        logger.info("flush eeprom")
        time.sleep(1)

    def reset_sys(self):
        self.device.slave_addr = 0x14
        # reset register
        self.device.write_reg(0x04, 0xF4)
        logger.info("reset system")
        time.sleep(5)

    def start_cap(self):
        self.device.slave_addr = 0x14
        # reset register
        self.device.write_reg(0x03, 0x01)

    def shutdown_output(self):
        self.device.slave_addr = 0x14
        self.device.write_reg(0x06, 0xB4)
        logger.info("Shutdown output")


    def charge_status(self):
        self.device.slave_addr = 0x14
        # check temp value
        val1 = self.device.read_reg(0x23, length=1)[0]
        logger.info("PGEMSTAT value: {0}".format(val1))
        logger.debug("PGEMSTAT value: {0}".format(val1))
        val2 = self.device.read_reg(0x21, length=1)[0]
        logger.info("GTG value: {0}".format(val2))
        logger.debug("GTG value: {0}".format(val2))
        if ((val1|0xFE)==0xFE) & ((val2&0x09)==0x09):
            return True
        else:
            return False


class Diamond4(PGEMBase):
    """
    PGEM with LTC3350 Charge IC used instead of BQ24707 class.
    """

    def __init__(self, device, barcode, **kvargs):
        super(Diamond4, self).__init__(device, barcode, **kvargs)
        logger.debug("LTC3350 Charge IC used instead of BQ24707, unknown ID")
        # self.TEMP_SENSRO_ADDR = 0x1A



if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.DEBUG)

    from UFT.devices.aardvark import pyaardvark
    #from dut import DUT
    adk = pyaardvark.Adapter()
    barcode1 = "AGIGA9811-001BCA02143900000228-01"
    dut = PGEMBase(device=adk,
                               slot=1,
                               barcode=barcode1)
    adk.slave_addr = 0x70  # 0111 0000
    wdata=[0x01]
    adk.write(wdata)
    adk.slave_addr=0x14
    dut.device.sleep(5)
    reg_value=adk.read_reg(0x20)[0]
    print reg_value
    print("aaaa")

    temp = dut.check_temp()
    print "temp: ", temp
    dut.write_vpd('C:\Agigga\JOB_TRANSFER\UFT_source_code\UFT_source_code_Garnet\Garnet_VPD.ebf',1)
    dut.read_vpd()
    adk.close()
