#!/usr/bin/python-sirius
import logging
from logging.handlers import RotatingFileHandler


def get_logger(name):
    logger = logging.getLogger(name)
    formatter = logging.Formatter(
        "%(asctime)-15s - (%(name)s) %(levelname)s - %(message)s", datefmt="%d/%m/%Y %H:%M:%S"
    )

    file_handler = RotatingFileHandler("/var/log/bbbfunction.log", maxBytes=15000000, backupCount=5)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

    return logger