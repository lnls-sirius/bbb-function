#!/usr/bin/python-sirius
import logging, sys
from math import log
from CountingPRU import *
from Adafruit_BBIO import GPIO

class Addressing:
    def __init__(self, f_xtal = 8e6):

        self.clk_default = f_xtal / 2 ** 4

        self.CH1 = "P9_13"
        self.CH3 = "P9_14"

        self.logger = logging.getLogger()
        self.logger.info("Checking Board Address")

        for channel in [self.CH1, self.CH3]:
            GPIO.setup(channel, GPIO.OUT)
            GPIO.output(channel, GPIO.LOW)

    def update_file(self, file_path = "./" , value = ""):
        with open("{}.addr.log".format(file_path), "w") as address:
            address.write(str(value)+"\n")
            address.close()

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
        return(status)

    def addr(self):

        for channel in [self.CH1, self.CH3]:
            GPIO.output(channel, GPIO.LOW)

        Init()
        counting = sum(Counting(1)[6:])
        Close()

        if counting == 0:
            self.logger.warning("It is not avaiable addressing by hardware")
            return(None)

        elif abs(counting - 1953) < 50:
            addr = 7

        else:
            addr = int(round(log(self.clk_default/counting)/log(2), 0))

        self.logger.info("Board Address is {}".format(addr))
        return(addr)

if __name__ == "__main__":
    count = Addressing()
