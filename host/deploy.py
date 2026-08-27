#!/usr/bin/env python3
"""
BadgeOS Deployment Tool

Deploy the local firmware tree to the HackNWA SockPuppetTycoon badge
over CircuitPython Raw REPL.

Features
--------
- Prefers the persistent CircuitPython CDC console interface.
- Detects another process holding the serial port on Linux.
- Recursively deploys the complete firmware directory.
- Creates remote directories automatically.
- Uploads code.py last.
- Skips boot.py unless explicitly requested.
- Verifies every uploaded file by remote file size.
- Attempts to leave Raw REPL cleanly after failures.
- Soft-reboots the badge after successful deployment.

Examples
--------

    python host/deploy.py

    python host/deploy.py --port /dev/ttyACM0

    python host/deploy.py --include-boot

    python host/deploy.py --no-reboot
"""

from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from serial.tools import list_ports

from repl import REPL
from serial_connection import SerialConnection


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIRMWARE_ROOT = PROJECT_ROOT / "firmware"

IGNORE_NAMES = {
    "__pycache__",
    ".DS_Store",
    "Thumbs.db",
}

IGNORE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".bak",
    ".swp",
    ".swo",
    ".tmp",
}

SIZE_MARKER = "__BADGEOS_FILE_SIZE__"


# ---------------------------------------------------------------------------
# Console output
# ---------------------------------------------------------------------------


def heading(text: str):
    print()
    print(text)
    print("=" * 60)


def format_size(size: int) -> str:
    if size < 1024:
        return "{} B".format(size)

    if size < 1024 * 1024:
        return "{:.1f} KiB".format(size / 1024)

    return "{:.2f} MiB".format(size / (1024 * 1024))


# ---------------------------------------------------------------------------
# Serial-port discovery
# ---------------------------------------------------------------------------


def discover_console_port() -> str:
    """
    Locate the CircuitPython console CDC interface.

    The HackNWA badge exposes two CDC ports:

        if00 = CircuitPython console / REPL
        if02 = secondary CDC data interface

    Prefer the persistent by-id if00 path whenever possible.
    """

    by_id_patterns = (
        "/dev/serial/by-id/*Pico*if00",
        "/dev/serial/by-id/*CircuitPython*if00",
        "/dev/serial/by-id/*RP2350*if00",
    )

    for pattern in by_id_patterns:
        matches = sorted(glob.glob(pattern))

        if matches:
            return matches[0]

    # Fall back to pyserial's USB device information.
    candidates = []

    for port in list_ports.comports():
        description = port.description or ""

        if "CircuitPython CDC control" in description:
            candidates.append(port.device)

    if candidates:
        return sorted(candidates)[0]

    # Final fallback to our existing SerialConnection discovery.
    return SerialConnection.discover()


# ---------------------------------------------------------------------------
# Busy-port detection
# ---------------------------------------------------------------------------


def resolve_device_path(port: str) -> str:
    """
    Resolve /dev/serial/by-id symlinks to the actual tty device.
    """

    try:
        return str(Path(port).resolve())
    except Exception:
        return port


def port_owners(port: str) -> list[int]:
    """
    Return PIDs currently holding the serial device.

    This check is Linux-specific. If lsof is unavailable, silently skip it.
    """

    if os.name != "posix":
        return []

    lsof = shutil.which("lsof")

    if lsof is None:
        return []

    device = resolve_device_path(port)

    result = subprocess.run(
        [lsof, "-t", device],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )

    owners = []

    for line in result.stdout.splitlines():
        line = line.strip()

        if line.isdigit():
            owners.append(int(line))

    return owners


def describe_process(pid: int) -> str:
    """
    Produce a short process description for an owning PID.
    """

    ps = shutil.which("ps")

    if ps is None:
        return "PID {}".format(pid)

    result = subprocess.run(
        [ps, "-p", str(pid), "-o", "comm="],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )

    command = result.stdout.strip()

    if not command:
        return "PID {}".format(pid)

    return "{} (PID {})".format(command, pid)


def ensure_port_available(port: str):
    """
    Refuse deployment if another process already owns the console.
    """

    owners = port_owners(port)

    # Ignore ourselves in the unlikely event lsof reports this process.
    owners = [
        pid
        for pid in owners
        if pid != os.getpid()
    ]

    if not owners:
        return

    print()
    print("ERROR: Badge serial console is currently in use.")
    print()

    for pid in owners:
        print("  {}".format(describe_process(pid)))

    print()
    print("Close picocom/screen/serial monitors or kill the process, then retry.")
    print()
    print("Example:")
    print()
    print("  lsof {}".format(resolve_device_path(port)))
    print("  kill <PID>")
    print()

    raise SystemExit(2)


# ---------------------------------------------------------------------------
# Firmware discovery
# ---------------------------------------------------------------------------


def should_ignore(path: Path) -> bool:
    if path.name in IGNORE_NAMES:
        return True

    if path.suffix in IGNORE_SUFFIXES:
        return True

    for part in path.parts:
        if part in IGNORE_NAMES:
            return True

    return False


def discover_firmware_files(include_boot: bool) -> list[Path]:
    """
    Build the ordered deployment list.

    Normal modules are uploaded first.
    code.py is uploaded last so the new entry point is installed only after
    its dependencies exist.

    boot.py is excluded unless --include-boot is supplied.
    """

    files = []

    for path in FIRMWARE_ROOT.rglob("*"):
        if not path.is_file():
            continue

        if should_ignore(path):
            continue

        relative = path.relative_to(FIRMWARE_ROOT)

        if relative == Path("boot.py") and not include_boot:
            continue

        files.append(path)

    def deployment_order(path: Path):
        relative = path.relative_to(FIRMWARE_ROOT)

        # Application entry point comes after everything it imports.
        if relative == Path("code.py"):
            return (2, relative.as_posix())

        # boot.py is intentionally last when explicitly requested.
        if relative == Path("boot.py"):
            return (3, relative.as_posix())

        return (1, relative.as_posix())

    return sorted(files, key=deployment_order)


def remote_path(local_path: Path) -> str:
    relative = local_path.relative_to(FIRMWARE_ROOT)

    return "/" + relative.as_posix()


# ---------------------------------------------------------------------------
# Remote filesystem helpers
# ---------------------------------------------------------------------------


def ensure_remote_parent(repl: REPL, destination: str):
    """
    Create all parent directories required by destination.
    """

    parts = destination.strip("/").split("/")[:-1]

    if not parts:
        return

    current = ""

    for part in parts:
        current += "/" + part
        repl.mkdir(current)


def remote_file_size(repl: REPL, destination: str) -> int:
    """
    Query the uploaded file size using CircuitPython's os.stat().
    """

    code = (
        "import os\n"
        "print('{marker}{{}}'.format(os.stat({path!r})[6]))"
    ).format(
        marker=SIZE_MARKER,
        path=destination,
    )

    output = repl.run(
        code,
        timeout=10.0,
    )

    match = re.search(
        re.escape(SIZE_MARKER) + r"(\d+)",
        output,
    )

    if match is None:
        raise RuntimeError(
            "Unable to determine remote size for {}.\n"
            "Raw REPL response:\n{}".format(
                destination,
                output,
            )
        )

    return int(match.group(1))


# ---------------------------------------------------------------------------
# Deployment
# ---------------------------------------------------------------------------


def upload_and_verify(
    repl: REPL,
    source: Path,
) -> tuple[int, int]:
    """
    Upload one file and verify its remote size.

    Returns
    -------
    tuple
        (local_size, remote_size)
    """

    destination = remote_path(source)

    ensure_remote_parent(
        repl,
        destination,
    )

    local_size = source.stat().st_size

    repl.upload(
        source,
        destination,
    )

    remote_size = remote_file_size(
        repl,
        destination,
    )

    if remote_size != local_size:
        raise RuntimeError(
            "Verification failed for {}: "
            "local={} bytes, remote={} bytes".format(
                destination,
                local_size,
                remote_size,
            )
        )

    return local_size, remote_size


# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Deploy BadgeOS firmware over the CircuitPython Raw REPL."
        )
    )

    parser.add_argument(
        "--port",
        help=(
            "Serial console device. If omitted, the CircuitPython "
            "CDC control interface is detected automatically."
        ),
    )

    parser.add_argument(
        "--include-boot",
        action="store_true",
        help=(
            "Upload boot.py as well. Disabled by default because boot.py "
            "controls USB configuration."
        ),
    )

    parser.add_argument(
        "--no-reboot",
        action="store_true",
        help="Leave the badge at the REPL instead of soft rebooting.",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    args = parse_args()

    if not FIRMWARE_ROOT.is_dir():
        raise SystemExit(
            "Firmware directory does not exist: {}".format(
                FIRMWARE_ROOT
            )
        )

    files = discover_firmware_files(
        include_boot=args.include_boot
    )

    if not files:
        raise SystemExit("No firmware files found.")

    total_bytes = sum(
        path.stat().st_size
        for path in files
    )

    port = args.port or discover_console_port()

    heading("BadgeOS Deployment")

    print("Project  : {}".format(PROJECT_ROOT))
    print("Firmware : {}".format(FIRMWARE_ROOT))
    print("Console  : {}".format(port))
    print("Files    : {}".format(len(files)))
    print("Payload  : {}".format(format_size(total_bytes)))
    print(
        "boot.py  : {}".format(
            "included"
            if args.include_boot
            else "skipped"
        )
    )

    ensure_port_available(port)

    heading("Connecting")

    print("Opening {}".format(port))

    deployment_started = time.monotonic()

    uploaded_files = 0
    uploaded_bytes = 0
    entered_raw = False

    try:
        with SerialConnection(port=port) as connection:
            repl = REPL(connection)

            print("Interrupting running firmware...")
            repl.interrupt()

            print("Entering Raw REPL...")
            repl.enter_raw()
            entered_raw = True

            heading("Uploading")

            for index, source in enumerate(files, start=1):
                destination = remote_path(source)
                local_size = source.stat().st_size

                print(
                    "[{}/{}] {:<46} {:>9}".format(
                        index,
                        len(files),
                        destination,
                        format_size(local_size),
                    )
                )

                _, verified_size = upload_and_verify(
                    repl,
                    source,
                )

                uploaded_files += 1
                uploaded_bytes += verified_size

                print("         verified")

            heading("Finalizing")

            print(
                "Verified {} files.".format(
                    uploaded_files
                )
            )

            print("Leaving Raw REPL...")
            repl.exit_raw()
            entered_raw = False

            if args.no_reboot:
                print("Soft reboot skipped.")
            else:
                print("Soft rebooting badge...")

                # The badge may re-enumerate its USB interfaces immediately
                # after this byte is sent. We deliberately do not wait for a
                # response.
                repl.soft_reset()

    except KeyboardInterrupt:
        print()
        print("Deployment interrupted by user.")

        raise SystemExit(130)

    except Exception as exc:
        print()
        print("=" * 60)
        print("DEPLOYMENT FAILED")
        print("=" * 60)
        print()
        print("{}: {}".format(
            type(exc).__name__,
            exc,
        ))
        print()

        if entered_raw:
            print(
                "The badge may still be in Raw REPL mode. "
                "Reconnect to the console if necessary."
            )

        raise SystemExit(1)

    elapsed = time.monotonic() - deployment_started

    heading("Deployment Complete")

    print("Files    : {} verified".format(uploaded_files))
    print("Bytes    : {}".format(format_size(uploaded_bytes)))
    print("Elapsed  : {:.2f} seconds".format(elapsed))

    if args.no_reboot:
        print("Badge    : left at REPL")
    else:
        print("Badge    : reboot requested")

    print()


if __name__ == "__main__":
    main()
