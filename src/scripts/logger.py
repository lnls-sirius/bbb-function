#!/usr/bin/python-sirius
import logging
from logging.handlers import RotatingFileHandler


def get_logger(name, logfile="/var/log/bbbfunction.log"):
    logger = logging.getLogger(name)
    formatter = logging.Formatter(
        "%(asctime)-15s - (%(name)s) %(levelname)s - %(message)s", datefmt="%d/%m/%Y %H:%M:%S"
    )

    file_handler = RotatingFileHandler(logfile, maxBytes=15000000, backupCount=5)
    file_handler.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(file_handler)

    logger.setLevel(logging.INFO)

    return logger


    