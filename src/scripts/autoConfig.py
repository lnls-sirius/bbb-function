#!/usr/bin/python-sirius
# # -*- coding: utf-8 -*-
import logging
import serial
import subprocess
import json
import re
import socket
import time
from xlrd import open_workbook
from consts import *
from bbb import BBB
from counters_addr import Addressing
from PRUserial485 import PRUserial485_address


logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(asctime)-15s %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')
logger = logging.getLogger('AutoConfig')

# Constants
COUNTINGPRU_ID = 0
SERIALXXCON_ID = 21
CONFIGURED_SUBNETS = ['102','103','104','105']


class AutoConfig():
    def __init__(self):
        self.boardID = PRUserial485_address()
        self.status = False
        self.check()

    def check(self):
        '''
        Check whether AUTOCONFIG is enabled only for some subnets
        '''
        if(self.get_subnet() in CONFIGURED_SUBNETS):
            # COUNTINGPRU
            if(self.boardID == COUNTINGPRU_ID):
                self.counter = Addressing()
                system("/root/counting-pru/src/DTO_CountingPRU.sh")
                for i in range(5):
                    self.status = self.counter.autoConfig_Available()
                    if self.status:
                        break
                    sleep(2)

            # SERIALxxCON - AUTOCONFIG: RTS and CTS pins tied together (jumper)   
            elif(self.boardID == SERIALXXCON_ID):
                for i in range(5):
                    try:
                        self.status = serial.Serial("/dev/ttyUSB0").cts
                    except:
                        self.status = False
                        sleep(2)

        # Subnet not configured, then:
        else:
            self.status = False

    def get_subnet(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't have to be reachable
            s.connect(('10.128.101.100', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP.split('.')[2]


        
class GetData():
    def __init__(self, datafile=AUTOCONFIG_FILE, subnet = ""):
        try:
            _sheet = open_workbook(datafile).sheet_by_name(subnet)
            keys = [_sheet.cell(0, col_index).value for col_index in range(_sheet.ncols)]
            self.data = {}

            for row_index in range(1,_sheet.nrows):
                dev_type = _sheet.cell(row_index, keys.index(DEVICE_TYPE_COLUMN)).value
                if dev_type == '':
                    continue
                info = {keys[col_index]: _sheet.cell(row_index, col_index).value for col_index in range(_sheet.ncols)}
                info[DEVICE_ID_COLUMN] = [int(s) for s in re.findall(r'\d+', info[DEVICE_ID_COLUMN])]
                if dev_type in self.data:
                    self.data[dev_type].append(info)
                else:
                    self.data[dev_type] = [info]
        except:
            self.data = {}

if __name__ == '__main__':

    AUTOCONFIG = AutoConfig().status

    if(AUTOCONFIG):
        mybeagle_config = ''

        # Get device.json from whoami.py and get identified equipment
        mybbb = BBB()
        mybbb.type = Device_Type[mybbb.node.type.code]
        mybbb.ids = [int(s) for s in re.findall(r'\d+', mybbb.node.details.split('\t')[0])]
        mybbb.currentIP = str(mybbb.get_network_specs()[1])
        mybbb.currentSubnet = mybbb.currentIP.split('.')[2]

        # Get devices from this subnet from the ConfigurationTable
        beagles = GetData(datafile=AUTOCONFIG_FILE, subnet=mybbb.currentSubnet)
 
        # Check if current BBB (type and devices found is on ConfigurationTable)
        if beagles.data:
            for bbb in beagles.data[mybbb.type]:
                # If PowerSupply, check their names instead of IDs
                if mybbb.type == "PowerSupply":
                    mybbb.PSnames = []
                    nodes = json.loads(mybbb.node.details.split('\t')[0].split('Names:')[-1].replace("'",'"'))
                    for node in nodes:
                        mybbb.PSnames.extend(node.split('/'))
                   
                    if(any(psname in bbb[DEVICE_NAME_COLUMN] for psname in mybbb.PSnames)):
                        mybeagle_config = bbb
                # If not PowerSupply, check IDs
                else:
                    if(any(id in bbb[DEVICE_ID_COLUMN] for id in mybbb.ids)):
                        mybeagle_config = bbb
 
        # If BBB config is found, proceed with configuration from datafile
        if mybeagle_config:
            logger.info("Found a compatible device in spreadsheet: {}. Proceed with BBB configuration!".format(mybeagle_config))

            # Save found config into a json file
            with open(CONFIG_FILE, 'w') as fp:
                json.dump(mybeagle_config, fp)

            # Update hostname
            logger.info("BBB hostname: {}".format(mybeagle_config[BBB_HOSTNAME_COLUMN]))
            mybbb.update_hostname(mybeagle_config[BBB_HOSTNAME_COLUMN])

            IP_AVAILABLE = subprocess.call(['ping', '-c', '1', '-W', '1', mybeagle_config[BBB_IP_COLUMN]], stdout=subprocess.DEVNULL)
            subnet = mybeagle_config[BBB_IP_COLUMN].split('.')[2]
            # Update IP, if available
            if IP_AVAILABLE and subnet == mybbb.currentSubnet:
                logger.info("BBB IP: {}".format(mybeagle_config[BBB_IP_COLUMN]))
                mybbb.update_ip_address('manual', new_ip_address=mybeagle_config[BBB_IP_COLUMN], new_mask="255.255.255.0", new_gateway="10.128.{}.1".format(subnet))
            else:
                if not IP_AVAILABLE:
                    if mybeagle_config[BBB_IP_COLUMN] == mybbb.currentIP:
                        logger.info("BBB IP is already configured to {}.".format(mybeagle_config[BBB_IP_COLUMN]))
                    else:
                        logger.info("Desired IP {} is currently in use by another device.".format(mybeagle_config[BBB_IP_COLUMN]))
                else:
                    logger.info("Cannot change to IP {}, subnet is not compatible to current one ({}).".format(mybeagle_config[BBB_IP_COLUMN], mybbb.currentSubnet))


        # If BBB not found, keep DHCP and raise a flag!
        else:
            logger.info("A compatible device was NOT found in spreadsheet. Verify if there is a config file at {}.".format(CONFIG_FILE))
            
            try:
                # Get previous config
                with open(CONFIG_FILE, 'w') as fp:
                    file_config = json.loads(mybeagle_config, fp)

                # Configure hostname
                logger.info("BBB hostname: {}".format(file_config[BBB_HOSTNAME_COLUMN]))
                mybbb.update_hostname(file_config[BBB_HOSTNAME_COLUMN])

                # If same subnet and desided IP is available, proceed with IP configuration
                IP_AVAILABLE = subprocess.call(['ping', '-c', '1', '-W', '1', file_config[BBB_IP_COLUMN]], stdout=subprocess.DEVNULL)
                subnet = file_config[BBB_IP_COLUMN].split('.')[2]
                if IP_AVAILABLE and mybbb.currentSubnet == subnet:
                    logger.info("BBB IP {}".format(file_config[BBB_IP_COLUMN]))
                    mybbb.update_ip_address('manual', new_ip_address=file_config[BBB_IP_COLUMN], new_mask="255.255.255.0", new_gateway="10.128.{}.1".format(subnet))
                else:
                    if not IP_AVAILABLE:
                        logger.info("Desired IP {} is currently in use by another device.".format(file_config[BBB_IP_COLUMN]))
                    else:
                        logger.info("Cannot change to IP {}, subnet is not compatible to current one ({}).".format(file_config[BBB_IP_COLUMN], mybbb.currentSubnet))
                
            except:
                logger.info("BBB configuration not found ! Keeping DHCP")
                
