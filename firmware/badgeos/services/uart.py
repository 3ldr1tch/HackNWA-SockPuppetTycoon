"""
BadgeOS UART Toolkit Service.

Owns the hardware UART driver and exposes UART operations to
other BadgeOS components such as the serial shell.

UART Toolkit v0.1:
    TX: GP2
    RX: GP3
    default: 115200 8N1
"""

import time

from badgeos.core import Service
from badgeos.drivers.uart import UARTDriver


class UARTService(Service):
    """BadgeOS UART Toolkit service."""

    LOOPBACK_PAYLOAD = (
        b"SOCKPUPPET UART TEST 001\r\n"
    )

    def __init__(
        self,
        tx_pin,
        rx_pin,
        baudrate=115200,
    ):
        super().__init__("UART")

        self.driver = UARTDriver(
            tx_pin,
            rx_pin,
            baudrate=baudrate,
            timeout=0,
        )

        self.tx_name = "GP2"
        self.rx_name = "GP3"

        self.tx_bytes = 0
        self.rx_bytes = 0

    def initialize(self):
        self.driver.initialize()

        super().initialize()

        self.log.info(
            "UART initialized: TX {} RX {} @ {} 8N1".format(
                self.tx_name,
                self.rx_name,
                self.driver.baudrate,
            )
        )

    def shutdown(self):
        self.driver.deinit()

        self.log.info(
            "UART stopped"
        )

        super().shutdown()

    def update(self):
        """
        UART v0.1 does not consume RX asynchronously.

        This is intentional. Shell commands such as `uart read`
        own RX consumption for now. A later monitor/bridge service
        will add buffered asynchronous receive handling.
        """
        pass

    @property
    def baudrate(self):
        return self.driver.baudrate

    @property
    def waiting(self):
        return self.driver.in_waiting

    def set_baudrate(self, baudrate):
        value = self.driver.set_baudrate(
            baudrate
        )

        self.log.info(
            "Baud rate changed to {}".format(
                value
            )
        )

        return value

    def send(self, data):
        count = self.driver.write(
            data
        )

        if count:
            self.tx_bytes += count

        return count or 0

    def read(self):
        data = self.driver.read()

        if data:
            self.rx_bytes += len(data)

        return data

    def drain(self):
        return self.driver.drain()

    def loopback_test(self):
        """
        Perform a controlled TX -> RX loopback test.

        GP2 must be physically jumpered to GP3.
        """

        self.driver.drain()

        payload = self.LOOPBACK_PAYLOAD

        sent = self.driver.write(
            payload
        ) or 0

        self.tx_bytes += sent

        # At 115200 baud the payload only needs a few milliseconds.
        # 50 ms gives the UART plenty of time without making the shell
        # noticeably sluggish.
        time.sleep(
            0.05
        )

        received = self.driver.read()

        if received:
            self.rx_bytes += len(
                received
            )

        return {
            "payload": payload,
            "sent": sent,
            "received": received,
            "passed": received == payload,
        }

    @property
    def status(self):
        return {
            "active": self.driver.active,
            "tx": self.tx_name,
            "rx": self.rx_name,
            "baudrate": self.driver.baudrate,
            "waiting": self.driver.in_waiting,
            "tx_bytes": self.tx_bytes,
            "rx_bytes": self.rx_bytes,
        }
