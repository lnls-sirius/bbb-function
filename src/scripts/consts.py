#!/usr/bin/python-sirius
from os import environ

FUNCTION_BASE = environ.get("FUNCTION_BASE", "/root/bbb-function")
FILE_FOLDER = FUNCTION_BASE + "/src/scripts"


RES_FILE = environ.get("RES_FILE")
BAUDRATE_FILE = environ.get("BAUDRATE_FILE")
DEVICE_JSON = environ.get("DEVICE_JSON")
PRU_POWER_SUPPLY = environ.get("PRU_POWER_SUPPLY")
COUNTING_PRU = environ.get("COUNTING_PRU")
SERIAL_THERMO = environ.get("SERIAL_THERMO")
MBTEMP = environ.get("MBTEMP")
AGILENT4UHV = environ.get("AGILENT4UHV")
MKS937B = environ.get("MKS937B")
SPIXCONV = environ.get("SPIXCONV")
NOTTY = environ.get("NOTTY")

SERVER_IP = "10.128.255.5"
#SERVER_IP = "10.0.6.69"
DEVICE_TYPE_COLUMN = "DEVICE_TYPE"
DEVICE_ID_COLUMN = "DEVICE_ID"
DEVICE_NAME_COLUMN = "DEVICE_NAME"
BBB_IP_1_COLUMN = "BBB_IP_1"
BBB_IP_2_COLUMN = "BBB_IP_2"
BBB_HOSTNAME_COLUMN = "BBB_HOSTNAME"
CONFIG_FILE = "/root/BBB-CONFIG.json"
AUTOCONFIG_FILE = "AUTOCONFIG.xlsx"
SEPARATOR = b"-----"


Device_Type = {
    0: "Undefined",
    1: "PowerSupply",
    2: "CountingPRU",
    3: "Thermo",
    4: "MBTemp",
    5: "4UHV",
    6: "MKS",
    7: "SPIxCONV",
}


TIMEOUT = 0.1
PORT = "/dev/ttyUSB0"
