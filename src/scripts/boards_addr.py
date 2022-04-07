#!/usr/bin/python-sirius
import logging
from math import log
from CountingPRU import *
from Adafruit_BBIO import GPIO


def update_file(file_path="./", value=""):
    with open("{}.addr.log".format(file_path), "w") as address:
        address.write(str(value) + "\n")
        address.close()

class CountingPRU_addr:
    def __init__(self, clock = 5e5):

        self.clk_default = clock

        self.CH1 = "P9_13"
        self.CH3 = "P9_14"
        
        self.CH2 = "P9_15"
        self.CH4 = "P9_16"

        self.logger = logging.getLogger()
        self.logger.info("Checking Board Address - CountingPRU")

        for channel in [self.CH1, self.CH2, self.CH3, self.CH4]:
            GPIO.setup(channel, GPIO.OUT)
            GPIO.output(channel, GPIO.LOW)

    def autoConfig_Available(self):

        for channel in [self.CH1, self.CH3]:
            GPIO.output(channel, GPIO.HIGH)
           
        for channel in [self.CH2, self.CH4]:
            GPIO.output(channel, GPIO.LOW)

        Init()
        counting = sum(Counting(1)[6:])
        Close()

        status = abs(counting - 100000) < 10000

        for channel in [self.CH1, self.CH3]:
            GPIO.output(channel, GPIO.LOW)

        self.logger.info("Auto configuration status: {}".format(status))
        return(status)

    def addr(self):
        
        if not(self.check24V()):
            self.logger.warning("Something wrong with 24Vdc.")
            return(-1)

        for channel in [self.CH1, self.CH2, self.CH3, self.CH4]:
            GPIO.output(channel, GPIO.LOW)

        Init()
        counting = sum(Counting(1)[6:])
        Close()

        if counting == 0:
            self.logger.warning("It is not available addressing by hardware")
            return(None)

        else:
            addr = int(round(log(self.clk_default/counting)/log(2), 0))

        self.logger.info("Board Address is {}".format(addr))
        return(addr)


    def check24V(self):
        
        for channel in [self.CH2, self.CH4]:
            GPIO.output(channel, GPIO.HIGH)
           
        for channel in [self.CH1, self.CH3]:
            GPIO.output(channel, GPIO.LOW)
            
        Init()
        counting = sum(Counting(1)[6:])
        Close()

        status = abs(counting - 100000) < 10000

        self.logger.info("+24Vdc Available status: {}".format(status))
        return(status)

class Simar_addr:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.info("Checking Board Address - SIMAR")

        self.addr_pins = ["P9_26", "P9_25", "P9_41", "P9_23", "P9_24"]

        for pin in self.addr_pins:
            GPIO.setup(pin, GPIO.IN)

    def autoConfig_Available(self):
        '''If both addr 4 and addr 3 are TRUE, autoConfig is available'''

        return(GPIO.input("P9_25") == 1 and GPIO.input("P9_26") == 1)

    def addr(self):
        addressing = 0
        for pow, pin in enumerate(self.addr_pins[:-2]):
            addressing += GPIO.input(pin)*(2**pow)

        return(addressing)

    @staticmethod
    def check():
        from Adafruit_BBIO import ADC
        ADC.setup()
        volts = ADC.read("P9_33") * 1.8

        return(abs(volts * 11 - 5) < 0.2)

if __name__ == "__main__":
    simar = Simar_addr()
    print(f"Is Simar? {Simar_addr.check()}\
            Addressing: {simar.addr()}\
            AutoConfig: {simar.autoConfig_Available()}")
