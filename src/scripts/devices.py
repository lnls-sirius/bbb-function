
#!/usr/bin/python-sirius
import logging
import time
import os
import subprocess
import sys
import struct
import Adafruit_BBIO.GPIO as GPIO
from PRUserial485 import (
    PRUserial485_open,
    PRUserial485_write,
    PRUserial485_read,
    PRUserial485_address,
)
from serial import Serial, STOPBITS_TWO, SEVENBITS, PARITY_EVEN
from persist import persist_info
from consts import *
from logger import get_logger
from boards_addr import *
import json
from datetime import datetime
import Adafruit_BBIO.SPI as SPI

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../"))
from bbb import Type

SPIxCONV = False

logger = get_logger("Devices")


if os.path.exists("/root/SPIxCONV/software/scripts"):
    sys.path.append("/root/SPIxCONV/software/scripts")
    import init # Do not remove, runs SPI init script
    import flash
    import selection

    SPIxCONV = True
else:
    logger.error("/root/SPIxCONV/software/scripts does not exist, SPIxCONV will always be false !")
    SPIxCONV = False


PIN_FTDI_PRU = "P8_11"  # 0: FTDI / 1: PRU
FTDI = 0
PRU = 1

PIN_RS232_RS485 = "P8_12"  # 0: RS232 / 1: RS485
RS232 = 0
RS485 = 1

PIN_SIMAR_DS = "P9_14"
PIN_SIMAR_LSB = "P9_15"
PIN_SIMAR_MSB = "P9_16"

GPIO.setup(PIN_FTDI_PRU, GPIO.IN)
GPIO.setup(PIN_RS232_RS485, GPIO.IN)

GPIO.setup(PIN_SIMAR_DS, GPIO.OUT)
GPIO.output(PIN_SIMAR_DS, GPIO.LOW)



# Checks  if flash memory  is mounted 
def pendrive():
    p = subprocess.run(['lsblk'],stdout= subprocess.PIPE)
    stdout = p.stdout
    return stdout.decode('ISO-8859-1') if p.returncode == 0 else ''

#Mount pendrive
def mount_pendrive():
    p  = subprocess.run(['mount','/dev/sda1','/mnt/USB'],stdout = subprocess.PIPE)
    stdout = p.stdout
    return stdout.decode('ISO-8859-1') if p.returncode == 0 else ''


#Checks flash memory  is connected
def check_devices():
    p = subprocess.run(['ls','/dev'],stdout = subprocess.PIPE)
    stdout = p.stdout
    return  stdout.decode('ISO-8859-1') if p.returncode == 0 else ''

# Checks what kind of file this in the flash memory
def read_pendrive():
    p = subprocess.run(['ls','/mnt/USB'],stdout= subprocess.PIPE)
    stdout = p.stdout
    return stdout.decode('ISO-8859-1') if p.returncode == 0 else ''

def reset():
    """
    Reset device.json content.
    """
    persist_info(0, 0, " ","RESET", "Searching for connected equipments.")

def simar():
    """
    Simar
    """
    logger.debug("SIMAR")
    simar = Simar_addr()

    if Simar_addr.check():
        boards = []

        spi = SPI.SPI(0, 0)
        spi.bpw = 8
        spi.lsbfirst = False
        spi.cshigh = False
        spi.mode = 3
        spi.msh = 1000000

        for board_addr in range(0,16):
            parity = False
            for char in '{0:04b}'.format(board_addr):
                if char == "1":
                    parity = not parity

            GPIO.output(PIN_SIMAR_DS, GPIO.LOW)
            spi.writebytes([(board_addr << 3) + (1 if parity else 0)])
            GPIO.output(PIN_SIMAR_DS, GPIO.HIGH)

            rec = 0
            info = ""
            address = 0
            while rec != 125:
                while(spi.xfer2([5,0])[1] == 1):
                    pass

                rec = spi.xfer2([3, address//256, address%256, 0])[3]

                if(rec == 0 or rec == 255):
                    break

                info += chr(rec)
                address += 1
            if info:
                boards.append({**json.loads(info), **{"address": board_addr}})

        sensor_type = { 0x58: "BMP280", 0x60: "BME280" }
        sensors = []

        GPIO.setup(PIN_SIMAR_LSB, GPIO.OUT)
        GPIO.setup(PIN_SIMAR_MSB, GPIO.OUT)

        for i in range(0,4):
            GPIO.output(PIN_SIMAR_LSB, GPIO.HIGH if (i >> 1) & 1 else GPIO.LOW)
            GPIO.output(PIN_SIMAR_MSB, GPIO.HIGH if (i >> 0) & 1 else GPIO.LOW)
            for addr in ["0x76", "0x77"]:
                try:
                    # Using check_output for backwards compatibility
                    sensor_reply = int(subprocess.check_output(["i2cget", "-y", "2", addr, "0xD0"]), 16)

                    if sensor_reply:
                        sensors.append("{} - Ch. {} ({})".format(sensor_type[sensor_reply], i, addr))
                except (subprocess.CalledProcessError, KeyError, ValueError, TypeError):
                    pass

        key_list = list(Device_Type.keys())
        val_list = list(Device_Type.values())

        file = open(RES_FILE, "w+")
        file.writelines("SIMAR")
        file.close()

        file = open(DEVICE_JSON, "w+")
        file.writelines(json.dumps({"device": key_list[val_list.index("SIMAR")], "sensors": sensors, "details": "SIMAR - Connected: [{}]".format(simar.addr()), "baudrate": 0, "boards":boards, "time": str(datetime.now())})+"\n")
        file.close()

        exit(0)


def counting_pru():
    """
    CountingPRU
    """
    logger.debug("Counting PRU")
    if PRUserial485_address() != 21 and not os.path.exists(PORT):
        counters = CountingPRU_addr()
        os.system("/root/counting-pru/src/DTO_CountingPRU.sh")
        name = "Counting PRU"
        persist_info(
            Type.COUNTING_PRU,
            name,
            0,
            COUNTING_PRU,
            "Connected: [{}]. Auto Configuration: {}".format(counters.addr(), counters.autoConfig_Available()),
        )


def no_tty():
    """
    NO /dev/ttyUSB0
    """
    logger.debug("No /dev/ttyUSB0")
    name = "No TTY"
    if not os.path.exists(PORT) and PRUserial485_address() == 21:
        persist_info(Type.UNDEFINED, name,115200, NOTTY)


def power_supply_pru():
    """
    PRU Power Supply
    """
    logger.debug("PRU Power Supply")
    ps_model_names = {
        0: "Empty",
        1: "FBP",
        2: "FBP_DCLINK",
        3: "FAC_ACDC",
        4: "FAC_DCDC",
        5: "FAC_2S_ACDC",
        6: "FAC_2S_DCDC",
        7: "FAC_2P4S_ACDC",
        8: "FAC_2P4S_DCDC",
        9: "FAP",
        10: "FAP_4P",
        11: "FAC_DCDC_EMA",
        12: "FAP_2P2S_Master",
        13: "FAP_2P2S_Slave",
        31: "UNDEFINED",
    }
    if GPIO.input(PIN_FTDI_PRU) == PRU and GPIO.input(PIN_RS232_RS485) == RS485 and PRUserial485_address() == 21:
        os.system("/root/pru-serial485/src/overlay.sh")
        baud = 6
        PRUserial485_open(baud, b"M")
        devices = []
        ps_model = []
        ps_names = []
        for ps_addr in range(1, 25):
            PRUserial485_write(BSMPChecksum(chr(ps_addr) + "\x10\x00\x01\x00").encode("latin-1"), 100)
            res = PRUserial485_read()
            if len(res) == 7 and res[1] == 17:
                devices.append(ps_addr)
                ps_model = ps_model_names[res[5] % 32]  # PS model: res[5] (bits 4..0)
                ps_name = getPSnames(ps_addr).replace(" ", "")
                if not ps_name in ps_names:
                    ps_names.append(ps_name)
                    name = "Power Supply"
            time.sleep(0.1)
        # Save info
        persist_info(
            Type.POWER_SUPPLY,
            name,
            6000000,
            PRU_POWER_SUPPLY,
            "PS model {}. Connected: {}. Names: {}".format(ps_model, devices, ps_names),
        )


def thermoIncluirChecksum(entrada):
    soma = 0
    for elemento in entrada:
        soma += ord(elemento)
    soma = soma % 256
    return entrada + "{0:02X}".format(soma) + "\x03"


def thermo_probe():
    """
    Thermo probes
    """
    logger.debug("Thermo probes")
    if (
        GPIO.input(PIN_FTDI_PRU) == FTDI
        and GPIO.input(PIN_RS232_RS485) == RS485
        and PRUserial485_address() == 21
        and os.path.exists(PORT)
    ):
        baud = 19200
        ser = Serial(
            port=PORT, baudrate=baud, bytesize=SEVENBITS, parity=PARITY_EVEN, stopbits=STOPBITS_TWO, timeout=TIMEOUT
        )
        msg = thermoIncluirChecksum("\x07" + "01RM1")
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.write(msg.encode("utf-8"))
        res = ser.read(50)
        name = "Thermo Probes"

        if len(res) != 0:
            persist_info(Type.SERIAL_THERMO,name, baud, SERIAL_THERMO)


def BSMPChecksum(string):
    counter = 0
    i = 0
    while i < len(string):
        counter += ord(string[i])
        i += 1
    counter = counter & 0xFF
    counter = (256 - counter) & 0xFF
    return string + chr(counter)


def getPSnames(ps_ID):
    getPSnames_command = (chr(ps_ID)) + "\x50\x00\x05\x20\x00\x00"
    psname = ""
    for ch in range(64):
        PRUserial485_write(BSMPChecksum(getPSnames_command + chr(ch) + "\x00").encode("latin-1"), 100)
        resp = PRUserial485_read()
        if len(resp) == 9:
            psname += chr(int(struct.unpack("<f", resp[4:8])[0]))
    return psname


def mbtemp():

    """
    MBTemp
    """
    logger.debug("MBTemp")
    if (
        GPIO.input(PIN_FTDI_PRU) == FTDI
        and GPIO.input(PIN_RS232_RS485) == RS485
        and PRUserial485_address() == 21
        and os.path.exists(PORT)
    ):
        baud = 115200
        ser = Serial(PORT, baud, timeout=TIMEOUT)
        devices = []
        for mbt_addr in range(1, 32):
            ser.write(BSMPChecksum(chr(mbt_addr) + "\x10\x00\x01\x00").encode("latin-1"))
            res = ser.read(10).decode("latin-1")
            if len(res) == 7 and res[1] == "\x11":
                devices.append(mbt_addr)
        ser.close()
        name = "MBTemp"
        if len(devices):
            persist_info(Type.MBTEMP, name, baud, MBTEMP, "MBTemps connected {}".format(devices))

                    

def mks9376b():
    """
    MKS 937B
    """
    logger.debug("MKS 937B")
    if (
        GPIO.input(PIN_FTDI_PRU) == FTDI
        and GPIO.input(PIN_RS232_RS485) == RS485
        and PRUserial485_address() == 21
        and os.path.exists(PORT)
    ):
        baud = 115200
        ser = Serial(port=PORT, baudrate=baud, timeout=0.05)
        devices = []
        for mks_addr in range(1, 255):
            msgm = "\@{0:03d}".format(mks_addr) + "PR1?;FF"
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            ser.write(msgm.encode("latin-1"))
            res = ser.read(20).decode("latin-1")
            if len(res) != 0:
                devices.append(mks_addr)
        ser.close()
        name = "MKS"
        if len(devices):
            persist_info(Type.MKS937B, name,baud, MKS937B, "MKS937Bs connected {}".format(devices))


def Agilent4UHV_CRC(string):
    counter = 0
    i = 0
    for b in string:
        if i > 0:
            counter ^= ord(b)
        i += 1

    string += chr(int(bin(counter)[2:6], 2) + 48)
    string += chr(int(bin(counter)[6:], 2) + 48)
    return string


def agilent4uhv():
    """
    AGILENT 4UHV
    """
    logger.debug("AGILENT 4UHV")
    if (
        GPIO.input(PIN_FTDI_PRU) == FTDI
        and GPIO.input(PIN_RS232_RS485) == RS485
        and PRUserial485_address() == 21
        and os.path.exists(PORT)
    ):
        baud = 38400
        ser = Serial(port=PORT, baudrate=baud, timeout=0.6)
        devices = []
        for addr in range(0, 32):
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            pl = ""
            pl += "\x02"
            pl += chr(addr + 128)
            pl += "\x38"
            pl += "\x31"
            pl += "\x30"
            pl += "\x30"
            pl += "\x03"
            ser.write(Agilent4UHV_CRC(pl).encode("latin-1"))
            res = ser.read(15).decode("latin-1")
            if len(res) != 0:
                devices.append(addr)
        ser.close()
        name = "Agilent 4UHV"
        if len(devices):
            persist_info(Type.AGILENT4UHV, name ,baud, AGILENT4UHV, "AGILENT4UHV connected {}".format(devices))


def spixconv():
    """
    SPIxCONV
    """
    logger.debug("SPIxCONV")

    if not SPIxCONV:
        return

    subprocess.call("config-pin P9_17 spi_cs", shell=True)  # CS
    subprocess.call("config-pin P9_21 spi", shell=True)  # DO
    subprocess.call("config-pin P9_18 spi", shell=True)  # DI
    subprocess.call("config-pin P9_22 spi_sclk", shell=True)  # CLK

    subprocess.call("config-pin P8_37 gpio", shell=True)  # BUSY
    subprocess.call("config-pin P9_24 gpio", shell=True)  # LDAC / CNVST
    subprocess.call("config-pin P9_26 gpio", shell=True)  # RS

    # Starts checking  for a flash memory
    find_devices =  check_devices()

    if(find_devices.find('sda') == -1 and find_devices.find('sdb') == -1):
        print("Pendrive  not detected")
        exit()

    else:
        print("Pendrive detected")
        devices = pendrive()
        result = devices.find('/mnt/USB')

        if(result == -1):
            mount_pendrive()

        pendrive_files  = read_pendrive()

        if(pendrive_files.find('AutoConfig.xlsx') == -1 and pendrive_files.find('AutoConfig.txt') == -1):
            print("No files detected")

        if(pendrive_files.find('AutoConfig.xlsx') ==-1  and pendrive_files.find('AutoConfig.txt') !=  -1):
            file = open('/mnt/USB/AutoConfig.txt')
            lines = file.readlines()
            bbb = lines[0].split("\n")
            print(bbb[0])
            name = bbb[0]

            for addr in range(0, 255):
                if flash.ID_read(addr) == 4:
                    spi_addr = 8 if flash.address_read(addr) == 0 else flash.address_read(addr)
                    logger.info(
                        "Addr code: {}\nSelection Board ID: {}\nFlash address: {}\n Name {}\nSPI address: {}".format(
                            addr,
                            selection.board_ID(addr),
                            flash.address_read(addr),
                            name,
                            spi_addr,
                            
                        )
                    )
                    persist_info(Type.SPIXCONV,  name, spi_addr, SPIXCONV, "SPIXCONV connected {}".format(spi_addr))

    

        
        
