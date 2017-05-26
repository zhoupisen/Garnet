#!/usr/bin/env python
# encoding: utf-8
"""Description: pgem parallel test on UFT test fixture.
Currently supports 4 duts in parallel.
"""

from UFT.config import PS_VOLT
from UFT.config import RESULT_LOG
from UFT.config import RESULT_DB
from UFT.config import SD_COUNTER
from UFT.config import START_VOLT
from UFT.config import CONFIG_DB
from UFT.config import DIAMOND4_LIST
from UFT.config import PS_OCP
from UFT.config import PS_OVP
from UFT.config import PS_CURR
from UFT.config import PS_CHAN
from UFT.config import PS_ADDR
from UFT.config import TOTAL_SLOTNUM
from UFT.config import LD_DELAY
from UFT.config import LD_PORT
from UFT.config import ADK_PORT
from UFT.config import INTERVAL


__version__ = "0.1"
__author__ = "@fanmuzhi, @boqiling"
__all__ = ["Channel", "ChannelStates"]

from UFT.devices import pwr, load, aardvark
from UFT.models import DUT_STATUS, DUT, Cycle, PGEMBase, Diamond4
from UFT.backend import load_config, load_test_item
from UFT.backend.session import SessionManager
from UFT.backend import simplexml
from UFT.config import *
import threading
from Queue import Queue
import logging
import time
import math
import os
import traceback
import datetime
import numpy as np

logger = logging.getLogger(__name__)


class ChannelStates(object):
    EXIT = -1
    INIT = 0x0A
    LOAD_DISCHARGE = 0x0C
    CHARGE = 0x0E
    PROGRAM_VPD = 0x0F
    CHECK_CAPACITANCE = 0x1A
    CHECK_ENCRYPTED_IC = 0x1B
    CHECK_TEMP = 0x1C
    DUT_DISCHARGE = 0x1D
    CHECK_POWER_FAIL = 0x1E


class Channel(threading.Thread):
    # aardvark
    adk = aardvark.Adapter(portnum=ADK_PORT)
    # setup load
    ld = load.DCLoad(port=LD_PORT, timeout=LD_DELAY)
    # setup main power supply
    ps = pwr.PowerSupply()

    def __init__(self, name, barcode_list, cable_barcodes_list, channel_id=0):
        """initialize channel
        :param name: thread name
        :param barcode_list: list of 2D barcode of dut.
        :param channel_id: channel ID, from 0 to 7
        :return: None
        """
        # channel number for mother board.
        # 8 mother boards can be stacked from 0 to 7.
        # use 1 motherboard in default.
        self.channel = channel_id

        # setup dut_list
        self.dut_list = []
        self.config_list = []
        self.barcode_list = barcode_list
        self.cable_barcodes_list = cable_barcodes_list

        # progress bar, 0 to 100
        self.progressbar = 0

        # counter, to calculate charge and discharge time based on interval
        self.counter = 0

        # pre-discharge current, default to 0.8A
        self.current = 2.0

        # exit flag and queue for threading
        self.exit = False
        self.queue = Queue()
        self.product_class = "Crystal"
        super(Channel, self).__init__(name=name)

    def read_volt(self, dut):
        val = dut.meas_vcap()
        return val

    def init(self):
        """ hardware initialize in when work loop starts.
        :return: None.
        """
         # setup load
        self.ld.reset()
        time.sleep(2)
        for slot in range(TOTAL_SLOTNUM):
            self.ld.select_channel(slot)
            self.ld.input_off()
            time.sleep(1)
            self.ld.protect_on()
            self.ld.change_func(load.DCLoad.ModeCURR)
            time.sleep(1)

        # setup power supply
        self.ps.selectChannel(node=PS_ADDR, ch=PS_CHAN)

        setting = {"volt": PS_VOLT, "curr": PS_CURR,
                   "ovp": PS_OVP, "ocp": PS_OCP}
        self.ps.set(setting)
        self.ps.activateOutput()
        time.sleep(2)
        volt = self.ps.measureVolt()
        curr = self.ps.measureCurr()
        if not ((PS_VOLT - 1) < volt < (PS_VOLT + 1)):
            self.ps.setVolt(0.0)
            logging.error("Power Supply Voltage {0} "
                          "is not in range".format(volt))
            raise AssertionError("Power supply voltage is not in range")
        if not (curr >= 0):
            self.ps.setVolt(0.0)
            logging.error("Power Supply Current {0} "
                          "is not in range".format(volt))
            raise AssertionError("Power supply current is not in range")

        # setup dut_list
        for i, bc in enumerate(self.barcode_list):
            if bc != "":
                # dut is present
                dut = PGEMBase(device=self.adk,
                               slot=i,
                               barcode=bc)
                if dut.partnumber in DIAMOND4_LIST:
                    self.product_class = "Diamond4"
                    dut = Diamond4(device=self.adk,
                                   slot=i,
                                   barcode=bc)
                dut.status = DUT_STATUS.Idle
                dut.cable_barcode = self.cable_barcodes_list[i]
                dut.testdate = datetime.datetime.utcnow()
                self.dut_list.append(dut)
                dut_config = load_config("sqlite:///" + CONFIG_DB,
                                         dut.partnumber, dut.revision)
                self.config_list.append(dut_config)
            else:
                # dut is not loaded on fixture
                self.dut_list.append(None)
                self.config_list.append(None)


    def reset_dut(self):
        """disable all charge and self-discharge, enable auto-discharge.
        just like the dut is not present.
        :return: None
        """
        for dut in self.dut_list:
            if dut is not None:
                self.switch_to_dut(dut.slotnum)
                # dut.write_ltc3350(0x17, 0x01)

                # disable charge
                dut.charge(status=False)

                # enable auto discharge
                self.switch_to_mb()
                #self.auto_discharge(slot=dut.slotnum, status=True)

                # empty the dut, one by one
                self.switch_to_dut(dut.slotnum)
                self.ld.select_channel(dut.slotnum)
                # val = self.read_volt(dut)
                self.ps.setVolt(0.0)
                time.sleep(1.5)
                val = self.ld.read_volt()
                if (val > START_VOLT):
                    # self.ps.setVolt(0.0)
                    self.ld.set_curr(self.current)
                    self.ld.input_on()
                    time.sleep(1.5)
                    dut.status = DUT_STATUS.Discharging
                while (val > START_VOLT):
                    # print "start_volt", val
                    # self.ps.setVolt(0.0)
                    # val = self.read_volt(dut)
                    val = self.ld.read_volt()
                    time.sleep(INTERVAL)
                self.ps.setVolt(PS_VOLT)
                time.sleep(1.5)
                self.ld.input_off()
                dut.status = DUT_STATUS.Idle

    def charge_dut(self):
        """charge
        """

        for dut in self.dut_list:
            if dut is None:
                continue
            config = load_test_item(self.config_list[dut.slotnum],
                                    "Charge")
            # print dut.slotnum
            if (not config["enable"]):
                continue
            if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                continue
            # disable auto discharge
            self.switch_to_mb()
            #self.auto_discharge(slot=dut.slotnum, status=False)
            self.switch_to_dut(dut.slotnum)

            # start charge
            dut.status = DUT_STATUS.Charging

        all_charged = False
        self.counter = 0
        start_time = time.time()
        time.sleep(5)
        #while (not dut.read_hwready) & ((time.time() - start_time)<200000):

        while (not all_charged):
            all_charged = True
            for dut in self.dut_list:
                if dut is None:
                    continue
                config = load_test_item(self.config_list[dut.slotnum],
                                        "Charge")
                if (not config["enable"]):
                    continue
                if (config["stoponfail"]) & \
                        (dut.status != DUT_STATUS.Charging):
                    continue
                self.switch_to_dut(dut.slotnum)
                if not dut.read_hwready():
                    time.sleep(5)
                this_cycle = Cycle()
                this_cycle.vin = dut.meas_vin()
                this_cycle.counter = self.counter
                this_cycle.time = time.time()
                try:
                    temperature = dut.check_temp()
                except aardvark.USBI2CAdapterException:
                    # temp ic not ready
                    temperature = 0
                this_cycle.temp = temperature
                this_cycle.state = "charge"
                self.counter += 1

                self.ld.select_channel(dut.slotnum)
                this_cycle.vcap = dut.meas_vcap()

                threshold = float(config["Threshold"].strip("aAvV"))
                ceiling = float(config["Ceiling"].strip("aAvV"))
                max_chargetime = config["max"]
                min_chargetime = config["min"]

                charge_time = this_cycle.time - start_time
                dut.charge_time = charge_time
                if (charge_time > max_chargetime):
                    all_charged &= True
                    dut.status = DUT_STATUS.Fail
                    dut.errormessage = "Charge Time Too Long."
                elif (dut.charge_status()):
                    if(ceiling >dut.meas_vcap() >= threshold)&(max_chargetime>dut.charge_time>min_chargetime):  #dut.meas_chg_time()
                        all_charged &= True
                        dut.status = DUT_STATUS.Idle  # pass
                    else:
                        dut.status = DUT_STATUS.Fail
                        dut.errormessage = "Charge Time or Vcap failed"
                else:
                    all_charged &= False
                dut.cycles.append(this_cycle)
                logger.info("dut: {0} status: {1} vcap: {2} "
                            "temp: {3} message: {4} ".
                            format(dut.slotnum, dut.status, this_cycle.vcap,
                                   this_cycle.temp, dut.errormessage))
            time.sleep(INTERVAL)

    def discharge_dut(self):
        """discharge
        """

        for dut in self.dut_list:
            if dut is None:
                continue
            config = load_test_item(self.config_list[dut.slotnum],
                                    "Discharge")
            if (not config["enable"]):
                continue
            if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                continue
            # disable auto discharge
            self.switch_to_mb()
            #self.auto_discharge(slot=dut.slotnum, status=False)
            # disable self discharge
            self.switch_to_dut(dut.slotnum)
            #dut.self_discharge(status=False)
            # disable charge
            #dut.charge(status=False)

            self.ld.select_channel(dut.slotnum)
            self.current = float(config["Current"].strip("aAvV"))
            self.ld.set_curr(self.current)  # set discharge current
            self.ld.input_on()
            dut.status = DUT_STATUS.Discharging

        # start discharge cycle
        all_discharged = False
        start_time = time.time()
        self.ps.setVolt(0.0)
        while (not all_discharged):
            all_discharged = True
            for dut in self.dut_list:
                if dut is None:
                    continue
                config = load_test_item(self.config_list[dut.slotnum],
                                        "Discharge")
                if (not config["enable"]):
                    continue
                if (config["stoponfail"]) & \
                        (dut.status != DUT_STATUS.Discharging):
                    continue
                self.switch_to_dut(dut.slotnum)
                # cap_in_ltc = dut.meas_capacitor()
                # print cap_in_ltc
                this_cycle = Cycle()
                this_cycle.vin = dut.meas_vin()
                try:
                    temperature = dut.check_temp()
                except aardvark.USBI2CAdapterException:
                    # temp ic not ready
                    temperature = 0
                this_cycle.temp = temperature
                this_cycle.counter = self.counter
                this_cycle.time = time.time()

                this_cycle.state = "discharge"
                self.ld.select_channel(dut.slotnum)
                this_cycle.vcap = dut.meas_vcap()
                # this_cycle.vcap = self.ld.read_volt()
                self.counter += 1

                threshold = float(config["Threshold"].strip("aAvV"))
                max_dischargetime = config["max"]
                min_dischargetime = config["min"]

                discharge_time = this_cycle.time - start_time
                dut.discharge_time = discharge_time
                if (discharge_time > max_dischargetime):
                    all_discharged &= True
                    self.ld.select_channel(dut.slotnum)
                    self.ld.input_off()
                    dut.status = DUT_STATUS.Fail
                    dut.errormessage = "Discharge Time Too Long."
                elif (this_cycle.vcap < threshold):
                    all_discharged &= True
                    self.ld.select_channel(dut.slotnum)
                    self.ld.input_off()
                    if (discharge_time < min_dischargetime):
                        dut.status = DUT_STATUS.Fail
                        dut.errormessage = "Discharge Time Too Short."
                    else:
                        dut.status = DUT_STATUS.Idle  # pass
                else:
                    all_discharged &= False
                dut.cycles.append(this_cycle)
                logger.info("dut: {0} status: {1} vcap: {2} "
                            "temp: {3} message: {4} ".
                            format(dut.slotnum, dut.status, this_cycle.vcap,
                                   this_cycle.temp, dut.errormessage))
            #time.sleep(0)
        self.ps.setVolt(PS_VOLT)



    def program_dut(self):
        """ program vpd of DUT.
        :return: None
        """
        time.sleep(5)
        for dut in self.dut_list:
            if dut is None:
                continue
            config = load_test_item(self.config_list[dut.slotnum],
                                    "Program_VPD")
            if (not config["enable"]):
                continue
            if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                continue
            self.switch_to_dut(dut.slotnum)
            if not dut.read_hwready():
                time.sleep(5)

            try:
                dut.write_vpd(config["File"], config["PGEMID"])
                dut.read_vpd()
                dut.program_vpd = 1
            except AssertionError:
                dut.status = DUT_STATUS.Fail
                dut.errormessage = "Programming VPD Fail"
                logger.info("dut: {0} status: {1} message: {2} ".
                            format(dut.slotnum, dut.status, dut.errormessage))



    def check_temperature_dut(self):
        """
        check temperature value of IC on DUT.
        :return: None.
        """
        for dut in self.dut_list:
            if dut is None:
                continue
            config = load_test_item(self.config_list[dut.slotnum],
                                    "Check_Temp")
            if (not config["enable"]):
                continue
            if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                continue
            self.switch_to_dut(dut.slotnum)
            temp = dut.check_temp()
            if not (config["min"] < temp < config["max"]):
                dut.status = DUT_STATUS.Fail
                dut.errormessage = "Temperature out of range."
                logger.info("dut: {0} status: {1} message: {2} ".
                            format(dut.slotnum, dut.status, dut.errormessage))



    def switch_to_dut(self, slot):
        """switch I2C ports by PCA9548A, only 1 channel is enabled.
        chnum(channel number): 0~7
        slotnum(slot number): 0~7
        """
        chnum = self.channel
        self.adk.slave_addr = 0x70 + chnum  # 0111 0000
        wdata = [0x01 << slot]

        # Switch I2C connection to current PGEM
        # Need call this function every time before communicate with PGEM
        self.adk.write(wdata)

    def switch_to_mb(self):
        """switch I2C ports back to mother board
           chnum(channel number): 0~7
        """
        chnum = self.channel
        self.adk.slave_addr = 0x70 + chnum  # 0111 0000
        wdata = 0x00

        # Switch I2C connection to mother board
        # Need call this function every time before communicate with
        # mother board
        self.adk.write(wdata)


    
    def calculate_capacitance(self):
        """ calculate the capacitance of DUT, based on vcap list in discharging.
        :return: capacitor value
        """

        for dut in self.dut_list:
            if dut is None:
                continue
            config = load_test_item(self.config_list[dut.slotnum],
                                    "Capacitor")
            if (not config["enable"]):
                continue
            if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                continue
            if dut.status != DUT_STATUS.Idle:
                continue
            self.switch_to_dut(dut.slotnum)
            dut.start_cap()
            time.sleep(1)
            logger.info("started cap measure")

        #close load and set PS
        self.ld.reset()
        time.sleep(2)
        # setup power supply
        self.ps.selectChannel(node=PS_ADDR, ch=PS_CHAN)
        setting = {"volt": PS_VOLT, "curr": PS_CURR,
                   "ovp": PS_OVP, "ocp": PS_OCP}
        self.ps.set(setting)
        self.ps.activateOutput()
        time.sleep(2)
        start_time = time.time()

        all_cap_mears=False
        while not all_cap_mears:
            all_cap_mears=True
            for dut in self.dut_list:
                if dut is None:
                    continue
                if dut.status != DUT_STATUS.Idle:
                    continue
                self.switch_to_dut(dut.slotnum)

                config = load_test_item(self.config_list[dut.slotnum],
                                "Capacitor")
                if config.has_key("Overtime"):
                    overtime=float(config["Overtime"])
                else:
                    overtime=600

                self.adk.slave_addr = 0x14
                val = self.adk.read_reg(0x23,0x01)[0]
                logger.info("PGEMSTAT.BIT2: {0}".format(val))
                vcap_temp=dut.meas_vcap()
                logger.info("dut: {0} vcap in cap calculate: {1}".format(dut.slotnum,vcap_temp))
                if (val | 0xFB)==0xFB: #PGEMSTAT.BIT2==0 CAP MEASURE COMPLETE
                    all_cap_mears &= True
                    val1 = dut.read_vpd_byaddress(0x100)[0] #`````````````````````````read cap vale from VPD``````````compare````````````````````````````
                    logger.info("capacitance_measured value: {0}".format(val1))
                    dut.capacitance_measured=val1
                    if not (config["min"] < val1 < config["max"]):
                        dut.status=DUT_STATUS.Fail
                        dut.errormessage = "Cap is over limits"
                        logger.info("dut: {0} capacitor: {1} message: {2} ".
                            format(dut.slotnum, dut.capacitance_measured,
                               dut.errormessage))
                elif time.time()-start_time > overtime:
                    all_cap_mears &= True
                    dut.status=DUT_STATUS.Fail
                    dut.errormessage = "Cap start over time"
                    logger.info("dut: {0} capacitor: {1} message: {2} ".
                        format(dut.slotnum, dut.capacitance_measured,
                               dut.errormessage))
                else:
                    all_cap_mears &= False
            time.sleep(2)

        #check capacitance ok
        for dut in self.dut_list:
            all_cap_ready=True
            if dut is None:
                continue
            if dut.status != DUT_STATUS.Idle:
                continue
            self.switch_to_dut(dut.slotnum)
            self.adk.slave_addr = 0x14
            val = self.adk.read_reg(0x21,0x01)[0]
            if not((val&0x02)==0x02):
                dut.status=DUT_STATUS.Fail
                dut.errormessage = "GTG.bit1 ==0 "
                logger.info("GTG.bit1 ==0")
            # check GTG_WARNING == 0x00
            temp=self.adk.read_reg(0x22)[0]
            logger.info("GTG_Warning value: {0}".format(temp))
            if not (temp==0x00):
                dut.status = DUT_STATUS.Fail
                dut.errormessage = "GTG_warning != 0x00"

    def save_db(self):
        # setup database
        # db should be prepared in cli.py
        sm = SessionManager()
        sm.prepare_db("sqlite:///" + RESULT_DB, [DUT, Cycle])
        session = sm.get_session("sqlite:///" + RESULT_DB)

        for dut in self.dut_list:
            if dut is None:
                continue
            for pre_dut in session.query(DUT). \
                    filter(DUT.barcode == dut.barcode).all():
                pre_dut.archived = 1
                session.add(pre_dut)
                session.commit()
            dut.archived = 0
            session.add(dut)
            session.commit()
        session.close()

    def save_file(self):
        """ save dut info to xml file
        :return:
        """
        for dut in self.dut_list:
            if dut is None:
                continue
            if not os.path.exists(RESULT_LOG):
                os.makedirs(RESULT_LOG)
            filename = dut.barcode + ".xml"
            filepath = os.path.join(RESULT_LOG, filename)
            i = 1
            while os.path.exists(filepath):
                filename = "{0}({1}).xml".format(dut.barcode, i)
                filepath = os.path.join(RESULT_LOG, filename)
                i += 1
            result = simplexml.dumps(dut.to_dict(), "entity")
            with open(filepath, "wb") as f:
                f.truncate()
                f.write(result)

    def prepare_to_exit(self):
        """ cleanup and save to database before exit.
        :return: None
        """
        for dut in self.dut_list:
            if dut is None:
                continue
            if (dut.status == DUT_STATUS.Idle):
                dut.status = DUT_STATUS.Pass
                msg = "passed"
            else:
                msg = dut.errormessage
            logger.info("TEST RESULT: dut {0} ===> {1}".format(
                dut.slotnum, msg))

        # save to xml logs
        self.save_file()

        # power off
        self.ps.deactivateOutput()

    def run(self):
        """ override thread.run()
        :return: None
        """
        while (not self.exit):
            state = self.queue.get()
            if (state == ChannelStates.EXIT):
                try:
                    self.prepare_to_exit()
                    self.exit = True
                    logger.info("Channel: Exit Successfully.")
                except Exception as e:
                    self.error(e)
            elif (state == ChannelStates.INIT):
                try:
                    logger.info("Channel: Initialize.")
                    self.init()
                    self.progressbar += 20
                except Exception as e:
                    self.error(e)
            elif (state == ChannelStates.CHARGE):
                try:
                    logger.info("Channel: Charge DUT.")
                    self.charge_dut()
                    self.progressbar += 20
                except Exception as e:
                    self.error(e)
            elif (state == ChannelStates.LOAD_DISCHARGE):
                try:
                    logger.info("Channel: Discharge DUT.")
                    self.discharge_dut()
                    self.progressbar += 20
                except Exception as e:
                    self.error(e)
            elif (state == ChannelStates.PROGRAM_VPD):
                try:
                    logger.info("Channel: Program VPD.")
                    self.program_dut()
                    self.progressbar += 10
                except Exception as e:
                    self.error(e)
            elif (state == ChannelStates.CHECK_TEMP):
                try:
                    logger.info("Channel: Check Temperature")
                    self.check_temperature_dut()
                    self.progressbar += 5
                except Exception as e:
                    self.error(e)
            elif (state == ChannelStates.CHECK_CAPACITANCE):
                try:
                    logger.info("Channel: Check Capacitor Value")
                    self.calculate_capacitance()
                    self.progressbar += 30
                except Exception as e:
                    self.error(e)
            else:
                logger.error("unknown dut state, exit...")
                self.exit = True

    def auto_test(self):
        self.queue.put(ChannelStates.INIT)
        self.queue.put(ChannelStates.PROGRAM_VPD)
        self.queue.put(ChannelStates.CHARGE)
        #self.queue.put(ChannelStates.PROGRAM_VPD)
        self.queue.put(ChannelStates.CHECK_CAPACITANCE)
        #self.queue.put(ChannelStates.CHECK_ENCRYPTED_IC)
        #self.queue.put(ChannelStates.CHECK_TEMP)
        #self.queue.put(ChannelStates.CHECK_POWER_FAIL)
        # self.queue.put(ChannelStates.DUT_DISCHARGE)
        self.queue.put(ChannelStates.LOAD_DISCHARGE)
        self.queue.put(ChannelStates.EXIT)
        self.start()

    def empty(self):
        for i in range(self.queue.qsize()):
            self.queue.get()

    def error(self, e):
        exc = sys.exc_info()
        logger.error(traceback.format_exc(exc))
        self.exit = True
        raise e

    def quit(self):
        self.empty()
        self.queue.put(ChannelStates.EXIT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # barcode = ["AGIGA9603-004BCA02144800000002-06",
    #            "AGIGA9603-004BCA02144800000002-06",
    #            "AGIGA9603-004BCA02144800000002-06",
    #            "AGIGA9603-004BCA02144800000002-06"]
    barcode = ["AGIGA9811-001BCA02143900000228-01"]
    ch = Channel(barcode_list=barcode, channel_id=0,
                 name="UFT_CHANNEL", cable_barcodes_list=[""])
    # ch.start()
    # ch.queue.put(ChannelStates.INIT)
    # ch.queue.put(ChannelStates.CHARGE)
    # ch.queue.put(ChannelStates.PROGRAM_VPD)
    # ch.queue.put(ChannelStates.CHECK_ENCRYPTED_IC)
    # ch.queue.put(ChannelStates.CHECK_TEMP)
    # ch.queue.put(ChannelStates.LOAD_DISCHARGE)
    # ch.queue.put(ChannelStates.CHECK_CAPACITANCE)
    # ch.queue.put(ChannelStates.EXIT)
    ch.auto_test()
    # ch.switch_to_mb()
    # ch.switch_to_dut(0)
    # ch.init()
    # ch.charge_dut()
    # ch.discharge_dut()
