#!/usr/bin/python-sirius
import logging
from math import log
from CountingPRU import *
from Adafruit_BBIO import GPIO


def update_file(file_path="./", value=""):
    with open("{}.addr.log".format(file_path), "w") as address:
        address.write(str(value) + "\n")
        address.close()

class coutingPRU_addr:
    def __init__(self, f_xtal=8e6):

        self.clk_default = f_xtal / 2 ** 4

        self.CH1 = "P9_13"
        self.CH3 = "P9_14"

        self.logger = logging.getLogger()
        self.logger.info("Checking Board Address - CountingPRU")

        for channel in [self.CH1, self.CH3]:
            GPIO.setup(channel, GPIO.OUT)
            GPIO.output(channel, GPIO.LOW)

    def autoConfig_Available(self):

        for channel in [self.CH1, self.CH3]:
            GPIO.output(channel, GPIO.HIGH)

        Init()
        counting = sum(Counting(1)[6:])
        Close()

        status = abs(counting - 488) < 50

        for channel in [self.CH1, self.CH3]:
            GPIO.output(channel, GPIO.LOW)

        self.logger.info("Auto configuration status: {}".format(status))
        return status

    def addr(self):

        for channel in [self.CH1, self.CH3]:
            GPIO.output(channel, GPIO.LOW)

        Init()
        counting = sum(Counting(1)[6:])
        Close()

        if counting == 0:
            self.logger.warning("It is not avaiable addressing by hardware")
            return None

        elif abs(counting - 1953) < 50:
            addr = 7

        else:
            addr = int(round(log(self.clk_default / counting) / log(2), 0))

        self.logger.info("Board Address is {}".format(addr))
        return addr

class simar_addr:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.info("Checking Board Address - SIMAR")

        self.addr_pins = ["P9_26", "P9_25", "P9_24", "P9_23", "P9_41"]

        for pin in self.addr_pins:
            GPIO.setup(pin, GPIO.IN)

    def autoConfig_Available(self):
        '''If both addr 4 and addr 3 are TRUE, autoConfig are available'''

        return(GPIO.input("P9_41") == 1 and GPIO.input("P9_23") == 1)

    def addr(self):
        addressing = 0
        for pow, pin in enumerate(self.addr_pins[:-2]):
            addressing += GPIO.input("P9_41")*(2**pow)

        return(addressing)