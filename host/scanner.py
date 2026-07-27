"""
scanner.py

Scans the local firmware directory and produces a list of
files that should be deployed.
"""

from pathlib import Path


class FirmwareScanner:

    def __init__(self, root: Path):
        self.root = root

    def files(self):

        files = []

        for path in sorted(self.root.rglob("*")):

            if path.is_dir():
                continue

            files.append(path)

        return files

    def directories(self):

        directories = []

        for path in sorted(self.root.rglob("*")):

            if path.is_dir():
                directories.append(path)

        return directories
