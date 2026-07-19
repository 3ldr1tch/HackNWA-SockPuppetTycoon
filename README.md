# HackNWA SockPuppetTycoon Badge
### BadgeOS Firmware

![Version](https://img.shields.io/badge/version-0.1.0--dev-blue)
![Platform](https://img.shields.io/badge/platform-RP2350A-green)
![Firmware](https://img.shields.io/badge/CircuitPython-10.x-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Overview

**BadgeOS** is an open-source firmware project for the **HackNWA SockPuppetTycoon conference badge**, built around the Raspberry Pi **RP2350A** microcontroller and CircuitPython.

The goal is to transform the badge from a conference giveaway into a portable embedded systems toolkit suitable for hardware development, diagnostics, education, and authorized security research.

BadgeOS is designed around a modular architecture so new tools can be added without modifying the core operating environment.

---

## Project Goals

- Modular firmware architecture
- Interactive serial shell
- LED-driven user interface
- Hardware auto-discovery
- GPIO exploration tools
- I²C utilities
- SPI utilities
- UART bridge
- USB diagnostics
- Plugin framework
- Flipper Zero companion mode
- Optional expansion module support

---

## Current Status

**Version:** 0.1.0-dev

This repository is under active development.

Current milestone:

- Repository bootstrap
- Hardware discovery framework
- Hardware abstraction layer (HAL)

---

# Hardware

Current target hardware:

| Component | Description |
|------------|-------------|
| MCU | Raspberry Pi RP2350A |
| Flash | 8 MB SPI Flash |
| USB | USB-C |
| LEDs | 12x NeoPixels |
| Buttons | 2 User Buttons |
| Debug | SWD |
| Firmware | CircuitPython 10.x |

---

# Planned Features

## Hardware Discovery

Automatic detection of:

- GPIO
- Buttons
- NeoPixel ring
- I²C buses
- SPI buses
- UART buses
- ADC inputs
- PWM outputs
- Optional expansion hardware

---

## Diagnostics

System information including:

- Firmware version
- CPU frequency
- Temperature
- Flash usage
- RAM usage
- USB state
- Hardware profile

---

## GPIO Explorer

Interactive GPIO control.

Examples:

```text
gpio list

gpio read GP20

gpio write GP20 high

gpio pwm GP18 1000
```

---

## I²C Tools

- Bus scanner
- Address identification
- Register read/write
- Device information

---

## SPI Tools

- Flash identification
- EEPROM access
- Sensor support
- Display support

---

## UART Tools

- Serial monitor
- Bridge mode
- Configurable baud rates
- Logging

---

## USB Tools

- Device information
- HID status
- Serial diagnostics
- USB descriptor information

---

## Plugin System

BadgeOS is designed around plugins.

Future plugins may include:

- OLED Display
- GPS
- LoRa
- CC1101
- nRF24L01+
- MCP23017
- BME280
- CAN Bus
- Logic Analyzer
- Frequency Counter
- IR Decoder
- PIO Tools

---

# Repository Layout

```
HackNWA_SockPuppetTycoon_Badge/

├── README.md
├── LICENSE
├── .gitignore
│
├── badgeos/
│   ├── boot.py
│   ├── code.py
│   ├── config.py
│   ├── hardware_probe.py
│   │
│   ├── core/
│   ├── tools/
│   ├── plugins/
│   ├── profiles/
│   └── lib/
│
├── docs/
│
├── hardware/
│
├── examples/
│
└── tools/
```

---

# Roadmap

## Milestone 0

- Repository setup
- Documentation
- Hardware discovery utility

---

## Milestone 1

- Hardware abstraction layer
- Button driver
- LED driver
- Configuration generation

---

## Milestone 2

- Interactive shell
- Diagnostics
- GPIO explorer

---

## Milestone 3

- I²C utilities
- SPI utilities
- UART monitor

---

## Milestone 4

- Plugin framework
- USB toolkit
- Flipper Zero companion

---

## Milestone 5

- PIO toolkit
- Logic analyzer
- Signal generator
- Protocol decoder

---

# Development Philosophy

BadgeOS is intended to be:

- Open source
- Well documented
- Modular
- Beginner friendly
- Easy to extend
- Hardware safe by default

Whenever possible, GPIOs remain configured as inputs until explicitly enabled by the user.

---

# Requirements

Hardware:

- HackNWA SockPuppetTycoon Badge
- USB-C data cable

Software:

- CircuitPython 10.x
- Python 3.11+ (optional for host tools)
- Git

Recommended tools:

- VS Code
- CircUp
- Mu Editor
- mpremote
- rshell

---

# Installation

1. Install CircuitPython 10.x on the badge.
2. Clone this repository.

```bash
git clone https://github.com/<YOUR_USERNAME>/HackNWA_SockPuppetTycoon_Badge.git
```

3. Copy the contents of the `badgeos/` directory to the `CIRCUITPY` drive.
4. Open the serial console.
5. Run the hardware discovery utility.
6. Follow the on-screen prompts.

---

# Contributing

Contributions are welcome.

Please:

- Open an issue before major changes.
- Keep commits focused.
- Document new modules.
- Follow existing coding conventions.

---

# License

This project is licensed under the MIT License.

See the LICENSE file for details.

---

# Acknowledgements

Special thanks to:

- HackNWA
- Horizon3.ai
- Raspberry Pi Foundation
- Adafruit
- CircuitPython contributors
- The open-source hardware community

---

# Disclaimer

This project is intended for education, hardware development, diagnostics, and authorized security research.

Users are responsible for complying with all applicable laws, regulations, and policies when using this software.

---

## Version

Current Version:

**0.1.0-dev**

Project codename:

**BadgeOS**
