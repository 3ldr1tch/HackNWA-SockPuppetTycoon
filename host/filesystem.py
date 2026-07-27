"""
filesystem.py

Directory management on the badge.
"""

from repl import REPL


class RemoteFilesystem:

    def __init__(self, repl: REPL):

        self.repl = repl

    def mkdir(self, path: str):

        code = f"""
import os

try:
    os.mkdir("{path}")
except OSError:
    pass
"""

        self.repl.run(code)
