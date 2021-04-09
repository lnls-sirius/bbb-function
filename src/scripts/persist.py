#!/usr/bin/python
import json
import logging
from datetime import datetime
from consts import RES_FILE, BAUDRATE_FILE, DEVICE_JSON
from logger import get_logger

logger = get_logger("Whoami")


def persist_info(device, baud, exit_code, details="No details."):
    """
    This method persist the information about which device is connected to this sbc.
    The info is stored using the following format:
    device_info = {'device': device, 'baudrate': baud, 'details': details, 'time': str(datetime.now())}
    Where:
    'device' is  the common.entity.entities Type."DEVICE".
    'details' a simple description.
    'time' the string representation os a python time object at the time this information has been defined.
    'baudrate' is the baudrate used for communicate to the connected device.
    """
    if exit_code != None:
        write_info(RES_FILE, exit_code)
    if type(baud) != int:
        raise TypeError("baud type is incorrect. ", baud)

    write_info(BAUDRATE_FILE, str(baud))

    device_info = {
        "device": device,
        "baudrate": baud,
        "details": str(exit_code) + " -  " + details,
        "time": str(datetime.now()),
    }

    logger.info("Device Identified !")
    write_info(DEVICE_JSON, json.dumps(device_info))
    exit(0)


def write_info(file_name, data):
    logger.info("Persisting {} at {}.".format(data, file_name))
    file = open(file_name, "w+")
    file.writelines(data)
    file.close()
