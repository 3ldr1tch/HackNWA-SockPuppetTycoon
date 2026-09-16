#!/usr/bin/env python3

from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parent.parent

SERVICES_INIT = (
    ROOT / "firmware/badgeos/services/__init__.py"
)

APPLICATION = (
    ROOT / "firmware/badgeos/application.py"
)

SHELL = (
    ROOT / "firmware/badgeos/services/serial_shell.py"
)


def backup(path):
    target = path.with_suffix(
        path.suffix + ".pre-uart-toolkit"
    )

    if not target.exists():
        shutil.copy2(
            path,
            target,
        )

    return target


def replace_once(
    text,
    old,
    new,
    label,
):
    count = text.count(
        old
    )

    if count != 1:
        raise RuntimeError(
            "{}: expected exactly one anchor, found {}".format(
                label,
                count,
            )
        )

    return text.replace(
        old,
        new,
        1,
    )


# ------------------------------------------------------------
# services/__init__.py
# ------------------------------------------------------------

text = SERVICES_INIT.read_text()

if (
    "from .uart import UARTService"
    not in text
):
    text = replace_once(
        text,
        "from .serial_shell import SerialShellService\n",
        (
            "from .serial_shell import SerialShellService\n"
            "from .uart import UARTService\n"
        ),
        "services import",
    )

if '"UARTService",' not in text:
    text = replace_once(
        text,
        '    "SerialShellService",\n',
        (
            '    "SerialShellService",\n'
            '    "UARTService",\n'
        ),
        "services __all__",
    )

backup(
    SERVICES_INIT
)

SERVICES_INIT.write_text(
    text
)


# ------------------------------------------------------------
# application.py
# ------------------------------------------------------------

text = APPLICATION.read_text()

if "    UARTService,\n" not in text:
    text = replace_once(
        text,
        "    SerialShellService,\n",
        (
            "    SerialShellService,\n"
            "    UARTService,\n"
        ),
        "application import",
    )

if "self.uart_service = None" not in text:
    text = replace_once(
        text,
        "        self.serial_shell = None\n",
        (
            "        self.serial_shell = None\n"
            "        self.uart_service = None\n"
        ),
        "application uart attribute",
    )

if "self.uart_service = (" not in text:
    anchor = """            self.serial_shell = (
                SerialShellService(
                    self.led,
                    self.mode_manager,
                )
            )
"""

    replacement = """            self.uart_service = (
                UARTService(
                    board.GP2,
                    board.GP3,
                    baudrate=115200,
                )
            )

            self.serial_shell = (
                SerialShellService(
                    self.led,
                    self.mode_manager,
                    self.uart_service,
                )
            )
"""

    text = replace_once(
        text,
        anchor,
        replacement,
        "application service construction",
    )

if (
    "self.scheduler.register(\n"
    "                self.uart_service\n"
    "            )"
    not in text
):
    anchor = """            self.scheduler.register(
                self.serial_shell
            )
"""

    replacement = """            self.scheduler.register(
                self.uart_service
            )

            self.scheduler.register(
                self.serial_shell
            )
"""

    text = replace_once(
        text,
        anchor,
        replacement,
        "application scheduler",
    )

backup(
    APPLICATION
)

APPLICATION.write_text(
    text
)


# ------------------------------------------------------------
# serial_shell.py
# ------------------------------------------------------------

text = SHELL.read_text()

if (
    "def __init__(self, led, mode_manager, uart_service=None):"
    not in text
):
    text = replace_once(
        text,
        "    def __init__(self, led, mode_manager):\n",
        (
            "    def __init__("
            "self, led, mode_manager, uart_service=None):\n"
        ),
        "shell constructor",
    )

if "self.uart_service = uart_service" not in text:
    text = replace_once(
        text,
        "        self.mode_manager = mode_manager\n",
        (
            "        self.mode_manager = mode_manager\n"
            "        self.uart_service = uart_service\n"
        ),
        "shell uart attribute",
    )

if (
    '"uart": lambda: self._command_uart(parts),'
    not in text
):
    text = replace_once(
        text,
        '            "led": lambda: self._command_led(parts),\n',
        (
            '            "uart": lambda: '
            'self._command_uart(parts),\n'
            '            "led": lambda: '
            'self._command_led(parts),\n'
        ),
        "shell dispatch",
    )

if '"  uart             Show UART status",' not in text:
    text = replace_once(
        text,
        '            "  led <color>      Set LED ring color",\n',
        (
            '            "  uart             Show UART status",\n'
            '            "  uart send <text> Send UART text",\n'
            '            "  uart read        Read UART RX",\n'
            '            "  uart hex         Read UART RX as hex",\n'
            '            "  uart baud <rate> Set UART baud rate",\n'
            '            "  uart test        Run GP2->GP3 loopback",\n'
            '            "  led <color>      Set LED ring color",\n'
        ),
        "shell help",
    )

if "    def _command_uart(self, parts):\n" not in text:
    anchor = (
        "    def _command_led(self, parts):\n"
    )

    method = '''    def _command_uart(self, parts):
        uart = self.uart_service

        if uart is None:
            self._write_line(
                "UART service unavailable."
            )
            return

        if len(parts) == 1 or parts[1].lower() == "status":
            status = uart.status

            self._write_line(
                "UART Toolkit v0.1"
            )
            self._write_line(
                "-----------------"
            )
            self._write_line(
                "  state: {}".format(
                    "ready"
                    if status["active"]
                    else "inactive"
                )
            )
            self._write_line(
                "  TX: {}".format(
                    status["tx"]
                )
            )
            self._write_line(
                "  RX: {}".format(
                    status["rx"]
                )
            )
            self._write_line(
                "  baud: {}".format(
                    status["baudrate"]
                )
            )
            self._write_line(
                "  format: 8N1"
            )
            self._write_line(
                "  waiting: {} byte(s)".format(
                    status["waiting"]
                )
            )
            self._write_line(
                "  TX total: {} byte(s)".format(
                    status["tx_bytes"]
                )
            )
            self._write_line(
                "  RX total: {} byte(s)".format(
                    status["rx_bytes"]
                )
            )
            return

        command = parts[1].lower()

        if command == "send":
            if len(parts) < 3:
                self._write_line(
                    "Usage: uart send <text>"
                )
                return

            text = " ".join(
                parts[2:]
            )

            count = uart.send(
                text
            )

            self._write_line(
                "TX [{}]: {}".format(
                    count,
                    text,
                )
            )
            return

        if command == "read":
            data = uart.read()

            if not data:
                self._write_line(
                    "RX: no data"
                )
                return

            try:
                display = data.decode(
                    "utf-8"
                )
            except Exception:
                display = repr(
                    data
                )

            self._write_line(
                "RX [{}]: {}".format(
                    len(data),
                    display,
                )
            )
            return

        if command == "hex":
            data = uart.read()

            if not data:
                self._write_line(
                    "RX: no data"
                )
                return

            values = " ".join(
                "{:02X}".format(value)
                for value in data
            )

            self._write_line(
                "RX [{}]: {}".format(
                    len(data),
                    values,
                )
            )
            return

        if command == "baud":
            if len(parts) != 3:
                self._write_line(
                    "Usage: uart baud <rate>"
                )
                return

            try:
                baudrate = int(
                    parts[2]
                )

                uart.set_baudrate(
                    baudrate
                )

            except Exception as exc:
                self._write_line(
                    "UART baud error: {}".format(
                        exc
                    )
                )
                return

            self._write_line(
                "UART baud: {}".format(
                    uart.baudrate
                )
            )
            return

        if command == "test":
            self._write_line(
                "UART Loopback Test"
            )
            self._write_line(
                "------------------"
            )
            self._write_line(
                "Connect GP2 TX -> GP3 RX"
            )

            result = uart.loopback_test()

            payload = result[
                "payload"
            ]

            received = result[
                "received"
            ]

            self._write_line(
                "TX [{}]: {!r}".format(
                    result["sent"],
                    payload,
                )
            )

            if received is None:
                self._write_line(
                    "RX [0]: None"
                )
            else:
                self._write_line(
                    "RX [{}]: {!r}".format(
                        len(received),
                        received,
                    )
                )

            self._write_line(
                "Result: {}".format(
                    "PASS"
                    if result["passed"]
                    else "FAIL"
                )
            )
            return

        self._write_line(
            "Usage: uart <status|send|read|hex|baud|test>"
        )

'''

    text = replace_once(
        text,
        anchor,
        method + anchor,
        "shell UART method",
    )

backup(
    SHELL
)

SHELL.write_text(
    text
)


print("UART Toolkit integration complete.")
print("")
print("Modified:")
print("  firmware/badgeos/services/__init__.py")
print("  firmware/badgeos/application.py")
print("  firmware/badgeos/services/serial_shell.py")
print("")
print("Backups use suffix:")
print("  .pre-uart-toolkit")
