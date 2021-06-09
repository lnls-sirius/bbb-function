#!/bin/bash
# -*- coding: utf-8 -*-
#set -x
source ${FUNCTION_BASE}/src/scripts/functions.sh
source ${FUNCTION_BASE}/src/envs.sh

pushd ${FUNCTION_BASE}/src/scripts

    function cleanup {
        stop_applications

        if [ -f ${RES_FILE} ]; then
                rm -rf ${RES_FILE}
        fi

        if [ -f ${BAUDRATE_FILE} ]; then
            rm -rf ${BAUDRATE_FILE}
        fi

        pushd ${FUNCTION_BASE}/src/scripts/
            ./bbbPrimarySecondary.py clean
        popd
    }

    trap cleanup EXIT
    cleanup

    # Synchronize common files and folders (startup scripts, bbb-function, rsync script, etc)
    synchronize_common

    # Run HardReset script, which is available at all boards
    startup_HardReset

    # PRIMARY OR SECONDARY BEAGLEBONE?
    bbb_primary_secondary


    if [[ ${BBB_STATUS} = "PRIMARY" ]]; then
        # The whoami.py script will save in a temporary file which device is connected
        # Run identification script, repeats until a device is found
        echo "Running identification script, repeats until a device is found."
        ./detectEquipment.py
    elif [[ ${BBB_STATUS} = "SECONDARY" ]]; then
        # Wait for equipment info - device.json - RES-FILE - BAUDRATE-FILE
        echo "Wait for equipment info..."
        ./detectEquipment.py --secondary
    fi

    # Proceed to autoConfig
    ./autoConfig.py

    # Prepare board to its application
    CONN_DEVICE=$(awk NR==1 ${RES_FILE})
    BAUDRATE=$(awk NR==1 ${BAUDRATE_FILE})

    # Running application
    while [ 1 ]
    do
        if [[ ${BBB_STATUS} = "PRIMARY" ]]; then
            
            if [[ ${CONN_DEVICE} = "${SPIXCONV}" ]]; then
                # Using variable BAUDRATE to store the board address
                spixconv ${BAUDRATE}

            elif [[ ${CONN_DEVICE} = "${PRU_POWER_SUPPLY}" ]]; then
                pru_power_supply

            elif [[ ${CONN_DEVICE} = "${COUNTING_PRU}" ]]; then
                counting_pru

            elif [[ ${CONN_DEVICE} = "${SERIAL_THERMO}" ]]; then
                serial_thermo

            elif [[ ${CONN_DEVICE} = "${MKS937B}" ]]; then
                mks

            elif [[ ${CONN_DEVICE} = "${AGILENT4UHV}" ]]; then
                uhv

            elif [[ ${CONN_DEVICE} = "${MBTEMP}" ]]; then
                mbtemp

            elif [ ! -z ${CONN_DEVICE} ]; then
                socat_devices

            else
                if [[ ${CONN_DEVICE} = "${NOTTY}" ]]; then
                    echo No matching device has been found. ttyUSB0 is disconnected.
                else
                    echo  Unknown device. Nothing has been done.
                fi
                exit 1
            fi

            pushd ${FUNCTION_BASE}/src/scripts/
                ./redundancyLoop.py --mode primary
                export EXIT_VALUE=$?
                if [[ ${EXIT_VALUE} = "2" ]]; then
                    export BBB_STATUS="SECONDARY"
                    ./bbbPrimarySecondary.py force-secondary
                fi
            popd

        elif [[ ${BBB_STATUS} = "SECONDARY" ]]; then
            pushd ${FUNCTION_BASE}/src/scripts/
                ./redundancyLoop.py --mode secondary
                export EXIT_VALUE=$?
                if [[ ${EXIT_VALUE} = "1" ]]; then
                    export BBB_STATUS="PRIMARY"
                    ./bbbPrimarySecondary.py force-primary
                fi
            popd
        fi
        echo "Cleaning up services"
        stop_applications
    done
popd
