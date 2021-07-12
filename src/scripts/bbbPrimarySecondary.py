#!/usr/bin/python-sirius
# -*- coding: utf-8 -*-

import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.UART as UART
import sys

# ----- CONSTANTS
PRIMARY = 1
SECONDARY = 2

# ----- GPIO PINS
inputPin = "P9_12"
outputPin = "P9_14"
GPIO.setup(inputPin, GPIO.IN)
GPIO.setup(outputPin, GPIO.OUT)

# ----- UART Config
UART.setup("UART4")

if "clean" in sys.argv:
    GPIO.output(outputPin, GPIO.LOW)
    exit(0)

# ----- CHECK STATUS
# Secondary
if(GPIO.input(inputPin)):
    GPIO.output(outputPin, GPIO.LOW)
    exit(SECONDARY)
# Primary
else:
    GPIO.output(outputPin, GPIO.HIGH)
    exit(PRIMARY)
