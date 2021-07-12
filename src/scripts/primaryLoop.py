#!/usr/bin/python-sirius
# -*- coding: utf-8 -*-
import Adafruit_BBIO.GPIO as GPIO
from bbb import BBB
import serial
import time
from consts import DEVICE_JSON

INFO_STREAMING_LOOP = 5 # seconds

LED = "P8_28"
CONFIG_JSON_PATH = '/opt/device.json'

def blinkLED():
    for _ in range (2):
        GPIO.output(LED, 1)
        time.sleep(0.1)
        GPIO.output(LED, 0)
        time.sleep(0.1)
    time.sleep(1)


# Open Config
with open(DEVICE_JSON, 'r') as reader:
    bbb_config = reader.read()


# Config UART
s = serial.Serial(port="/dev/ttyO4", baudrate=115200)

# Config LED
GPIO.setup(LED, GPIO.OUT)

# Continuous loop
# 1. Stream info
# 2. Blink LED (heartbeat)
# 3. Slave monitoring -----> ????
while True:
    s.write(bbb_config.encode())
    for i in range (INFO_STREAMING_LOOP):
        blinkLED()
