#!/usr/bin/python-sirius
# # -*- coding: utf-8 -*-
import logging
import serial
import subprocess
import json
import re
import time
from xlrd import open_workbook
from consts import *
from bbb import BBB
from logger import get_logger

logger = get_logger("AutoConfig")


# AUTOCONFIG: RTS and CTS pins tied together (jumper)
for i in range(5):
    try:
        AUTOCONFIG = serial.Serial("/dev/ttyUSB0").cts
    except:
        AUTOCONFIG = False
        time.sleep(2)


class GetData:
    def __init__(self, datafile=AUTOCONFIG_FILE, subnet=""):
        try:
            _sheet = open_workbook(datafile).sheet_by_name(subnet)
            keys = [_sheet.cell(0, col_index).value for col_index in range(_sheet.ncols)]
            self.data = {}

            for row_index in range(1, _sheet.nrows):
                dev_type = _sheet.cell(row_index, keys.index(DEVICE_TYPE_COLUMN)).value
                if dev_type == "":
                    continue
                info = {keys[col_index]: _sheet.cell(row_index, col_index).value for col_index in range(_sheet.ncols)}
                info[DEVICE_ID_COLUMN] = [int(s) for s in re.findall(r"\d+", info[DEVICE_ID_COLUMN])]
                if dev_type in self.data:
                    self.data[dev_type].append(info)
                else:
                    self.data[dev_type] = [info]
        except:
            self.data = {}


if __name__ == "__main__":

    if AUTOCONFIG:
        mybeagle_config = ""

        # Get device.json from whoami.py and get identified equipment
        mybbb = BBB()

        mybbb.type = Device_Type[mybbb.node.type.code]
        mybbb.ids = [int(s) for s in re.findall(r"\d+", mybbb.node.details.split("\t")[0])]
        mybbb.currentIP = str(mybbb.get_network_specs()[1])
        mybbb.currentSubnet = mybbb.currentIP.split(".")[2]

        # Get devices from this subnet from the ConfigurationTable
        beagles = GetData(datafile=AUTOCONFIG_FILE, subnet=mybbb.currentSubnet)

        # Check if current BBB (type and devices found is on ConfigurationTable)
        if beagles.data:
            for bbb in beagles.data[mybbb.type]:
                # If PowerSupply, check their names instead of IDs
                if mybbb.type == "PowerSupply":
                    mybbb.PSnames = []
                    nodes = json.loads(mybbb.node.details.split("\t")[0].split("Names:")[-1].replace("'", '"'))
                    for node in nodes:
                        mybbb.PSnames.extend(node.split("/"))

                    if any(psname in bbb[DEVICE_NAME_COLUMN] for psname in mybbb.PSnames):
                        mybeagle_config = bbb
                # If not PowerSupply, check IDs
                else:
                    if any(id in bbb[DEVICE_ID_COLUMN] for id in mybbb.ids):
                        mybeagle_config = bbb

        # If BBB config is found, proceed with configuration from datafile
        if mybeagle_config:
            logger.info(
                "Found a compatible device in spreadsheet: {}. Proceed with BBB configuration!".format(mybeagle_config)
            )

            # Save found config into a json file
            with open(CONFIG_FILE, "w") as fp:
                json.dump(mybeagle_config, fp)

            # Update hostname
            logger.info("BBB hostname: {}".format(mybeagle_config[BBB_HOSTNAME_COLUMN]))
            mybbb.update_hostname(mybeagle_config[BBB_HOSTNAME_COLUMN])

            IP_AVAILABLE = subprocess.call(
                ["ping", "-c", "1", "-W", "1", mybeagle_config[BBB_IP_COLUMN]], stdout=subprocess.DEVNULL
            )
            subnet = mybeagle_config[BBB_IP_COLUMN].split(".")[2]
            # Update IP, if available
            if IP_AVAILABLE and subnet == mybbb.currentSubnet:
                logger.info("BBB IP: {}".format(mybeagle_config[BBB_IP_COLUMN]))
                mybbb.update_ip_address(
                    "manual",
                    new_ip_address=mybeagle_config[BBB_IP_COLUMN],
                    new_mask="255.255.255.0",
                    new_gateway="10.128.{}.1".format(subnet),
                )
            else:
                if not IP_AVAILABLE:
                    if mybeagle_config[BBB_IP_COLUMN] == mybbb.currentIP:
                        logger.info("BBB IP is already configured to {}.".format(mybeagle_config[BBB_IP_COLUMN]))
                    else:
                        logger.error(
                            "Desired IP {} is currently in use by another device.".format(
                                mybeagle_config[BBB_IP_COLUMN]
                            )
                        )
                else:
                    logger.error(
                        "Cannot change to IP {}, subnet is not compatible to current one ({}).".format(
                            mybeagle_config[BBB_IP_COLUMN], mybbb.currentSubnet
                        )
                    )

        # If BBB not found, keep DHCP and raise a flag!
        else:
            logger.error(
                "A compatible device was NOT found in spreadsheet. Verify if there is a config file at {}.".format(
                    CONFIG_FILE
                )
            )

            try:
                # Get previous config
                with open(CONFIG_FILE, "w") as fp:
                    file_config = json.loads(mybeagle_config, fp)

                # Configure hostname
                logger.info("BBB hostname: {}".format(file_config[BBB_HOSTNAME_COLUMN]))
                mybbb.update_hostname(file_config[BBB_HOSTNAME_COLUMN])

                # If same subnet and desided IP is available, proceed with IP configuration
                IP_AVAILABLE = subprocess.call(
                    ["ping", "-c", "1", "-W", "1", file_config[BBB_IP_COLUMN]], stdout=subprocess.DEVNULL
                )
                subnet = file_config[BBB_IP_COLUMN].split(".")[2]
                if IP_AVAILABLE and mybbb.currentSubnet == subnet:
                    logger.info("BBB IP {}".format(file_config[BBB_IP_COLUMN]))
                    mybbb.update_ip_address(
                        "manual",
                        new_ip_address=file_config[BBB_IP_COLUMN],
                        new_mask="255.255.255.0",
                        new_gateway="10.128.{}.1".format(subnet),
                    )
                else:
                    if not IP_AVAILABLE:
                        logger.error(
                            "Desired IP {} is currently in use by another device.".format(file_config[BBB_IP_COLUMN])
                        )
                    else:
                        logger.error(
                            "Cannot change to IP {}, subnet is not compatible to current one ({}).".format(
                                file_config[BBB_IP_COLUMN], mybbb.currentSubnet
                            )
                        )

            except:
                logger.info("BBB configuration not found ! Keeping DHCP")
