"""
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
