#!/usr/bin/python-sirius
# -*- coding: utf-8 -*-

from os import system
from time import sleep
from subprocess import getoutput
import Adafruit_BBIO.GPIO as GPIO
from PRUserial485 import PRUserial485_address
from logger import get_logger
from autoConfig import AutoConfig
from boards_addr import * # Do not remove

logger = get_logger("dhcpConfig")

LED_PIN = "P8_28"

COUNTINGPRU_ADDRESS = 0
SERIALXXCON_ADDRESS = 21


def dhcp():
    """
    Set IP to DHCP
    """
    service = ""
    while service == "":
        service = getoutput("(connmanctl services | awk '{print $3}')")
    logger.info("Ethernet service {}".format(service))
    system("connmanctl config {} --ipv4 dhcp".format(service))


def led():
    """
    Shows the user that the IP has been configured
    TODO: BLINK ACCORDING TO NEW IP ADDRESS !
    """
    for i in range(40):
        GPIO.output(LED_PIN, not (GPIO.input(LED_PIN)))
        sleep(0.05)


if __name__ == "__main__":
    logger.info("Verifying AUTOCONFIG/DHCP configuring in hardware...")

    # ----------------------------------
    # Led configuration
    # ----------------------------------
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.output(LED_PIN, GPIO.LOW)

    # ----------------------------------
    # AutoConfig Status
    # ----------------------------------
    AUTOCONFIG = AutoConfig().status

    # ----------------------------------
    # Apply DHCP config if needed
    # ----------------------------------
    # COUNTINGPRU, SIMAR
    if PRUserial485_address() == COUNTINGPRU_ADDRESS:
        if AUTOCONFIG:
            logger.info("AUTOCONFIG enabled. Configuring DHCP.")
            dhcp()
            led()

    # SERIALxxCON
    elif PRUserial485_address() == SERIALXXCON_ADDRESS:
        for pin in ["P8_11", "P8_12"]:
            GPIO.setup(pin, GPIO.IN)
        # Check if the keys are set to the DHCP position
        DHCPmode_switches = GPIO.input("P8_11") == 1 and GPIO.input("P8_12") == 0

        if AUTOCONFIG or DHCPmode_switches:
            if AUTOCONFIG:
                logger.info("AUTOCONFIG enabled. Configuring DHCP.")
            elif DHCPmode_switches:
                logger.info("SERIALxxCON red switches on DHCP position. Configuring DHCP.")
            dhcp()
            led()

    if not (AUTOCONFIG):
        logger.info("AUTOCONFIG disabled.")
