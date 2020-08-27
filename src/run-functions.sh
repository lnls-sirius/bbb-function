#!/bin/bash

export FUNCTION_BASE=/root/bbb-function
export PYTHONPATH=${FUNCTION_BASE}
export RSYNC_SERVER="10.128.255.5"
sed -i -e 's/RSYNC_SERVER.*$/RSYNC_SERVER="10.128.255.5"/' /root/.bashrc
export RSYNC_LOCAL="/root"
export RSYNC_PORT="873"

# Generate the initial device.json

pushd ${FUNCTION_BASE}/src/scripts/
    source ./../envs.sh
    sleep 10
    ./get_counters_ip.py
    ./key_dhcp.py   #Verificar se dhcp deve ser configurado
popd


# Updating etc folder and bbb-function if rsync server available.
wait-for-it ${RSYNC_SERVER}:873 --timeout=5
if [ $? -eq 0 ]; then
        # Updating bbb-function files
        echo Synchronizing bbb-function files
        ./function/script/rsync_beaglebone.sh bbb-function-dev
        if [ $? -eq 0 ]; then
            echo New version of bbb-function. Making and restarting services...
            pushd ${FUNCTION_BASE}
                echo "New bbb-function version! Reinstalling and restarting services..."
#                make install
            popd
        fi
else
    echo "Rsync server not available for bbb-function upgrading"
fi


# BBB-function application
pushd ${FUNCTION_BASE}/src
    echo Starting BBB Function application
    ./init.sh
popd
