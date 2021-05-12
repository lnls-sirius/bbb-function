#!/usr/bin/python3
import argparse
import logging
import socket
import logging.handlers
import time

from serial import Serial
from logger import get_logger

if __name__ == "__main__":

    parser = argparse.ArgumentParser("TCP - Serial Bind")
    parser.add_argument("--debug", dest="debug", action="store_true")

    parser.add_argument("--terminator", default="", help="Termination string.", dest="terminator")

    parser.add_argument("--logging-ip", default="10.128.255.5", help="Remote logging server ip.", dest="logging_ip")
    parser.add_argument("--port", "-p", default=4161, type=int, help="TCP Server port", dest="port")
    parser.add_argument("--tcp-buffer", "-tcpb", default=1024, type=int, help="TCP recv buffer", dest="tcp_buffer")
    parser.add_argument("--baudrate", "-b", default=115200, type=int, help="Serial port baudrate", dest="baudrate")
    parser.add_argument(
        "--serial-buffer-timeout",
        default=0.05,
        type=float,
        help="Maximum time to wait for the input buffer to fill after the first byte is detected inside the buffer.",
        dest="ser_buff_tout",
    )
    parser.add_argument("--timeout", "-t", default=0.1, type=float, help="Serial port timeout", dest="timeout")
    parser.add_argument("--device", "-d", default="/dev/ttyUSB0", help="Serial port full path", dest="device")

    parser.add_argument(
        "--zero-bytes",
        "-zb",
        default="ZB",
        help="What to return when a zero lengh response is returned from the serial port.",
        dest="zero_bytes",
    )
    args = parser.parse_args()

    zb = args.zero_bytes.encode("utf-8")
    terminator = args.terminator.encode("utf-8")

    logger = get_logger("TCP Serial")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(levelname)s] %(message)s", datefmt="%d/%m/%Y %H:%M:%S.%f")

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)
    consoleHandler.setLevel(logging.INFO)
    logger.addHandler(consoleHandler)

    if args.debug:
        socketHandler = logging.handlers.SocketHandler(args.logging_ip, logging.handlers.DEFAULT_TCP_LOGGING_PORT)
        socketHandler.setFormatter(formatter)
        socketHandler.setLevel(logging.DEBUG)
        logger.addHandler(socketHandler)
        logger.info("Network logging enable {}.".format(args.logging_ip))

    ser = Serial(args.device, args.baudrate, timeout=args.timeout)
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", args.port))
            s.listen()
            logger.info("Listening...")
            conn, addr = s.accept()
            conn.settimeout(10)
            try:
                with conn:
                    logger.info("Connected {} {}".format(conn, addr))
                    while True:
                        data = conn.recv(args.tcp_buffer)

                        if not data:
                            logger.warn("No data from IOC...")
                            break

                        ser.reset_input_buffer()
                        ser.reset_output_buffer()

                        ser.write(data)
                        res = ser.read(1)
                        time.sleep(args.ser_buff_tout)
                        if ser.in_waiting > 0:
                            res += ser.read_all()
                        res = res + terminator if res else zb + terminator

                        conn.sendall(res)
                        logger.debug("In=%s     Out=%s     len=%s" % (data, res, len(res)))
            except ConnectionError:
                logger.exception("Connection Error!")
            except socket.timeout:
                logger.exception("TCP Timeout")
