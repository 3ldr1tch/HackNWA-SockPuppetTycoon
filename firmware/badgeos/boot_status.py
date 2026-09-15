"""
BadgeOS Boot Status Indicators.

Provides simple visual status patterns for startup success and failure.
"""

import time


def show_boot_success(led):
    """
    Brief visual confirmation that BadgeOS initialized successfully.
    """

    led.fill(
        (
            0,
            255,
            0,
        )
    )

    time.sleep(
        0.12
    )

    led.off()


def show_boot_error(led):
    """
    Display a visible startup failure indication.

    Sequence:
        red flash x3
        leave pixel 0 red
    """

    red = (
        255,
        0,
        0,
    )

    for _ in range(3):
        led.fill(
            red
        )

        time.sleep(
            0.20
        )

        led.off()

        time.sleep(
            0.15
        )

    led.set_pixel(
        0,
        red,
    )
