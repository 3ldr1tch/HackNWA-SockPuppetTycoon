#!/usr/bin/env python3
from pathlib import Path
import re
import sys

path = Path("firmware/badgeos/application.py")
text = path.read_text()

# Find the existing set_mode(...) call that queues the initial mode before scheduler startup.
# We deliberately avoid reconstructing application.py so all current registrations/services stay intact.
patterns = [
    r'(self\.mode_manager\.set_mode\(\s*)self\.input_demo(\s*\))',
    r'(self\.mode_manager\.set_mode\(\s*)input_demo(\s*\))',
]

replacement_done = False
for pattern in patterns:
    new_text, count = re.subn(
        pattern,
        r'\1self.showcase_mode\2',
        text,
        count=1,
    )
    if count:
        text = new_text
        replacement_done = True
        break

if not replacement_done:
    print("Could not safely identify the current initial-mode line.")
    print("No changes were made to application.py.")
    print("Show the set_mode / ShowcaseMode portion of application.py before patching it.")
    sys.exit(1)

path.write_text(text)
print("application.py initial mode changed to ShowcaseMode.")
