#!/bin/bash
#@todo: Those environment variables are for debugging purposes. They are meant to be set in a more elegant and flexible way.

# Socat Welcome Port
export SOCAT_PORT=4161
# Wich ip/mask that are allowed to connect to socat.
export SERVER_IP_ADDR="10.128.255.0/24"
# Serial port name to be used
export SOCAT_DEVICE="/dev/ttyUSB0"

# The whoami.py script will use the following environment variables.
# Do not use spaces!
export DEVICE_JSON="/opt/device.json"
export RES_FILE="/var/tmp/res"
export BAUDRATE_FILE="/var/tmp/baudrate"
export CONN_DEVICE="/dev/ttyUSB0"
export PRU_POWER_SUPPLY='PRU_POWER_SUPPLY'
export COUNTING_PRU='COUNTING_PRU'
export SERIAL_THERMO='SERIAL_THERMO'
export MBTEMP='MBTEMP'
export AGILENT4UHV='AGILENT4UHV'
export MKS937B='MKS937B'
export SPIXCONV='SPIXCONV'
export SIMAR='SIMAR'
export NOTTY='NOTTY'
