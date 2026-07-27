"""
manifest.py

Represents a firmware image ready for deployment.
"""

from pathlib import Path

from scanner import FirmwareScanner


class Manifest:

    def __init__(self, firmware_root: Path):

        self.root = firmware_root

        scanner = FirmwareScanner(firmware_root)

        self.files = scanner.files()
        self.directories = scanner.directories()

    def __len__(self):

        return len(self.files)
