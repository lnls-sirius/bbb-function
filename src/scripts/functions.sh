#!/bin/bash
# -*- coding: utf-8 -*-

function rsync_PRUserial485 {
    echo Synchronizing pru-serial485 files
    pushd ${FUNCTION_BASE}/src/scripts/
        ./rsync_beaglebone.sh pru-serial485
    popd
}

function synchronize_common {
    # Synchronize common files and folders (startup scripts, bbb-daemon, rsync script, etc)
    pushd ${FUNCTION_BASE}/src/scripts/
        echo "Synchronizing startup scripts and pru-serial485"
        ./rsync_beaglebone.sh startup-scripts
        rsync_PRUserial485
    popd
}

function startup_loop {
    echo "Starting infinite loop ..."
    set +x
    while [ true ]; do
        sleep 2
    done
}

function resetDeviceJson {
    pushd ${FUNCTION_BASE}/src/scripts/
        ./whoami.py --reset
        cat /opt/device.json
    popd
}

function overlay_PRUserial485 {
    echo Initializing PRUserial485 overlay.

    if [ ! -d /root/pru-serial485 ]; then
        echo "[ERROR] PRUserial485: The folder /root/pru-serial485 doesn\'t exist."
        exit 1
    fi

    if [ ! -f /root/pru-serial485/src/overlay.sh ]; then
        echo "[ERROR] PRUserial485: The file /root/pru-serial485/src/overlay.sh doesn\'t exist."
        exit 1
    fi

    pushd /root/pru-serial485/src
        ./overlay.sh
    popd
}

function overlay_CountingPRU {
    echo Initializing CountingPRU overlay.

    if [ ! -d /root/counting-pru ]; then
        echo "[ERROR] counting-pru: The folder /root/counting-pru doesn\'t exist."
        exit 1
    fi

    if [ ! -f /root/counting-pru/src/DTO_CountingPRU.sh ]; then
        echo "[ERROR] counting-pru:  The file /root/counting-pru/src/DTO_CountingPRU.sh doesn\'t exist."
        exit 1
    fi

    pushd /root/counting-pru/src
        ./DTO_CountingPRU.sh
    popd
}

function overlay_SPIxCONV {
    echo "Initializing SPIxCONV overlay."

    if [ ! -d /root/SPIxCONV ]; then
        echo "[ERROR] SPIxCONV: The folder /root/SPIxCONV doesn\'t exist."
        exit 1
    fi

    if [ ! -f /root/SPIxCONV/init/SPIxCONV_config-pin.sh ]; then
        echo "[ERROR] SPIxCONV: The file /root/SPIxCONV/init/SPIxCONV_config-pin.sh doesn\'t exist."
        exit 1
    fi

    pushd /root/SPIxCONV/init
        chmod +x SPIxCONV_config-pin.sh
       ./SPIxCONV_config-pin.sh
    popd
}

function counting_pru {
    echo "PRUserial485 address != 21 and ttyUSB0 is disconnected. Assuming CountingPRU."
    echo "Synchronizing counting-pru files"

    pushd ${FUNCTION_BASE}/src/scripts/
        ./rsync_beaglebone.sh counting-pru
    popd

    overlay_CountingPRU

    echo "Initializing CountingPRU ..."

    if [ ! -d /root/counting-pru ]; then
        echo "[ERROR] CountingPRU: The folder /root/counting-pru doesn\'t exist."
        exit 1
    fi

    if [ ! -f /root/counting-pru/IOC/SI-CountingPRU_Socket.py ]; then
        echo "[ERROR] CountingPRU: The file /root/counting-pru/IOC/SI-CountingPRU_Socket.py doesn\'t exist."
        exit 1
    fi

    pushd /root/counting-pru/IOC
        ./SI-CountingPRU_Socket.py
    popd
}

function startup_blinkingLED {
    if pgrep "HeartBeat" >/dev/null 2>&1
    then
        echo "HeartBeat Running ..."
    else
        echo "Startup LED blinking..."

        if [ ! -d /root/startup-scripts ]; then
            echo "[ERROR] blinkingLED: The folder /root/startup-scripts doesn\'t exist."
            return 1
        fi

        if [ ! -f /root/startup-scripts/HeartBeat.py ]; then
            echo "[ERROR] blinkingLED: The file /root/startup-scripts/HeartBeat.py doesn\'t exist."
            return 1
        fi

        pushd /root/startup-scripts
        ./HeartBeat.py &
        popd
    fi
}

function startup_HardReset {
    if pgrep "HardReset" >/dev/null 2>&1
    then
        echo "HardReset Running ..."
    else
        echo "Startup HardReset..."

        if [ ! -d /root/startup-scripts ]; then
            echo "[ERROR] HardReset: The folder /root/startup-scripts doesn\'t exist."
            return 1
        fi

        if [ ! -f /root/startup-scripts/HardReset.py ]; then
            echo "[ERROR] HardReset: The file /root/startup-scripts/HardReset.py doesn\'t exist."
            return 1
        fi

        pushd /root/startup-scripts
            ./HardReset.py &
        popd
    fi
}

function spixconv {
    echo SPIXCONV detected.
    echo Synchronizing pru-serial485 and spixconv files
    pushd ${FUNCTION_BASE}/src/scripts/
        ./rsync_beaglebone.sh spixconv
    popd
    overlay_PRUserial485
    overlay_SPIxCONV

    cd /root/SPIxCONV/software/scripts
    ./spixconv_unix_socket.py ${1} --tcp -p 5005
}

function pru_power_supply {
    echo Rs-485 and PRU switches are on. Assuming PRU Power Supply.
    echo Synchronizing ponte-py and eth-bridge files.
    pushd ${FUNCTION_BASE}/src/scripts/
        # Base files: PRU library and ethernet/serial bridge
        ./rsync_beaglebone.sh ponte-py
        ./rsync_beaglebone.sh eth-bridge-pru-serial485
    popd

    echo "Running eth-bridge-pru-serial485 on ports 5000 and 6000"
    systemctl start eth-bridge-pru-serial485.service

    echo "Running Ponte-py at port 4000"
    pushd /root/ponte-py
        python-sirius Ponte.py
    popd
}

function serial_thermo {
    echo  Serial Thermo probe detected.
    echo Synchronizing pru-serial485 and serial-thermo files
    pushd ${FUNCTION_BASE}/src/scripts/
        ./rsync_beaglebone.sh serial-thermo
    popd
    overlay_PRUserial485
    # @todo
    # - Rodar IOC e scripts python
}

function mks {
    sync_PRUserial485
    overlay_PRUserial485
    socat TCP-LISTEN:5002,reuseaddr,fork,nodelay FILE:/dev/ttyUSB0,b115200,rawer
    # ${DAEMON_BASE}/src/scripts/tcpSerial.py -p 5002 -b 115200 -t 0.15 --debug --serial-buffer-timeout 0.100
}

function uhv {
    overlay_PRUserial485
    ${FUNCTION_BASE}/src/scripts/tcpSerial.py -p 5004 -b 38400  -t 0.23 --debug --serial-buffer-timeout 0.075
}

function mbtemp {
    overlay_PRUserial485
    echo  "Starting socat with:"
    socat TCP-LISTEN:5003,reuseaddr,fork,nodelay,range=${SERVER_IP_ADDR} FILE:${SOCAT_DEVICE},b${BAUDRATE}
}

function socat_devices {
    overlay_PRUserial485
    echo  "Starting socat with:"
    socat TCP-LISTEN:${SOCAT_PORT},reuseaddr,fork,nodelay,range=${SERVER_IP_ADDR} FILE:${SOCAT_DEVICE},b${BAUDRATE},rawer
}