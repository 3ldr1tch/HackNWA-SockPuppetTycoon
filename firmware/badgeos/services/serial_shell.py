"""BadgeOS Serial Shell Service."""

import gc
import time
import usb_cdc
import microcontroller
import supervisor

from badgeos.core import Service
from badgeos.version import CODENAME, VERSION


class SerialShellService(Service):
    PROMPT = "badgeos> "
    HISTORY_LIMIT = 16

    def __init__(self, led, mode_manager, uart_service=None):
        super().__init__("SerialShell")

        self.led = led
        self.mode_manager = mode_manager
        self.uart_service = uart_service

        self.serial = None

        self._buffer = ""
        self._last_was_cr = False

        self._history = []
        self._history_index = None
        self._history_draft = ""

        self._escape_state = 0

    def initialize(self):
        super().initialize()

        self.serial = usb_cdc.data

        self._buffer = ""
        self._last_was_cr = False

        self._history = []
        self._history_index = None
        self._history_draft = ""

        self._escape_state = 0

        if self.serial is None:
            self.enabled = False

            self.log.error(
                "USB CDC data interface unavailable"
            )

            return

        self._drain_input()

        self.log.info(
            "Serial shell initialized"
        )

        self._show_banner()

        self._write_line(
            "Type 'help' for commands."
        )

        self._write_line("")

        self._prompt()

    def shutdown(self):
        self.serial = None

        self._buffer = ""
        self._last_was_cr = False

        self._history = []
        self._history_index = None
        self._history_draft = ""

        self._escape_state = 0

        self.log.info(
            "Serial shell stopped"
        )

        super().shutdown()

    def _drain_input(self):
        try:
            time.sleep(
                0.05
            )

            while self.serial.in_waiting:
                self.serial.read(
                    self.serial.in_waiting
                )

        except Exception:
            pass

    def update(self):
        if self.serial is None:
            return

        try:
            waiting = self.serial.in_waiting

            if not waiting:
                return

            data = self.serial.read(
                waiting
            )

            if not data:
                return

            try:
                text = data.decode(
                    "utf-8"
                )
            except Exception:
                return

            for character in text:
                self._process_character(
                    character
                )

        except Exception as exc:
            self.log.error(
                "CDC RX failed: {}: {}".format(
                    type(exc).__name__,
                    exc,
                )
            )

    def _process_character(self, character):
        if self._escape_state == 1:
            self._escape_state = (
                2
                if character == "["
                else 0
            )

            return

        if self._escape_state == 2:
            self._escape_state = 0

            if character == "A":
                self._history_previous()

            elif character == "B":
                self._history_next()

            return

        if character == "\x1b":
            self._escape_state = 1
            return

        if character == "\r":
            self._execute_buffer()
            self._last_was_cr = True
            return

        if character == "\n":
            if self._last_was_cr:
                self._last_was_cr = False
                return

            self._execute_buffer()
            return

        self._last_was_cr = False

        if character in ("\b", "\x7f"):
            if self._buffer:
                self._buffer = (
                    self._buffer[:-1]
                )

                self._write(
                    "\b \b"
                )

            return

        value = ord(
            character
        )

        if 32 <= value <= 126:
            if self._history_index is not None:
                self._history_index = None
                self._history_draft = ""

            self._buffer += character

            self._write(
                character
            )

    # ---------------------------------------------------------
    # History
    # ---------------------------------------------------------

    def _add_history(self, command):
        if not command:
            return

        if (
            self._history
            and self._history[-1] == command
        ):
            return

        self._history.append(
            command
        )

        if len(self._history) > self.HISTORY_LIMIT:
            self._history.pop(
                0
            )

    def _history_previous(self):
        if not self._history:
            return

        if self._history_index is None:
            self._history_draft = self._buffer

            self._history_index = (
                len(self._history) - 1
            )

        elif self._history_index > 0:
            self._history_index -= 1

        self._buffer = self._history[
            self._history_index
        ]

        self._redraw_input()

    def _history_next(self):
        if self._history_index is None:
            return

        if self._history_index < (
            len(self._history) - 1
        ):
            self._history_index += 1

            self._buffer = self._history[
                self._history_index
            ]

        else:
            self._history_index = None
            self._buffer = self._history_draft
            self._history_draft = ""

        self._redraw_input()

    def _redraw_input(self):
        self._write(
            "\r\x1b[2K"
        )

        self._write(
            self.PROMPT
        )

        self._write(
            self._buffer
        )

    def _command_history(self):
        if not self._history:
            self._write_line(
                "History is empty."
            )

            return

        self._write_line(
            "Command history:"
        )

        for i, command in enumerate(
            self._history,
            1,
        ):
            self._write_line(
                "  {:>2}  {}".format(
                    i,
                    command,
                )
            )

    # ---------------------------------------------------------
    # Command dispatch
    # ---------------------------------------------------------

    def _execute_buffer(self):
        command = self._buffer.strip()

        self._buffer = ""
        self._history_index = None
        self._history_draft = ""

        self._write_line("")

        if command:
            self._add_history(
                command
            )

            self._execute(
                command
            )

        self._prompt()

    def _execute(self, command):
        parts = command.split()

        if not parts:
            return

        name = parts[0].lower()

        dispatch = {
            "help": lambda: self._command_help(),
            "about": lambda: self._command_about(),
            "banner": lambda: self._show_banner(),
            "clear": lambda: self._command_clear(),
            "status": lambda: self._command_status(),
            "history": lambda: self._command_history(),
            "modes": lambda: self._command_modes(),
            "mode": lambda: self._command_mode(parts),
            "mem": lambda: self._command_mem(),
            "uptime": lambda: self._command_uptime(),
            "usb": lambda: self._command_usb(),
            "version": lambda: self._command_version(),
            "diag": lambda: self._command_diag(parts),
            "hid": lambda: self._command_hid(parts),
            "uart": lambda: self._command_uart(parts),
            "led": lambda: self._command_led(parts),
            "reboot": lambda: self._command_reboot(),
        }

        handler = dispatch.get(
            name
        )

        if handler:
            handler()

        else:
            self._write_line(
                "Unknown command: {}".format(
                    name
                )
            )

            self._write_line(
                "Type 'help' for commands."
            )

    # ---------------------------------------------------------
    # Help / banner / status
    # ---------------------------------------------------------

    def _command_help(self):
        lines = [
            "BadgeOS commands",
            "----------------",
            "  help             Show this help",
            "  about            Show BadgeOS information",
            "  banner           Show startup banner",
            "  clear            Clear the terminal",
            "  status           Show system status",
            "  history          Show command history",
            "  modes            List available modes",
            "  mode             Show active mode",
            "  mode next        Switch to next mode",
            "  mode prev        Switch to previous mode",
            "  mode <name>      Switch to named mode",
            "  mem              Show free RAM",
            "  uptime           Show uptime",
            "  usb              Show USB status",
            "  version          Show BadgeOS version",
            "  diag             Show diagnostics",
            "  diag <page>      Show one diagnostic",
            "  hid              Show HID toolkit status",
            "  hid host <os>    Set HID host profile",
            "  uart             Show UART status",
            "  uart send <text> Send UART text",
            "  uart dump        Show captured UART RX",
            "  uart hex         Show capture as hex",
            "  uart clear       Clear UART RX capture",
            "  uart stats       Show UART statistics",
            "  uart baud <rate> Set UART baud rate",
            "  uart rates       Show probe baud rates",
            "  uart probe       Start passive baud probe",
            "  uart probe status",
            "                   Show passive probe status",
            "  uart probe stop  Stop passive baud probe",
            "  uart test        Run GP2->GP3 loopback",
            "  led <color>      Set LED ring color",
            "  reboot           Reboot the badge",
            "",
            "History:",
            "  Up arrow         Previous command",
            "  Down arrow       Next command",
            "",
            "Examples:",
            "  mode next",
            "  mode HIDDemo",
            "  diag ram",
            "  led magenta",
            "  uart probe",
        ]

        for line in lines:
            self._write_line(
                line
            )

    def _show_banner(self):
        for line in (
            "",
            "========================================",
            "              BadgeOS",
            "         HackNWA Badge Runtime",
            "----------------------------------------",
            "  Version : {}".format(VERSION),
            "  Codename: {}".format(CODENAME),
            "========================================",
        ):
            self._write_line(
                line
            )

    def _command_about(self):
        self._show_banner()

        for line in (
            "",
            "BadgeOS is a modular CircuitPython runtime",
            "for the HackNWA Sock Puppet Tycoon badge.",
            "",
            "Capabilities:",
            "  - cooperative service scheduler",
            "  - event-driven input",
            "  - runtime mode switching",
            "  - NeoPixel effects",
            "  - USB HID keyboard",
            "  - USB CDC shell",
            "  - system diagnostics",
        ):
            self._write_line(
                line
            )

    def _command_clear(self):
        self._write(
            "\x1b[2J\x1b[H"
        )

        self._show_banner()

        self._write_line("")

    def _command_status(self):
        self._write_line(
            "BadgeOS status"
        )

        self._write_line(
            "--------------"
        )

        self._write_line(
            "  version: {}".format(
                VERSION
            )
        )

        self._write_line(
            "  codename: {}".format(
                CODENAME
            )
        )

        self._write_line(
            "  mode: {}".format(
                self._current_mode_name()
            )
        )

        self._write_line(
            "  modes: {}".format(
                len(self.mode_manager.modes())
            )
        )

        self._write_line(
            "  uptime: {} seconds".format(
                int(time.monotonic())
            )
        )

        self._write_line(
            "  free RAM: {} bytes".format(
                gc.mem_free()
            )
        )

        self._write_line(
            "  USB connected: {}".format(
                supervisor.runtime.usb_connected
            )
        )

        self._write_line(
            "  shell: running"
        )

    # ---------------------------------------------------------
    # Diagnostics
    # ---------------------------------------------------------

    def _command_mem(self):
        self._write_line(
            "Free RAM: {} bytes".format(
                gc.mem_free()
            )
        )

    def _command_uptime(self):
        self._write_line(
            "Uptime: {} seconds".format(
                int(time.monotonic())
            )
        )

    def _command_usb(self):
        self._write_line(
            "USB connected: {}".format(
                supervisor.runtime.usb_connected
            )
        )

    def _command_version(self):
        self._write_line(
            "BadgeOS {} ({})".format(
                VERSION,
                CODENAME,
            )
        )

    def _command_diag(self, parts):
        if len(parts) == 1:
            self._write_line(
                "Diagnostics"
            )

            self._write_line(
                "-----------"
            )

            self._write_line(
                "  RAM free: {} bytes".format(
                    gc.mem_free()
                )
            )

            self._write_line(
                "  uptime: {} seconds".format(
                    int(time.monotonic())
                )
            )

            self._write_line(
                "  USB connected: {}".format(
                    supervisor.runtime.usb_connected
                )
            )

            self._write_line(
                "  version: {} ({})".format(
                    VERSION,
                    CODENAME,
                )
            )

            self._write_line(
                "  mode: {}".format(
                    self._current_mode_name()
                )
            )

            return

        if len(parts) != 2:
            self._write_line(
                "Usage: diag <ram|uptime|usb|version>"
            )

            return

        page = parts[1].lower()

        handlers = {
            "ram": self._command_mem,
            "uptime": self._command_uptime,
            "usb": self._command_usb,
            "version": self._command_version,
        }

        handler = handlers.get(
            page
        )

        if handler:
            handler()

        else:
            self._write_line(
                "Unknown diagnostic page: {}".format(
                    page
                )
            )

            self._write_line(
                "Valid pages: ram uptime usb version"
            )

    # ---------------------------------------------------------
    # Modes
    # ---------------------------------------------------------

    def _command_modes(self):
        modes = self.mode_manager.modes()

        if not modes:
            self._write_line(
                "No modes registered."
            )

            return

        self._write_line(
            "Available modes:"
        )

        current = self.mode_manager.current_mode

        for mode in modes:
            self._write_line(
                "  {} {}".format(
                    "*"
                    if mode is current
                    else " ",
                    mode.name,
                )
            )

    def _command_mode(self, parts):
        if len(parts) == 1:
            self._write_line(
                "Active mode: {}".format(
                    self._current_mode_name()
                )
            )

            return

        if len(parts) != 2:
            self._write_line(
                "Usage: mode <next|prev|name>"
            )

            return

        requested = parts[1]
        lowered = requested.lower()

        if lowered == "next":
            self._switch_relative_mode(
                1
            )

            return

        if lowered in (
            "prev",
            "previous",
        ):
            self._switch_relative_mode(
                -1
            )

            return

        mode = self.mode_manager.get_mode(
            requested
        )

        if mode is None:
            self._write_line(
                "Unknown mode: {}".format(
                    requested
                )
            )

            self._write_line(
                "Type 'modes' to list modes."
            )

            return

        if mode is self.mode_manager.current_mode:
            self._write_line(
                "Already active: {}".format(
                    mode.name
                )
            )

            return

        self.mode_manager.set_mode(
            mode
        )

        self._write_line(
            "Switched to mode: {}".format(
                mode.name
            )
        )

    def _switch_relative_mode(self, direction):
        modes = list(
            self.mode_manager.modes()
        )

        if not modes:
            self._write_line(
                "No modes registered."
            )

            return

        current = self.mode_manager.current_mode

        try:
            index = modes.index(
                current
            )

        except ValueError:
            index = 0

        mode = modes[
            (index + direction) % len(modes)
        ]

        self.mode_manager.set_mode(
            mode
        )

        self._write_line(
            "Switched to mode: {}".format(
                mode.name
            )
        )

    # ---------------------------------------------------------
    # HID toolkit
    # ---------------------------------------------------------

    def _command_hid(self, parts):
        mode = self.mode_manager.get_mode(
            "HIDDemo"
        )

        if mode is None:
            self._write_line(
                "HIDDemo mode unavailable."
            )

            return

        if len(parts) == 1:
            status = mode.get_status()

            self._write_line(
                "HID Toolkit"
            )

            self._write_line(
                "-----------"
            )

            self._write_line(
                "  host: {}".format(
                    status["host"]
                )
            )

            self._write_line(
                "  state: {}".format(
                    status["state"]
                )
            )

            self._write_line(
                "  executions: {}".format(
                    status["executions"]
                )
            )

            self._write_line(
                "  keyboard: {}".format(
                    "ready"
                    if status["keyboard"]
                    else "inactive"
                )
            )

            self._write_line("")

            self._write_line(
                "Usage: hid host <linux|windows|macos>"
            )

            return

        if (
            len(parts) == 3
            and parts[1].lower() == "host"
        ):
            try:
                host = mode.set_host_profile(
                    parts[2]
                )

            except ValueError:
                self._write_line(
                    "Unknown HID host: {}".format(
                        parts[2]
                    )
                )

                self._write_line(
                    "Valid hosts: linux windows macos"
                )

                return

            self._write_line(
                "HID host: {}".format(
                    host
                )
            )

            return

        self._write_line(
            "Usage: hid host <linux|windows|macos>"
        )

    # ---------------------------------------------------------
    # UART toolkit
    # ---------------------------------------------------------

    def _command_uart(self, parts):
        uart = self.uart_service

        if uart is None:
            self._write_line(
                "UART service unavailable."
            )

            return

        if (
            len(parts) == 1
            or parts[1].lower() == "status"
        ):
            self._show_uart_status(
                uart
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

            try:
                count = uart.send(
                    text
                )

            except Exception as exc:
                self._write_line(
                    "UART send error: {}".format(
                        exc
                    )
                )

                return

            self._write_line(
                "TX [{}]: {}".format(
                    count,
                    text,
                )
            )

            return

        if (
            command in (
                "read",
                "dump",
            )
            and not (
                command == "dump"
                and len(parts) >= 3
                and parts[2].lower() == "hex"
            )
        ):
            self._uart_dump(
                uart
            )

            return

        if (
            command == "hex"
            or (
                command == "dump"
                and len(parts) >= 3
                and parts[2].lower() == "hex"
            )
        ):
            self._uart_hex(
                uart
            )

            return

        if command == "clear":
            cleared = uart.clear()

            self._write_line(
                "UART RX buffer cleared: {} byte(s)".format(
                    cleared
                )
            )

            return

        if command == "stats":
            self._uart_stats(
                uart
            )

            return

        if command == "baud":
            self._uart_baud(
                uart,
                parts,
            )

            return

        if command == "rates":
            self._uart_rates(
                uart
            )

            return

        if command == "probe":
            self._uart_probe(
                uart,
                parts,
            )

            return

        if command == "test":
            self._uart_test(
                uart
            )

            return

        self._write_line(
            "Usage: uart <status|send|dump|hex|clear|stats|baud|rates|probe|test>"
        )

    def _show_uart_status(self, uart):
        status = uart.status

        self._write_line(
            "UART Toolkit v0.3"
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
            "  buffered: {}/{} byte(s)".format(
                status["buffered"],
                status["buffer_size"],
            )
        )

        self._write_line(
            "  hardware waiting: {} byte(s)".format(
                status["hardware_waiting"]
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

        self._write_line(
            "  overruns: {} byte(s)".format(
                status["rx_overruns"]
            )
        )

        self._write_line(
            "  probe: {}".format(
                "running"
                if status["probe_active"]
                else (
                    "complete"
                    if status["probe_complete"]
                    else "idle"
                )
            )
        )

    def _uart_dump(self, uart):
        data = uart.snapshot()

        if not data:
            self._write_line(
                "RX buffer empty."
            )

            return

        self._write_line(
            "UART RX capture [{} byte(s)]".format(
                len(data)
            )
        )

        self._write_line(
            "---------------------------"
        )

        output = ""

        for value in data:
            if value in (
                9,
                10,
                13,
            ):
                output += chr(
                    value
                )

            elif 32 <= value <= 126:
                output += chr(
                    value
                )

            else:
                output += "."

        self._write_line(
            output
        )

    def _uart_hex(self, uart):
        data = uart.snapshot()

        if not data:
            self._write_line(
                "RX buffer empty."
            )

            return

        self._write_line(
            "UART RX hex [{} byte(s)]".format(
                len(data)
            )
        )

        self._write_line(
            "-------------------------"
        )

        offset = 0

        while offset < len(data):
            chunk = data[
                offset:offset + 16
            ]

            values = " ".join(
                "{:02X}".format(
                    value
                )
                for value in chunk
            )

            self._write_line(
                "{:04X}: {}".format(
                    offset,
                    values,
                )
            )

            offset += 16

    def _uart_stats(self, uart):
        status = uart.status

        self._write_line(
            "UART Statistics"
        )

        self._write_line(
            "---------------"
        )

        self._write_line(
            "  buffered: {}/{} byte(s)".format(
                status["buffered"],
                status["buffer_size"],
            )
        )

        self._write_line(
            "  RX total: {} byte(s)".format(
                status["rx_bytes"]
            )
        )

        self._write_line(
            "  TX total: {} byte(s)".format(
                status["tx_bytes"]
            )
        )

        self._write_line(
            "  overruns: {} byte(s)".format(
                status["rx_overruns"]
            )
        )

    def _uart_baud(self, uart, parts):
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

    def _uart_rates(self, uart):
        self._write_line(
            "UART Passive Probe Rates"
        )

        self._write_line(
            "------------------------"
        )

        for rate in uart.PROBE_RATES:
            self._write_line(
                "  {}".format(
                    rate
                )
            )

        self._write_line(
            ""
        )

        self._write_line(
            "Window: {:.2f} second(s) per rate".format(
                uart.PROBE_WINDOW
            )
        )

        self._write_line(
            "Probe is RX-only; BadgeOS does not transmit."
        )

    def _uart_probe(self, uart, parts):
        if len(parts) == 2:
            try:
                status = uart.start_probe()

            except Exception as exc:
                self._write_line(
                    "UART probe error: {}".format(
                        exc
                    )
                )

                return

            self._write_line(
                "UART Passive Probe"
            )

            self._write_line(
                "------------------"
            )

            self._write_line(
                "Probe started."
            )

            self._write_line(
                "RX-only: GP2 TX will not transmit."
            )

            self._write_line(
                "Rates: {}".format(
                    " ".join(
                        str(rate)
                        for rate in uart.PROBE_RATES
                    )
                )
            )

            self._write_line(
                "Window: {:.2f}s per rate".format(
                    status["window"]
                )
            )

            self._write_line(
                "Use 'uart probe status' for results."
            )

            return

        if len(parts) != 3:
            self._write_line(
                "Usage: uart probe <status|stop>"
            )

            return

        action = parts[2].lower()

        if action == "status":
            self._show_uart_probe_status(
                uart
            )

            return

        if action == "stop":
            stopped = uart.stop_probe()

            if stopped:
                self._write_line(
                    "UART passive probe stopped."
                )

                self._write_line(
                    "Restored baud: {}".format(
                        uart.baudrate
                    )
                )

            else:
                self._write_line(
                    "UART probe is not running."
                )

            return

        self._write_line(
            "Usage: uart probe <status|stop>"
        )

    def _show_uart_probe_status(self, uart):
        status = uart.probe_status

        self._write_line(
            "UART Passive Probe"
        )

        self._write_line(
            "------------------"
        )

        if status["active"]:
            self._write_line(
                "  state: running"
            )

            self._write_line(
                "  rate: {}".format(
                    status["current_rate"]
                )
            )

            self._write_line(
                "  progress: {}/{}".format(
                    status["index"] + 1,
                    status["count"],
                )
            )

            self._write_line(
                "  sample: {} byte(s)".format(
                    status["sample_bytes"]
                )
            )

            self._write_line(
                "  elapsed: {:.2f}/{:.2f}s".format(
                    status["elapsed"],
                    status["window"],
                )
            )

        elif status["cancelled"]:
            self._write_line(
                "  state: stopped"
            )

        elif status["complete"]:
            self._write_line(
                "  state: complete"
            )

        else:
            self._write_line(
                "  state: idle"
            )

        results = status["results"]

        if not results:
            self._write_line(
                "  results: none yet"
            )

            return

        self._write_line(
            ""
        )

        self._write_line(
            "  baud     score  bytes  printable  result"
        )

        self._write_line(
            "  -------  -----  -----  ---------  -----------"
        )

        for result in results:
            self._write_line(
                "  {:>7}  {:>5}  {:>5}  {:>8}%  {}".format(
                    result["baudrate"],
                    result["score"],
                    result["bytes"],
                    result["printable"],
                    result["label"],
                )
            )

        best = status["best"]

        if best is not None and best["bytes"] > 0:
            self._write_line(
                ""
            )

            self._write_line(
                "Best candidate: {} baud".format(
                    best["baudrate"]
                )
            )

            self._write_line(
                "Score: {} ({})".format(
                    best["score"],
                    best["label"],
                )
            )

            self._write_line(
                "Current UART baud: {}".format(
                    uart.baudrate
                )
            )

            self._write_line(
                "Candidate is heuristic, not proof."
            )

        elif status["complete"]:
            self._write_line(
                ""
            )

            self._write_line(
                "No UART traffic detected."
            )

            self._write_line(
                "Restored baud: {}".format(
                    uart.baudrate
                )
            )

    def _uart_test(self, uart):
        self._write_line(
            "UART Loopback Test"
        )

        self._write_line(
            "------------------"
        )

        self._write_line(
            "Connect GP2 TX -> GP3 RX"
        )

        try:
            result = uart.loopback_test()

        except Exception as exc:
            self._write_line(
                "UART test error: {}".format(
                    exc
                )
            )

            return

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

    # ---------------------------------------------------------
    # LEDs / reboot
    # ---------------------------------------------------------

    def _command_led(self, parts):
        if len(parts) != 2:
            self._write_line(
                "Usage: led <color>"
            )

            return

        color = parts[1].lower()

        commands = {
            "red": self.led.red,
            "green": self.led.green,
            "blue": self.led.blue,
            "yellow": self.led.yellow,
            "cyan": self.led.cyan,
            "magenta": self.led.magenta,
            "purple": self.led.magenta,
            "white": self.led.white,
            "off": self.led.off,
        }

        if color == "orange":
            self.led.fill(
                (255, 80, 0)
            )

            self._write_line(
                "LED: orange"
            )

            return

        if color not in commands:
            self._write_line(
                "Unknown LED color: {}".format(
                    color
                )
            )

            self._write_line(
                "Type 'help' to list colors."
            )

            return

        commands[color]()

        self._write_line(
            "LED: {}".format(
                color
            )
        )

    def _command_reboot(self):
        self._write_line(
            "Rebooting BadgeOS..."
        )

        self._write_line(
            "USB connection will disconnect."
        )

        try:
            self.serial.flush()

        except Exception:
            pass

        time.sleep(
            0.20
        )

        microcontroller.reset()

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _current_mode_name(self):
        mode = self.mode_manager.current_mode

        return (
            "none"
            if mode is None
            else mode.name
        )

    def _write(self, text):
        if self.serial is None:
            return

        try:
            self.serial.write(
                text.encode("utf-8")
            )

        except Exception:
            pass

    def _write_line(self, text):
        self._write(
            text + "\r\n"
        )

    def _prompt(self):
        self._write(
            self.PROMPT
        )
