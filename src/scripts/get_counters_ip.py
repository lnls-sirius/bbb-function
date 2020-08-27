#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import system
from time import sleep
from commands import getoutput
from PRUserial485 import PRUserial485_address

import sys
import socket
import logging
import Adafruit_BBIO.GPIO as GPIO

counters_ip = ['152','153','154']

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)-15s %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')
logger = logging.getLogger('get_counters_ip')

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return(s.getsockname()[0])

def ping_ips(node):
    ip_disponible = []
    for ip in counters_ip:
        out = system("ping -c 1 -n -W 2 {}".format('.'.join(i for i in node)+'.'+ip))
        if out: ip_disponible.append(ip)
    return(ip_disponible)

def set_ip(new_ip, gateway):
    service = ""
    while(service == ""):
        service = getoutput("(connmanctl services |awk '{print $3}')")

    logger.info("Ethernet service {}".format(service))
    logger.info("Setting IP address to {}".format(new_ip))
    system("connmanctl config {} --ipv4 manual {} 255.255.255.0 {} \
    --nameservers 10.0.0.71 10.0.0.72 ".format(service, new_ip, gateway))

def led(num):
    for i in range(num):
        GPIO.output("P8_28", GPIO.HIGH)
        sleep(1)
        GPIO.output("P8_28", GPIO.LOW)
        sleep(1)

if __name__ == '__main__':

    if PRUserial485_address() != 0:
        sys.exit()

    logger.info("Checking IP Availability for the Counter")

    GPIO.setup("P8_28", GPIO.OUT)    #Led configuration
    GPIO.output("P8_28", GPIO.LOW)

    my_ip = get_ip_address().split('.')

    if not(my_ip[-1] in counters_ip):
        a = ping_ips(my_ip[:-1])
        if len(a) == 1:
            set_ip('.'.join(i for i in my_ip[:-1])+'.'+a[0], '.'.join(i for i in my_ip[:-1])+'.1')
            led(int(a[0])-150)
