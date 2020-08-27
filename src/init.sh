#!/bin/bash
# -*- coding: utf-8 -*-
#set -x
source ${FUNCTION_BASE}/src/scripts/functions.sh
source ${FUNCTION_BASE}/src/envs.sh

pushd ${FUNCTION_BASE}/src/scripts

    function cleanup {
        # Reset the detected device
#        resetDeviceJson
        systemctl stop eth-bridge-pru-serial485

        if [ -f ${RES_FILE} ]; then
                rm -rf ${RES_FILE}
        fi

        if [ -f ${BAUDRATE_FILE} ]; then
            rm -rf ${BAUDRATE_FILE}
        fi
    }

    trap cleanup EXIT
    cleanup

    # Synchronize common files and folders (startup scripts, bbb-function, rsync script, etc)
    synchronize_common

    # Run HardReset script, which is available at all boards
    startup_HardReset

    # The whoami.py script will save in a temporary file which device is connected
    # Run identification script, repeats until a device is found
    echo "Running identification script, repeats until a device is found."
    ./detectEquipment.py
    ./autoConfig.py

    # Prepare board to its application
    CONN_DEVICE=$(awk NR==1 ${RES_FILE})
    BAUDRATE=$(awk NR==1 ${BAUDRATE_FILE})

    if [[ ${CONN_DEVICE} = "${SPIXCONV}" ]]; then
        # Using variable BAUDRATE to store the board address
        startup_blinkingLED
        spixconv ${BAUDRATE}

    elif [[ ${CONN_DEVICE} = "${PRU_POWER_SUPPLY}" ]]; then
        startup_blinkingLED
        pru_power_supply

    elif [[ ${CONN_DEVICE} = "${COUNTING_PRU}" ]]; then
        startup_blinkingLED
        counting_pru

    elif [[ ${CONN_DEVICE} = "${SERIAL_THERMO}" ]]; then
        startup_blinkingLED
        serial_thermo

    elif [[ ${CONN_DEVICE} = "${MKS937B}" ]]; then
        startup_blinkingLED
        mks

    elif [[ ${CONN_DEVICE} = "${AGILENT4UHV}" ]]; then
        startup_blinkingLED
        uhv

    elif [[ ${CONN_DEVICE} = "${MBTEMP}" ]]; then
        startup_blinkingLED
        mbtemp

    elif [ ! -z ${CONN_DEVICE} ]; then
        startup_blinkingLED
        socat_devices

    else
        if [[ ${CONN_DEVICE} = "${NOTTY}" ]]; then
            echo No matching device has been found. ttyUSB0 is disconnected.
        else
            echo  Unknown device. Nothing has been done.
        fi
        exit 1
    fi
popd

