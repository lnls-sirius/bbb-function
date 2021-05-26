#!/usr/bin/python-sirius
# -*- coding: utf-8 -*-

import Adafruit_BBIO.UART as UART
import Adafruit_BBIO.GPIO as GPIO
from bbb import BBB
import serial
import time

INFO_READING_LOOP = 2 # seconds

LED = "P8_28"

def blinkLED():
    for _ in range (1):
        GPIO.output(LED, 1)
        time.sleep(0.5)
        GPIO.output(LED, 0)
        time.sleep(0.5)

# Config UART
s = serial.Serial(port="/dev/ttyO4", baudrate=115200, timeout=INFO_READING_LOOP)

# Config LED
GPIO.setup(LED, GPIO.OUT)

# Continuous loop - Secondary BBB
# 1. Read info
# 2. Blink LED (heartbeat2)
# 3. ----> ????
while True:
    info = s.read(1000)
    for i in range (INFO_READING_LOOP):
        blinkLED()
