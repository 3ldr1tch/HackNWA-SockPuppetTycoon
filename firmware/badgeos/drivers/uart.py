"""
BadgeOS UART Driver.

Low-level hardware UART access for the RP2350.

Default BadgeOS UART Toolkit wiring:
    TX: GP2
    RX: GP3

The driver is intentionally unaware of the BadgeOS shell and scheduler.
It only owns and operates the hardware UART peripheral.
"""

import busio


class UARTDriver:
    """Low-level BadgeOS hardware UART driver."""

    def __init__(
        self,
        tx_pin,
        rx_pin,
        baudrate=115200,
        timeout=0,
    ):
        self.tx_pin = tx_pin
        self.rx_pin = rx_pin
        self.baudrate = baudrate
        self.timeout = timeout

        self.uart = None

    @property
    def active(self):
        return self.uart is not None

    @property
    def in_waiting(self):
        if self.uart is None:
            return 0

        return self.uart.in_waiting

    def initialize(self):
        if self.uart is not None:
            return

        self.uart = busio.UART(
            self.tx_pin,
            self.rx_pin,
            baudrate=self.baudrate,
            timeout=self.timeout,
        )

    def deinit(self):
        if self.uart is None:
            return

        self.uart.deinit()
        self.uart = None

    def set_baudrate(self, baudrate):
        """
        Reconfigure the UART at a new baud rate.
        """

        baudrate = int(baudrate)

        if baudrate <= 0:
            raise ValueError(
                "Baud rate must be greater than zero."
            )

        was_active = self.active

        if was_active:
            self.deinit()

        self.baudrate = baudrate

        if was_active:
            self.initialize()

        return self.baudrate

    def write(self, data):
        if self.uart is None:
            raise RuntimeError(
                "UART is not initialized."
            )

        if isinstance(data, str):
            data = data.encode("utf-8")

        return self.uart.write(data)

    def read(self, count=None):
        if self.uart is None:
            raise RuntimeError(
                "UART is not initialized."
            )

        if count is None:
            count = self.uart.in_waiting

        if not count:
            return None

        return self.uart.read(count)

    def drain(self):
        """
        Discard all currently buffered RX data.

        Useful before a controlled loopback test because a floating RX
        pin may have produced garbage bytes.
        """

        total = 0

        while self.uart is not None:
            waiting = self.uart.in_waiting

            if not waiting:
                break

            data = self.uart.read(waiting)

            if not data:
                break

            total += len(data)

        return total
