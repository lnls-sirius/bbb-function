#!/usr/bin/python-sirius
# -*- coding: utf-8 -*-

from unicodedata import name
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.UART as UART
from bbb import BBB
import serial
import time
from consts import SEPARATOR, DEVICE_JSON, SERVER_IP
import redis
import argparse
from logger import get_logger
import threading
import subprocess
import PRUserial485


global errorStatus
STREAMING_LOOP = 2 # seconds
TIMEOUT = 0.5
ERROR_DELAY = 10 # seconds
LED = "P8_28"
PIN_FTDI_PRU="P8_11"
streamDelayFactor = {"primary": 1, "secondary": 2}

def blinkLED(mode):
    while True:
        for _ in range (2):
            if mode == "primary":
                for _ in range (2):
                    GPIO.output(LED, 1)
                    time.sleep(0.1)
                    GPIO.output(LED, 0)
                    time.sleep(0.1)
            elif mode == "secondary":
                for _ in range (1):
                    GPIO.output(LED, 1)
                    time.sleep(0.5)
                    GPIO.output(LED, 0)
                    time.sleep(0.5)
            time.sleep(1)

def streamInfo(mode, epoch):
    if mode == "primary":
       message = bbb_config.encode() + SEPARATOR + \
                    str(mybbb.get_network_specs()[1]).encode() + SEPARATOR + \
                        mode.encode() + SEPARATOR + \
                            str(epoch).encode()

    elif mode == "secondary":
        message = SEPARATOR + \
                    str(mybbb.get_network_specs()[1]).encode() + SEPARATOR + \
                        mode.encode() + SEPARATOR + \
                            str(epoch).encode()

    else:
        message = b""
        logger.error("Mode not found")

    while True:
        s.write(message)
        time.sleep(STREAMING_LOOP*streamDelayFactor[mode])

def getInfo(mode, this_epoch):
    global errorStatus
    countdown = int(ERROR_DELAY / TIMEOUT)
    while True:
        ipaddr = ""
        info = s.read(1000)
        if info:
            try: 
                countdown = int(ERROR_DELAY / TIMEOUT)

                ipaddr = info.split(SEPARATOR)[1]
                matching_bbb = info.split(SEPARATOR)[2]
                matching_epoch = float(info.split(SEPARATOR)[3])

                r.hset("device", "matching_ip_address", ipaddr)
                r.hset("device", "matching_bbb", matching_bbb)
                r.hset("device", "matching_epoch", matching_epoch)

                if matching_bbb == mode.encode():
                    if not subprocess.call(["ping", "-w", "1","-c", "1", SERVER_IP], stdout=subprocess.DEVNULL):
                        if matching_epoch > this_epoch:
                            logger.info("Both BBBs with same config and this one is older. Mode swapping.")
                            errorStatus[mode] = True
                    else:
                        logger.info("Both BBBs with same config. This one is not connected to SERVER. Mode Swapping")
                        errorStatus[mode] = True
            except:
                time.sleep(1)
        else:
            countdown -= 1 
            
            if countdown == 0 and mode == "secondary":
                errorStatus[mode] = True
            elif mode == "primary":
                countdown = int(ERROR_DELAY / TIMEOUT)

def pingPrimary(mode):
    global errorPing
    countdown = int(ERROR_DELAY / TIMEOUT / 2)
    while True:
        primary_bbb = r.hget("device", "matching_ip_address")
        if primary_bbb:

            not_ping_primary = subprocess.call(["ping", "-w", "1","-c", "1", primary_bbb], stdout=subprocess.DEVNULL)
            not_ping_server = subprocess.call(["ping", "-w", "1","-c", "1", SERVER_IP], stdout=subprocess.DEVNULL)

            # Ping not responsive
            if not_ping_primary and not not_ping_server:
                countdown -= 1
            # Ping pong!
            else:
                countdown = int(ERROR_DELAY / TIMEOUT / 2)

            # Countdown reached
            if countdown == 0 and mode == "secondary":
                errorPing[mode] = True

        time.sleep(0.5)


def snifferSerial(baudrate):
    GPIO.setup(PIN_FTDI_PRU,GPIO.IN)
    conexao=GPIO.input(PIN_FTDI_PRU)

    contador=0
    armazena=b''  
#    print("*******************************************************************************")  
        
    if (conexao):
        PRUserial485.PRUserial485_open(6,b'S')
#        print("*******************************************************************************")
        while True:
            resposta=PRUserial485.PRUserial485_read(1000)
#            print(resposta)
            armazena=armazena+resposta
            if (len(armazena)>10000):
#                print("*******************************************************************************")
#                print(len(armazena))
#                print(armazena)
                leitura='dados['+str(contador)+']'
                r.set(leitura,armazena)
                contador += 1
                if (contador==10):
                    contador=0
                armazena=b''
    else:
        s = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)
        while True:
            resposta=s.readline()
    #        print(resposta)




if __name__ == "__main__":

    global errorStatus, errorPing
    errorStatus = {"primary": False, "secondary": False}
    errorPing = {"primary": False, "secondary": False}
    errorExit = {"primary": 2, "secondary": 1}

    # Logger
    logger = get_logger("redundancyLoop")

    # Args
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m", "--mode", 
        type=str, 
        choices=["primary", "secondary"], 
        default="primary",
        help="BBB mode: primary or secondary one"
        )
    args = parser.parse_args()

    
    # Config UART
    UART.setup("UART4")
    s = serial.Serial(port="/dev/ttyO4", baudrate=115200, timeout=TIMEOUT)

    # Connect to local redis db
    r = redis.StrictRedis(host="127.0.0.1", port=6379)
    r.hset("device", "this_bbb", args.mode)
    r.hset("device", "redundancy_epoch", time.time())
    r.hset("device", "matching_ip_address", "")
    r.hset("device", "matching_bbb", "")
    

    # Config LED
    GPIO.setup(LED, GPIO.OUT)

    # Get BBB
    mybbb = BBB()

    # Open Config
    if args.mode == "primary":
        with open(DEVICE_JSON, 'r') as reader:
            bbb_config = reader.read()

    # Continuous loop - Threads
    blinkThread = threading.Thread(target=blinkLED, args=[args.mode], daemon=True)
    streamThread = threading.Thread(target=streamInfo, args=[args.mode, time.time()], daemon=True)
    infoThread  = threading.Thread(target=getInfo, args=[args.mode, time.time()], daemon=True)
    if args.mode == "secondary":
        pingThread  = threading.Thread(target=pingPrimary, args=[args.mode], daemon=True)
        snifferThread = threading.Thread(target=snifferSerial, args=[6], daemon=True)

    blinkThread.start()
    streamThread.start()
    infoThread.start()
    if args.mode == "secondary":
        pingThread.start()
        snifferThread.start()

    while True:
        time.sleep(1)

        if errorStatus[args.mode] or errorPing[args.mode]:
            logger.info("Error while monitoring {} BBB. Exiting, swapping mode and restarting applications".format(args.mode))
            exit(errorExit[args.mode])
