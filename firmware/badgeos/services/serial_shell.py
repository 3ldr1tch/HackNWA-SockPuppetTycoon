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

    def __init__(self, led, mode_manager):
        super().__init__("SerialShell")
        self.led = led
        self.mode_manager = mode_manager
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
            self.log.error("USB CDC data interface unavailable")
            return
        self._drain_input()
        self.log.info("Serial shell initialized")
        self._show_banner()
        self._write_line("Type 'help' for commands.")
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
        self.log.info("Serial shell stopped")
        super().shutdown()

    def _drain_input(self):
        try:
            time.sleep(0.05)
            while self.serial.in_waiting:
                self.serial.read(self.serial.in_waiting)
        except Exception:
            pass

    def update(self):
        if self.serial is None:
            return
        try:
            waiting = self.serial.in_waiting
            if not waiting:
                return
            data = self.serial.read(waiting)
            if not data:
                return
            try:
                text = data.decode("utf-8")
            except Exception:
                return
            for character in text:
                self._process_character(character)
        except Exception as exc:
            self.log.error("CDC RX failed: {}: {}".format(type(exc).__name__, exc))

    def _process_character(self, character):
        if self._escape_state == 1:
            self._escape_state = 2 if character == "[" else 0
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
                self._buffer = self._buffer[:-1]
                self._write("\b \b")
            return
        value = ord(character)
        if 32 <= value <= 126:
            if self._history_index is not None:
                self._history_index = None
                self._history_draft = ""
            self._buffer += character
            self._write(character)

    def _add_history(self, command):
        if not command or (self._history and self._history[-1] == command):
            return
        self._history.append(command)
        if len(self._history) > self.HISTORY_LIMIT:
            self._history.pop(0)

    def _history_previous(self):
        if not self._history:
            return
        if self._history_index is None:
            self._history_draft = self._buffer
            self._history_index = len(self._history) - 1
        elif self._history_index > 0:
            self._history_index -= 1
        self._buffer = self._history[self._history_index]
        self._redraw_input()

    def _history_next(self):
        if self._history_index is None:
            return
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._buffer = self._history[self._history_index]
        else:
            self._history_index = None
            self._buffer = self._history_draft
            self._history_draft = ""
        self._redraw_input()

    def _redraw_input(self):
        self._write("\r\x1b[2K")
        self._write(self.PROMPT)
        self._write(self._buffer)

    def _command_history(self):
        if not self._history:
            self._write_line("History is empty.")
            return
        self._write_line("Command history:")
        for i, command in enumerate(self._history, 1):
            self._write_line("  {:>2}  {}".format(i, command))

    def _execute_buffer(self):
        command = self._buffer.strip()
        self._buffer = ""
        self._history_index = None
        self._history_draft = ""
        self._write_line("")
        if command:
            self._add_history(command)
            self._execute(command)
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
            "led": lambda: self._command_led(parts),
            "reboot": lambda: self._command_reboot(),
        }
        handler = dispatch.get(name)
        if handler:
            handler()
        else:
            self._write_line("Unknown command: {}".format(name))
            self._write_line("Type 'help' for commands.")

    def _command_help(self):
        lines = [
            "BadgeOS commands", "----------------",
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
            "  led <color>      Set LED ring color",
            "  reboot           Reboot the badge",
            "", "History:",
            "  Up arrow         Previous command",
            "  Down arrow       Next command",
            "", "Examples:", "  mode next", "  mode HIDDemo",
            "  diag ram", "  led magenta",
        ]
        for line in lines:
            self._write_line(line)

    def _show_banner(self):
        for line in (
            "", "========================================",
            "              BadgeOS",
            "         HackNWA Badge Runtime",
            "----------------------------------------",
            "  Version : {}".format(VERSION),
            "  Codename: {}".format(CODENAME),
            "========================================",
        ):
            self._write_line(line)

    def _command_about(self):
        self._show_banner()
        for line in (
            "", "BadgeOS is a modular CircuitPython runtime",
            "for the HackNWA Sock Puppet Tycoon badge.", "",
            "Capabilities:",
            "  - cooperative service scheduler",
            "  - event-driven input",
            "  - runtime mode switching",
            "  - NeoPixel effects",
            "  - USB HID keyboard",
            "  - USB CDC shell",
            "  - system diagnostics",
        ):
            self._write_line(line)

    def _command_clear(self):
        self._write("\x1b[2J\x1b[H")
        self._show_banner()
        self._write_line("")

    def _command_status(self):
        self._write_line("BadgeOS status")
        self._write_line("--------------")
        self._write_line("  version: {}".format(VERSION))
        self._write_line("  codename: {}".format(CODENAME))
        self._write_line("  mode: {}".format(self._current_mode_name()))
        self._write_line("  modes: {}".format(len(self.mode_manager.modes())))
        self._write_line("  uptime: {} seconds".format(int(time.monotonic())))
        self._write_line("  free RAM: {} bytes".format(gc.mem_free()))
        self._write_line("  USB connected: {}".format(supervisor.runtime.usb_connected))
        self._write_line("  shell: running")

    def _command_mem(self):
        self._write_line("Free RAM: {} bytes".format(gc.mem_free()))

    def _command_uptime(self):
        self._write_line("Uptime: {} seconds".format(int(time.monotonic())))

    def _command_usb(self):
        self._write_line("USB connected: {}".format(supervisor.runtime.usb_connected))

    def _command_version(self):
        self._write_line("BadgeOS {} ({})".format(VERSION, CODENAME))

    def _command_diag(self, parts):
        if len(parts) == 1:
            self._write_line("Diagnostics")
            self._write_line("-----------")
            self._write_line("  RAM free: {} bytes".format(gc.mem_free()))
            self._write_line("  uptime: {} seconds".format(int(time.monotonic())))
            self._write_line("  USB connected: {}".format(supervisor.runtime.usb_connected))
            self._write_line("  version: {} ({})".format(VERSION, CODENAME))
            self._write_line("  mode: {}".format(self._current_mode_name()))
            return
        if len(parts) != 2:
            self._write_line("Usage: diag <ram|uptime|usb|version>")
            return
        page = parts[1].lower()
        handlers = {"ram": self._command_mem, "uptime": self._command_uptime,
                    "usb": self._command_usb, "version": self._command_version}
        handler = handlers.get(page)
        if handler:
            handler()
        else:
            self._write_line("Unknown diagnostic page: {}".format(page))
            self._write_line("Valid pages: ram uptime usb version")

    def _command_modes(self):
        modes = self.mode_manager.modes()
        if not modes:
            self._write_line("No modes registered.")
            return
        self._write_line("Available modes:")
        current = self.mode_manager.current_mode
        for mode in modes:
            self._write_line("  {} {}".format("*" if mode is current else " ", mode.name))

    def _command_mode(self, parts):
        if len(parts) == 1:
            self._write_line("Active mode: {}".format(self._current_mode_name()))
            return
        if len(parts) != 2:
            self._write_line("Usage: mode <next|prev|name>")
            return
        requested = parts[1]
        lowered = requested.lower()
        if lowered == "next":
            self._switch_relative_mode(1)
            return
        if lowered in ("prev", "previous"):
            self._switch_relative_mode(-1)
            return
        mode = self.mode_manager.get_mode(requested)
        if mode is None:
            self._write_line("Unknown mode: {}".format(requested))
            self._write_line("Type 'modes' to list modes.")
            return
        if mode is self.mode_manager.current_mode:
            self._write_line("Already active: {}".format(mode.name))
            return
        self.mode_manager.set_mode(mode)
        self._write_line("Switched to mode: {}".format(mode.name))

    def _switch_relative_mode(self, direction):
        modes = list(self.mode_manager.modes())
        if not modes:
            self._write_line("No modes registered.")
            return
        current = self.mode_manager.current_mode
        try:
            index = modes.index(current)
        except ValueError:
            index = 0
        mode = modes[(index + direction) % len(modes)]
        self.mode_manager.set_mode(mode)
        self._write_line("Switched to mode: {}".format(mode.name))

    def _command_led(self, parts):
        if len(parts) != 2:
            self._write_line("Usage: led <color>")
            return
        color = parts[1].lower()
        commands = {
            "red": self.led.red, "green": self.led.green, "blue": self.led.blue,
            "yellow": self.led.yellow, "cyan": self.led.cyan,
            "magenta": self.led.magenta, "purple": self.led.magenta,
            "white": self.led.white, "off": self.led.off,
        }
        if color == "orange":
            self.led.fill((255, 80, 0))
            self._write_line("LED: orange")
            return
        if color not in commands:
            self._write_line("Unknown LED color: {}".format(color))
            self._write_line("Type 'help' to list colors.")
            return
        commands[color]()
        self._write_line("LED: {}".format(color))

    def _command_reboot(self):
        self._write_line("Rebooting BadgeOS...")
        self._write_line("USB connection will disconnect.")
        try:
            self.serial.flush()
        except Exception:
            pass
        time.sleep(0.20)
        microcontroller.reset()

    def _current_mode_name(self):
        mode = self.mode_manager.current_mode
        return "none" if mode is None else mode.name

    def _write(self, text):
        if self.serial is None:
            return
        try:
            self.serial.write(text.encode("utf-8"))
        except Exception:
            pass

    def _write_line(self, text):
        self._write(text + "\r\n")

    def _prompt(self):
        self._write(self.PROMPT)
