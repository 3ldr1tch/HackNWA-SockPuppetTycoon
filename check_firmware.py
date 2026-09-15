#!/usr/bin/env python3
"""Compile every BadgeOS firmware Python source before deployment."""

from pathlib import Path
import py_compile
import sys

root = Path("firmware")
files = sorted(root.rglob("*.py"))

failures = []

print("BadgeOS firmware syntax check")
print("=" * 60)

for path in files:
    try:
        py_compile.compile(
            str(path),
            doraise=True,
        )
        print("PASS  {}".format(path))
    except py_compile.PyCompileError as exc:
        failures.append((path, exc))
        print("FAIL  {}".format(path))
        print("      {}".format(exc.msg))

print("=" * 60)

if failures:
    print("{} file(s) failed syntax validation.".format(len(failures)))
    sys.exit(1)

print("{} file(s) passed.".format(len(files)))
