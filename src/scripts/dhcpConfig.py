#!/usr/bin/python-sirius
# -*- coding: utf-8 -*-

from os import system
from time import sleep
from subprocess import getoutput
import serial
import logging
import Adafruit_BBIO.GPIO as GPIO
from PRUserial485 import PRUserial485_address
from counters_addr import Addressing
from autoConfig import AutoConfig


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)-15s %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')
logger = logging.getLogger('key_dhcp')


LED_PIN = "P8_28"

COUNTINGPRU_ADDRESS = 0
SERIALXXCON_ADDRESS = 21

        

def dhcp():
    '''
    Set IP to DHCP
    '''
    service = ""
    while(service == ""):
        service = getoutput("(connmanctl services | awk '{print $3}')")
    logger.info("Ethernet service {}".format(service))
    system("connmanctl config {} --ipv4 dhcp".format(service))

def led():		
    '''
    Shows the user that the IP has been configured
    TODO: BLINK ACCORDING TO NEW IP ADDRESS !
    '''
    for i in range(40):
        GPIO.output(LED_PIN, not(GPIO.input(LED_PIN)))
        sleep(0.05)


if __name__ == '__main__':
    logger.info("Verificando condicao DHCP em Hardware")

    # ----------------------------------
    # Led configuration
    # ----------------------------------
    GPIO.setup(LED_PIN, GPIO.OUT)    
    GPIO.output(LED_PIN, GPIO.LOW)


    '''
    # ----------------------------------
    # Check whether AUTOCONFIG is enabled
    # ----------------------------------
    # COUNTINGPRU
    if(PRUserial485_address() == COUNTINGPRU_ADDRESS):
        counter = Addressing()
        system("/root/counting-pru/src/DTO_CountingPRU.sh")
        for i in range(5):
            AUTOCONFIG = counter.autoConfig_Available()
            if AUTOCONFIG:
                break
            sleep(2)
    # SERIALxxCON   
    elif(PRUserial485_address() == SERIALXXCON_ADDRESS):
        for i in range(5):
            try:
                AUTOCONFIG = serial.Serial("/dev/ttyUSB0").cts
                if AUTOCONFIG:
                    break
            except:
                AUTOCONFIG = False
                sleep(2)
    '''

    AUTOCONFIG = AutoConfig().status
    logger.info(AUTOCONFIG)


    # ----------------------------------
    # Apply DHCP config if needed
    # ----------------------------------
    # COUNTINGPRU
    if(PRUserial485_address() == COUNTINGPRU_ADDRESS):
        logger.info("Contadora detectada")

        if AUTOCONFIG:
            logger.info("Configurando DHCP")
            dhcp()
            led()
    # SERIALxxCON        
    elif(PRUserial485_address() == SERIALXXCON_ADDRESS):
        for pin in ["P8_11", "P8_12"]:
            GPIO.setup(pin, GPIO.IN)
        #Check if the keys are set to the DHCP position
        DHCPmode_switches = (GPIO.input("P8_11") == 1 and GPIO.input("P8_12") == 0)
                                                                                                                
        if (AUTOCONFIG or DHCPmode_switches):
            logger.info("AUTOCONFIG enabled. Configuring DHCP")
            dhcp()
            led()
