"""
BadgeOS UART Toolkit Service.

UART Toolkit v0.3

Provides:
    - asynchronous UART receive
    - fixed-size circular RX buffer
    - RX/TX statistics
    - ASCII capture dump
    - hexadecimal capture dump
    - buffer clearing
    - runtime baud-rate switching
    - loopback testing
    - non-blocking passive baud probing

Default wiring:
    TX: GP2
    RX: GP3
    115200 8N1
"""

import time

from badgeos.core import Service
from badgeos.drivers.uart import UARTDriver


class UARTService(Service):
    """BadgeOS UART Toolkit service."""

    LOOPBACK_PAYLOAD = (
        b"SOCKPUPPET UART TEST 001\r\n"
    )

    DEFAULT_BUFFER_SIZE = 2048

    PROBE_RATES = (
        9600,
        19200,
        38400,
        57600,
        115200,
        230400,
    )

    PROBE_WINDOW = 0.75

    def __init__(
        self,
        tx_pin,
        rx_pin,
        baudrate=115200,
        buffer_size=DEFAULT_BUFFER_SIZE,
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

        self.buffer_size = int(buffer_size)

        if self.buffer_size < 64:
            raise ValueError(
                "UART buffer must be at least 64 bytes."
            )

        self._rx_buffer = bytearray(
            self.buffer_size
        )

        self._rx_head = 0
        self._rx_count = 0

        self.tx_bytes = 0
        self.rx_bytes = 0

        self.rx_overruns = 0

        # Passive baud probe state.
        self._probe_active = False
        self._probe_index = 0
        self._probe_started = 0.0
        self._probe_original_baud = baudrate
        self._probe_sample = bytearray()
        self._probe_results = []
        self._probe_complete = False
        self._probe_cancelled = False

    # ---------------------------------------------------------
    # Service lifecycle
    # ---------------------------------------------------------

    def initialize(self):
        self.driver.initialize()

        self.driver.drain()

        super().initialize()

        self.log.info(
            "UART initialized: TX {} RX {} @ {} 8N1".format(
                self.tx_name,
                self.rx_name,
                self.driver.baudrate,
            )
        )

        self.log.info(
            "UART RX buffer: {} bytes".format(
                self.buffer_size
            )
        )

    def shutdown(self):
        if self._probe_active:
            self.stop_probe()

        self.driver.deinit()

        self.log.info(
            "UART stopped"
        )

        super().shutdown()

    def update(self):
        """
        Service UART RX and advance passive baud probing.

        This method never waits for input. BadgeOS calls it repeatedly
        from the cooperative scheduler.
        """

        waiting = self.driver.in_waiting

        if waiting:
            data = self.driver.read(
                waiting
            )

            if data:
                if self._probe_active:
                    self._probe_sample.extend(
                        data
                    )
                else:
                    self._store_rx(
                        data
                    )

        if self._probe_active:
            self._update_probe()

    # ---------------------------------------------------------
    # Circular receive buffer
    # ---------------------------------------------------------

    def _store_rx(self, data):
        """
        Append bytes to the circular capture buffer.

        When full, the oldest byte is overwritten.
        """

        for value in data:
            self._rx_buffer[
                self._rx_head
            ] = value

            self._rx_head = (
                self._rx_head + 1
            ) % self.buffer_size

            if self._rx_count < self.buffer_size:
                self._rx_count += 1
            else:
                self.rx_overruns += 1

            self.rx_bytes += 1

    def snapshot(self):
        """
        Return buffered RX bytes oldest -> newest.

        The capture is not removed.
        """

        count = self._rx_count

        if count == 0:
            return b""

        start = (
            self._rx_head - count
        ) % self.buffer_size

        if start < self._rx_head:
            return bytes(
                self._rx_buffer[
                    start:self._rx_head
                ]
            )

        return bytes(
            self._rx_buffer[
                start:
            ]
            +
            self._rx_buffer[
                :self._rx_head
            ]
        )

    def clear(self):
        """
        Clear captured RX data.

        Lifetime byte statistics are retained.
        """

        cleared = self._rx_count

        self._rx_head = 0
        self._rx_count = 0

        return cleared

    @property
    def buffered(self):
        return self._rx_count

    # ---------------------------------------------------------
    # UART configuration / TX
    # ---------------------------------------------------------

    @property
    def baudrate(self):
        return self.driver.baudrate

    @property
    def waiting(self):
        return self.driver.in_waiting

    def set_baudrate(self, baudrate):
        if self._probe_active:
            raise RuntimeError(
                "Cannot manually change baud during probe."
            )

        value = self.driver.set_baudrate(
            baudrate
        )

        self.clear()
        self.driver.drain()

        self.log.info(
            "Baud rate changed to {}".format(
                value
            )
        )

        return value

    def send(self, data):
        if self._probe_active:
            raise RuntimeError(
                "UART TX disabled during passive probe."
            )

        count = self.driver.write(
            data
        )

        if count:
            self.tx_bytes += count

        return count or 0

    # ---------------------------------------------------------
    # Compatibility read
    # ---------------------------------------------------------

    def read(self):
        """
        Return the current capture snapshot.
        """

        return self.snapshot()

    def drain(self):
        """
        Clear both BadgeOS capture and hardware RX FIFO.
        """

        captured = self.clear()
        hardware = self.driver.drain()

        return captured + hardware

    # ---------------------------------------------------------
    # Loopback test
    # ---------------------------------------------------------

    def loopback_test(self):
        """
        Perform controlled GP2 TX -> GP3 RX loopback.
        """

        if self._probe_active:
            raise RuntimeError(
                "Cannot run loopback during passive probe."
            )

        self.drain()

        payload = self.LOOPBACK_PAYLOAD

        sent = self.driver.write(
            payload
        ) or 0

        self.tx_bytes += sent

        time.sleep(
            0.05
        )

        received = self.driver.read()

        if received:
            self._store_rx(
                received
            )

        return {
            "payload": payload,
            "sent": sent,
            "received": received,
            "passed": received == payload,
        }

    # ---------------------------------------------------------
    # Passive baud probe
    # ---------------------------------------------------------

    @property
    def probe_active(self):
        return self._probe_active

    @property
    def probe_complete(self):
        return self._probe_complete

    @property
    def probe_results(self):
        return list(
            self._probe_results
        )

    def start_probe(self):
        """
        Begin a non-blocking passive baud probe.

        Nothing is transmitted. The service cycles through common
        baud rates and scores received data for text-like structure.
        """

        if self._probe_active:
            raise RuntimeError(
                "UART probe already running."
            )

        self._probe_original_baud = (
            self.driver.baudrate
        )

        self._probe_index = 0
        self._probe_results = []
        self._probe_sample = bytearray()
        self._probe_complete = False
        self._probe_cancelled = False
        self._probe_active = True

        self.clear()

        self._begin_probe_rate(
            self.PROBE_RATES[0]
        )

        self.log.info(
            "Passive UART baud probe started"
        )

        return self.probe_status

    def stop_probe(self):
        """
        Cancel an active probe and restore the original baud rate.
        """

        if not self._probe_active:
            return False

        self._probe_active = False
        self._probe_cancelled = True

        self.driver.set_baudrate(
            self._probe_original_baud
        )

        self.driver.drain()

        self.log.info(
            "Passive UART baud probe stopped"
        )

        return True

    def _begin_probe_rate(self, baudrate):
        """
        Switch to one probe rate and start a fresh sample window.
        """

        self.driver.set_baudrate(
            baudrate
        )

        self.driver.drain()

        self._probe_sample = bytearray()
        self._probe_started = time.monotonic()

    def _update_probe(self):
        """
        Advance the asynchronous probe state machine.
        """

        elapsed = (
            time.monotonic()
            - self._probe_started
        )

        if elapsed < self.PROBE_WINDOW:
            return

        baudrate = self.PROBE_RATES[
            self._probe_index
        ]

        sample = bytes(
            self._probe_sample
        )

        result = self._score_probe_sample(
            baudrate,
            sample,
        )

        self._probe_results.append(
            result
        )

        self._probe_index += 1

        if self._probe_index >= len(
            self.PROBE_RATES
        ):
            self._finish_probe()
            return

        self._begin_probe_rate(
            self.PROBE_RATES[
                self._probe_index
            ]
        )

    def _finish_probe(self):
        """
        Finish probing and select the highest-scoring candidate.
        """

        self._probe_active = False
        self._probe_complete = True

        best = self.best_probe_result()

        if best is not None and best["bytes"] > 0:
            restore_baud = best["baudrate"]
        else:
            restore_baud = self._probe_original_baud

        self.driver.set_baudrate(
            restore_baud
        )

        self.driver.drain()

        self.log.info(
            "Passive UART baud probe complete"
        )

    def _score_probe_sample(
        self,
        baudrate,
        data,
    ):
        """
        Score a UART sample for likely human-readable serial text.

        This is deliberately heuristic. A high score means the sample
        looks plausible, not that the baud rate is proven correct.
        """

        total = len(data)

        if total == 0:
            return {
                "baudrate": baudrate,
                "bytes": 0,
                "printable": 0,
                "linebreaks": 0,
                "controls": 0,
                "score": 0,
                "label": "no data",
            }

        printable = 0
        linebreaks = 0
        controls = 0

        for value in data:
            if 32 <= value <= 126:
                printable += 1
            elif value in (9, 10, 13):
                printable += 1

                if value in (10, 13):
                    linebreaks += 1
            else:
                controls += 1

        printable_percent = int(
            (printable * 100) / total
        )

        control_percent = int(
            (controls * 100) / total
        )

        score = printable_percent

        if linebreaks:
            score += 8

        if total >= 16:
            score += 4

        if total >= 64:
            score += 4

        if total >= 128:
            score += 4

        if control_percent >= 25:
            score -= 15

        if control_percent >= 50:
            score -= 20

        if score < 0:
            score = 0

        if score > 100:
            score = 100

        if score >= 85:
            label = "likely text"
        elif score >= 65:
            label = "plausible"
        elif score >= 40:
            label = "weak"
        else:
            label = "unlikely"

        return {
            "baudrate": baudrate,
            "bytes": total,
            "printable": printable_percent,
            "linebreaks": linebreaks,
            "controls": control_percent,
            "score": score,
            "label": label,
        }

    def best_probe_result(self):
        """
        Return the highest-scoring probe result.
        """

        if not self._probe_results:
            return None

        best = None

        for result in self._probe_results:
            if best is None:
                best = result
                continue

            if result["score"] > best["score"]:
                best = result
                continue

            if (
                result["score"] == best["score"]
                and result["bytes"] > best["bytes"]
            ):
                best = result

        return best

    @property
    def probe_status(self):
        current_rate = None
        elapsed = 0.0

        if self._probe_active:
            current_rate = self.PROBE_RATES[
                self._probe_index
            ]

            elapsed = (
                time.monotonic()
                - self._probe_started
            )

        return {
            "active": self._probe_active,
            "complete": self._probe_complete,
            "cancelled": self._probe_cancelled,
            "index": self._probe_index,
            "count": len(self.PROBE_RATES),
            "current_rate": current_rate,
            "elapsed": elapsed,
            "window": self.PROBE_WINDOW,
            "sample_bytes": len(
                self._probe_sample
            ),
            "original_baud": self._probe_original_baud,
            "results": self.probe_results,
            "best": self.best_probe_result(),
        }

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    @property
    def status(self):
        return {
            "active": self.driver.active,
            "tx": self.tx_name,
            "rx": self.rx_name,
            "baudrate": self.driver.baudrate,
            "hardware_waiting": self.driver.in_waiting,
            "buffered": self._rx_count,
            "buffer_size": self.buffer_size,
            "tx_bytes": self.tx_bytes,
            "rx_bytes": self.rx_bytes,
            "rx_overruns": self.rx_overruns,
            "probe_active": self._probe_active,
            "probe_complete": self._probe_complete,
        }
