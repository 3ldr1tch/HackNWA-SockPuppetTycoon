#!/usr/bin/env python3
"""
BadgeOS Deployment Tool

Uploads the contents of the firmware directory to a mounted
CircuitPython CIRCUITPY drive.

Version: 0.1.0-dev
"""

from pathlib import Path
import shutil
import sys


class Manifest:
    def __init__(self):
        self.directories = []
        self.files = []


def build_manifest(source):
    """
    Scan the firmware directory and build a deployment manifest.
    """

    manifest = Manifest()

    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)

        if path.is_dir():
            manifest.directories.append(relative)

        elif path.is_file():
            manifest.files.append(relative)

    return manifest


def validate_target(target):
    """
    Ensure the deployment target exists.
    """

    if not target.exists():
        raise RuntimeError(f"Target does not exist: {target}")

    if not target.is_dir():
        raise RuntimeError(f"Target is not a directory: {target}")


def create_directories(target, manifest):
    """
    Create any missing directories.
    """

    for directory in manifest.directories:
        (target / directory).mkdir(parents=True, exist_ok=True)


def copy_files(source, target, manifest):
    """
    Copy every file in the manifest.
    """

    for filename in manifest.files:
        shutil.copy2(
            source / filename,
            target / filename
        )
        print(f"Copied {filename}")


def verify_files(source, target, manifest):
    """
    Verify every copied file exists and matches size.
    """

    for filename in manifest.files:

        src = source / filename
        dst = target / filename

        if not dst.exists():
            raise RuntimeError(f"Missing file: {filename}")

        if src.stat().st_size != dst.stat().st_size:
            raise RuntimeError(f"Verification failed: {filename}")


def deploy(source, target):

    manifest = build_manifest(source)

    validate_target(target)

    create_directories(target, manifest)

    copy_files(source, target, manifest)

    verify_files(source, target, manifest)

    print("\nDeployment successful.")


def main():

    if len(sys.argv) != 3:
        print("Usage:")
        print("  uploader.py <firmware_dir> <target_dir>")
        sys.exit(1)

    source = Path(sys.argv[1]).resolve()
    target = Path(sys.argv[2]).resolve()

    deploy(source, target)


if __name__ == "__main__":
    main()"""
BadgeOS Deployment Tools

uploader.py

Uploads files to the badge over Raw REPL.
"""

from pathlib import Path

from repl import REPL


class Uploader:

    def __init__(self, repl: REPL):

        self.repl = repl

    def upload_text_file(
        self,
        source: Path,
        destination: str,
    ):

        text = source.read_text(
            encoding="utf-8"
        )

        escaped = repr(text)

        program = f"""
with open("{destination}", "w") as f:
    f.write({escaped})
"""

        self.repl.run(program)

    def mkdir(self, path: str):

        program = f"""
import os

try:
    os.mkdir("{path}")
except OSError:
    pass
"""

        self.repl.run(program)
