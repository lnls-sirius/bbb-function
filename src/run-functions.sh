#!/bin/bash

export FUNCTION_BASE=/root/bbb-function
export PYTHONPATH=${FUNCTION_BASE}
export RSYNC_SERVER="10.128.114.161"
sed -i -e 's/RSYNC_SERVER.*$/RSYNC_SERVER="10.128.114.161"/' /root/.bashrc
export RSYNC_LOCAL="/root"
export RSYNC_PORT="873"

# Env vars
pushd ${FUNCTION_BASE}/src/scripts/
    source ./../envs.sh
popd


# Wait a few seconds before starting
#sleep 30


# Updating etc folder and bbb-function if rsync server available.
# wait-for-it ${RSYNC_SERVER}:873 --timeout=2
if [ $? -eq 0 ]; then
        # Updating bbb-function files
        pushd ${FUNCTION_BASE}/src/scripts/
        echo Synchronizing bbb-function files
        ./rsync_beaglebone.sh bbb-function
        popd
#        if [ $? -eq 0 ]; then
#            echo New version of bbb-function. Making and restarting services...
#            pushd ${FUNCTION_BASE}
#                echo "New bbb-function version! Reinstalling and restarting services..."
#                make install
#            popd
#        fi
else
    echo "Rsync server not available for bbb-function upgrading"
fi


# IP configuring - if autoConfig
pushd ${FUNCTION_BASE}/src/scripts/
    source ./../envs.sh
    ./dhcpConfig.py   #Verificar se dhcp deve ser configurado
popd


# BBB-function application
pushd ${FUNCTION_BASE}/src
    echo Starting BBB Function application
    ./init.sh
popd
