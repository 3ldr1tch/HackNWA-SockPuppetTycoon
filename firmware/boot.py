"""
BadgeOS boot.py

Minimal boot configuration for development.
"""

import supervisor

# Keep auto reload enabled while developing.
supervisor.runtime.autoreload = True

print("BadgeOS boot")
