#!/bin/bash
# -----------------------------------------------------------------------------
# Sirius Control System - Beaglebone Black
# Remote Sync Files and Libraries
# -----------------------------------------------------------------------------
# October, 2018
# Patricia H Nallin
# -----------------------------------------------------------------------------
PROJECT=$1

# Proceed if a project was requested
if [ ! -z ${PROJECT} ]; then
        # -------------------------------------------------------------------------
        # Check whether Rsync Server is available - First item in rsync.conf must be "online"
        SYNC_AVAILABLE=`rsync -n --contimeout=2 $RSYNC_SERVER::`;
        if [ "${SYNC_AVAILABLE%% *}" = "online" ]; then
            # ---------------------------------------------------------------------
            # etc-folder files
            if [ "${PROJECT}" = "etc-folder" ]; then
                UPDATES=`rsync -ainO $RSYNC_SERVER::$PROJECT /etc`;
            # ---------------------------------------------------------------------
            # Project files
            else
                UPDATES=`rsync -ainO $RSYNC_SERVER::$PROJECT $RSYNC_LOCAL/$PROJECT`;
            fi

            # No updates available
            if [ -z "$UPDATES" ]; then
                echo "No updates found.";
                exit 1
            # ---------------------------------------------------------------------
            #  Synchronizing files. There are updates for the project.
            else
                # -----------------------------------------------------------------
                # etc-folder files
                if [ "${PROJECT}" = "etc-folder" ]; then
                    rsync -a $RSYNC_SERVER::$PROJECT /etc > /tmp/rsync.log;
                # -----------------------------------------------------------------
                # Project files - Also build libraries
                else
                    rsync -a --exclude '*.info' --delete-after $RSYNC_SERVER::$PROJECT $RSYNC_LOCAL/$PROJECT > /tmp/rsync.log;
                fi
                if [ $? -eq 0 ]; then
                    # If project is listed below, build libraries as well
                    if [ "$PROJECT" = "counting-pru" ]; then
                        pushd $RSYNC_LOCAL/$PROJECT/src
                            ./library_build.sh
                        popd
                    fi
                    if [ "$PROJECT" = "pru-serial485" ]; then
                        pushd $RSYNC_LOCAL/$PROJECT/src
                            make install
                        popd
                    fi
                    if [ "$PROJECT" = "eth-bridge-pru-serial485" ]; then
                        pushd $RSYNC_LOCAL/$PROJECT/server
                            make install
                        popd
                    fi
                    exit 0
                fi
            fi
        fi
else
    echo "No project selected for updating.";
    exit 1
fi
