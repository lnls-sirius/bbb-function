#!/usr/bin/python-sirius
# -*- coding: utf-8 -*-

from os import system
from time import sleep
from subprocess import getoutput
import serial
import logging
import Adafruit_BBIO.GPIO as GPIO
from PRUserial485 import PRUserial485_address
import socket
from logger import get_logger

logger = get_logger("key_dhcp")

LED_PIN = "P8_28"

CONFIGURED_SUBNETS = ["102", "103"]


def get_subnet():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't have to be reachable
        s.connect(("10.128.101.100", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP.split(".")[2]


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
    """
    for i in range(40):
        GPIO.output(LED_PIN, not (GPIO.input(LED_PIN)))
        sleep(0.05)


if __name__ == "__main__":
    logger.info("Verificando condicao DHCP em Hardware")

    device_addr = PRUserial485_address()

    GPIO.setup(LED_PIN, GPIO.OUT)  # Led configuration
    GPIO.output(LED_PIN, GPIO.LOW)

    if get_subnet() in CONFIGURED_SUBNETS:
        for i in range(5):
            try:
                AUTOCONFIG = serial.Serial("/dev/ttyUSB0").cts
            except:
                AUTOCONFIG = False
                sleep(2)
    else:
        logger.info("Subnet not yet configured!")
        AUTOCONFIG = False

    # CONTADORA
    if device_addr == 0:
        logger.info("Contadora detectada")

        for en_FF in ["P8_43", "P8_44", "P8_45", "P8_46", "P9_29", "P9_31"]:  # Enable Flip-Flops
            sleep(0.05)
            GPIO.setup(en_FF, GPIO.OUT)
            sleep(0.05)
            GPIO.output(en_FF, GPIO.HIGH)

        sleep(1)  # Sleep until FF set its output, frequency of input oscillator must be higher than 1 Hz
        state = ""
        for pin in ["P8_39", "P8_40", "P8_41", "P8_42", "P9_28", "P9_30"]:
            GPIO.setup(pin, GPIO.IN)
            sleep(0.05)
            state += str(GPIO.input(pin))

        if state == "101010":
            logger.info("Configurando DHCP")
            dhcp()
            led()

    # SERIALxxCON
    else:
        for pin in ["P8_11", "P8_12"]:
            GPIO.setup(pin, GPIO.IN)
        # Check if the keys are set to the DHCP position
        DHCPmode_switches = GPIO.input("P8_11") == 1 and GPIO.input("P8_12") == 0

        if AUTOCONFIG or DHCPmode_switches:
            logger.info("AUTOCONFIG enabled. Configuring DHCP")
            dhcp()
            led()
