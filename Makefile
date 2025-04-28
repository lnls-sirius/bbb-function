PREFIX ?= /usr/local

FUNCTION_SERVICE_NAME = bbb-function
FUNCTION_SRC_SERVICE_FILE = ${FUNCTION_SERVICE_NAME}.service
FUNCTION_DEPENDENCIES = systemd-networkd systemd-networkd-wait-online
SERVICE_FILE_DEST = /etc/systemd/system

.PHONY: all install uninstall dependencies clean

all:

install:
	# Services
	cp --preserve=mode services/${FUNCTION_SRC_SERVICE_FILE} ${SERVICE_FILE_DEST}

	pip3.6 install --no-cache-dir -r requirements.txt
	pip3.6 install Adafruit_BBIO

	systemctl daemon-reload
	
	# enable and start dependencies
	systemctl enable ${FUNCTION_DEPENDENCIES}
	systemctl start ${FUNCTION_DEPENDENCIES}

	systemctl enable ${FUNCTION_SERVICE_NAME}
	systemctl restart ${FUNCTION_SERVICE_NAME}

uninstall:
	systemctl stop ${FUNCTION_SERVICE_NAME}

	rm -f ${SERVICE_FILE_DEST}/${FUNCTION_SRC_SERVICE_FILE}

	systemctl daemon-reload

clean:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~'    -exec rm --force {} +
	find . -name '__pycache__'  -exec rm -rd --force {} +

