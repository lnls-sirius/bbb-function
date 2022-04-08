#!/usr/bin/python-sirius
# # -*- coding: utf-8 -*-
from unicodedata import name
import serial
import subprocess
import json
import re
import socket
from xlrd import open_workbook
from consts import *
from bbb import BBB
from logger import get_logger
from boards_addr import *
from PRUserial485 import PRUserial485_address
from os import system
from time import sleep

logger = get_logger("AutoConfig")

# Constants
COUNTINGPRU_SIMAR_ID = 0
SERIALXXCON_ID = 21
CONFIGURED_SUBNETS = ["102", "103", "104", "105", "106", \
"107", "108", "109", "110", "111", "112",\
"113", "114", "115", "116", "117", "118", "119", "120", "121", "123", \
"131", "132", "133", "134", "135", "136", "137"]


class AutoConfig:
    def __init__(self):
        self.boardID = PRUserial485_address()
        self.status = False
        self.check()

    def read_USB0(self):
            p = subprocess.run(['ls','/dev'],stdout= subprocess.PIPE)
            stdout = p.stdout
            return stdout.decode('ISO-8859-1') if p.returncode == 0 else ''
    def check(self):
        """
        Check whether AUTOCONFIG is enabled only for some subnets
        """

        if self.get_subnet() in CONFIGURED_SUBNETS:
            # COUNTINGPRU
            if self.boardID == COUNTINGPRU_SIMAR_ID:
                self.simar = Simar_addr()
                self.counter = CountingPRU_addr()

                if Simar_addr.check():
                    for i in range(5):
                        self.status = self.simar.autoConfig_Available()
                        if self.status:
                            break
                        sleep(2)
                else:
                    system("/root/counting-pru/src/DTO_CountingPRU.sh")
                    for i in range(5):
                        self.status = self.counter.autoConfig_Available()
                        if self.status:
                            break
                        sleep(2)

            # SERIALxxCON - AUTOCONFIG: RTS and CTS pins tied together (jumper)
            elif self.boardID == SERIALXXCON_ID:
                read_usb = self.read_USB0()

                if(read_usb.find('ttyUSB') != -1):
                    for i in range(5):
                        try:
                            self.status = serial.Serial("/dev/ttyUSB0").cts
                        except:
                            self.status = False
                            sleep(2)
                else:
                    # Considera SPIxCONV = Pulsados
                    self.status = True

        # Subnet not configured, then:
        else:
            self.status = False

    def get_subnet(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't have to be reachable
            s.connect(("10.128.101.100", 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = "127.0.0.1"
        finally:
            s.close()
        return IP.split(".")[2]


class GetData:
    def __init__(self,datafile=AUTOCONFIG_FILE, subnet=""):
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

    AUTOCONFIG = AutoConfig().status

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
                        if "PS model FBP" in mybbb.node.details:
                            mybbb.PSnames.extend(node.split("/"))
                        else:
                            mybbb.PSnames.extend(node.split(","))

                    if any(psname in bbb[DEVICE_NAME_COLUMN] for psname in mybbb.PSnames):
                        mybeagle_config = bbb

                if( mybbb.type == "SPIxCONV" and mybbb.name == bbb[DEVICE_NAME_COLUMN]):
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


            # If same subnet and desided IP is available, proceed with IP configuration
            # Check primary IP
            IP_AVAILABLE_1 = subprocess.call(
                ["ping", "-c", "1", "-W", "1", mybeagle_config[BBB_IP_1_COLUMN]], stdout=subprocess.DEVNULL
            )
            # Check secondary IP, if available on spreadsheet
            if mybeagle_config[BBB_IP_2_COLUMN]:
                IP_AVAILABLE_2 = subprocess.call(
                    ["ping", "-c", "1", "-W", "1", mybeagle_config[BBB_IP_2_COLUMN]], stdout=subprocess.DEVNULL
                )
            else:
                IP_AVAILABLE_2 = False
            # Check requested subnet
            subnet = mybeagle_config[BBB_IP_1_COLUMN].split(".")[2]


            # Update IP, if available
            if (IP_AVAILABLE_1 or IP_AVAILABLE_2) and subnet == mybbb.currentSubnet:
                if IP_AVAILABLE_1:
                    new_ip = mybeagle_config[BBB_IP_1_COLUMN]
                else:
                    new_ip = mybeagle_config[BBB_IP_2_COLUMN]

                logger.info("BBB IP: {}".format(new_ip))
                mybbb.update_ip_address(
                    "manual",
                    new_ip_address=new_ip,
                    new_mask="255.255.255.0",
                    new_gateway="10.0.{}.1".format(subnet),
                )
            else:
                if not (IP_AVAILABLE_1 or IP_AVAILABLE_2):
                    if mybeagle_config[BBB_IP_1_COLUMN] == mybbb.currentIP or mybeagle_config[BBB_IP_2_COLUMN] == mybbb.currentIP:
                        logger.info("BBB IP is already configured to {}.".format(mybbb.currentIP))
                    else:
                        logger.error(
                            "Desired IPs {} / {} are currently in use by other devices.".format(
                                mybeagle_config[BBB_IP_1_COLUMN],
                                mybeagle_config[BBB_IP_2_COLUMN]
                            )
                        )
                else:
                    logger.error(
                        "Cannot change to IP {} / {}, subnet is not compatible to current one ({}).".format(
                            mybeagle_config[BBB_IP_1_COLUMN],
                            mybeagle_config[BBB_IP_2_COLUMN],
                            mybbb.currentSubnet
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
                with open(CONFIG_FILE, "r") as fp:
                    mybeagle_config = json.load(fp)
                    
                # Configure hostname
                logger.info("BBB hostname: {}".format(mybeagle_config[BBB_HOSTNAME_COLUMN]))
                mybbb.update_hostname(mybeagle_config[BBB_HOSTNAME_COLUMN])

                # If same subnet and desided IP is available, proceed with IP configuration
                # Check primary IP
                IP_AVAILABLE_1 = subprocess.call(
                    ["ping", "-c", "1", "-W", "1", mybeagle_config[BBB_IP_1_COLUMN]], stdout=subprocess.DEVNULL
                )
                # Check secondary IP, if available on spreadsheet
                if mybeagle_config[BBB_IP_2_COLUMN]:
                    IP_AVAILABLE_2 = subprocess.call(
                        ["ping", "-c", "1", "-W", "1", mybeagle_config[BBB_IP_2_COLUMN]], stdout=subprocess.DEVNULL
                    )
                else:
                    IP_AVAILABLE_2 = False
                # Check requested subnet
                subnet = mybeagle_config[BBB_IP_1_COLUMN].split(".")[2]


                # Update IP, if available
                if (IP_AVAILABLE_1 or IP_AVAILABLE_2) and subnet == mybbb.currentSubnet:
                    if IP_AVAILABLE_1:
                        new_ip = mybeagle_config[BBB_IP_1_COLUMN]
                    else:
                        new_ip = mybeagle_config[BBB_IP_2_COLUMN]

                    logger.info("BBB IP: {}".format(new_ip))
                    mybbb.update_ip_address(
                        "manual",
                        new_ip_address=new_ip,
                        new_mask="255.255.255.0",
                        new_gateway="10.128.{}.1".format(subnet),
                    )
                else:
                    if not (IP_AVAILABLE_1 or IP_AVAILABLE_2):
                        if mybeagle_config[BBB_IP_1_COLUMN] == mybbb.currentIP or mybeagle_config[BBB_IP_2_COLUMN] == mybbb.currentIP:
                            logger.info("BBB IP is already configured to {}.".format(mybbb.currentIP))
                        else:
                            logger.error(
                                "Desired IPs {} / {} are currently in use by other devices.".format(
                                    mybeagle_config[BBB_IP_1_COLUMN],
                                    mybeagle_config[BBB_IP_2_COLUMN]
                                )
                            )
                    else:
                        logger.error(
                            "Cannot change to IP {} / {}, subnet is not compatible to current one ({}).".format(
                                mybeagle_config[BBB_IP_1_COLUMN],
                                mybeagle_config[BBB_IP_2_COLUMN],
                                mybbb.currentSubnet
                            )
                        )
            except:
                logger.info("BBB configuration not found ! Keeping DHCP")

