#!/usr/bin/python-sirius
# -*- coding: utf-8 -*-

import argparse
import json
import logging
import time
import Adafruit_BBIO.UART as UART
from serial import Serial
from os import path, remove

from consts import *
from persist import persist_info, write_info
from logger import get_logger
from devices import (
    mbtemp,
    counting_pru,
    power_supply_pru,
    thermo_probe,
    mks9376b,
    agilent4uhv,
    reset,
    spixconv,
    simar,
)

logger = get_logger("detectEquipment")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--reset', action='store_true')
    parser.add_argument('--secondary', action='store_true')

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.reset:
        logger.info("Reseting json file...")
        reset()
        exit(0)

    if args.secondary:
        logger.info('Getting configuration from primary BBB...')
        UART.setup("UART4")

        s = Serial(port="/dev/ttyO4", baudrate=115200, timeout=1)
        
        device_info = b''
        while (device_info == b''):
            device_info = s.read(1000).split(b'-----')[0]

        device_info = json.loads(device_info)

        write_info(DEVICE_JSON, json.dumps(device_info))
        write_info(BAUDRATE_FILE, str(device_info['baudrate']))
        write_info(RES_FILE, device_info['details'].split(" -  ")[0])
        exit(0)

    logger.info('Iterating through possible devices ...')

    try:
        remove(RES_FILE)
    except:
        pass
    try:
        remove(BAUDRATE_FILE)
    except:
        pass

    # Loop until detect something
    while not path.isfile(RES_FILE) or not path.isfile(BAUDRATE_FILE):
        logger.info('Searching...')
        try:
            power_supply_pru()  # Power supplies
            mks9376b()          # Vacuum gauges
            agilent4uhv()       # Ion pumps
            spixconv()          # Pulsed magnets
            mbtemp()            # Temperature measurements
            counting_pru()      # Gamma detectors
            # simar()
            # thermo_probe()
            # no_tty()
        except SystemExit:
            exit()
        except:
            logger.exception("Something wrong happened !")

        time.sleep(2.0)

    logger.info("End of the identification Script ...")
