"""
BadgeOS Startup Animation.

Provides a short visual boot sequence before the normal BadgeOS
services and interactive modes begin.
"""

import time


def run_startup_animation(led):
    """
    Play the BadgeOS startup animation.

    Sequence:
        cyan chase clockwise
        magenta chase counter-clockwise
        white flash
        LEDs off
    """

    cyan = (
        0,
        180,
        255,
    )

    magenta = (
        255,
        0,
        180,
    )

    white = (
        255,
        255,
        255,
    )

    # ---------------------------------------------------------
    # Cyan chase
    # ---------------------------------------------------------

    for index in range(
        led.pixel_count
    ):
        led.off()

        led.set_pixel(
            index,
            cyan,
        )

        time.sleep(
            0.035
        )

    # ---------------------------------------------------------
    # Magenta reverse chase
    # ---------------------------------------------------------

    for index in range(
        led.pixel_count - 1,
        -1,
        -1,
    ):
        led.off()

        led.set_pixel(
            index,
            magenta,
        )

        time.sleep(
            0.035
        )

    # ---------------------------------------------------------
    # Boot confirmation flashes
    # ---------------------------------------------------------

    led.fill(
        magenta
    )

    time.sleep(
        0.10
    )

    led.fill(
        cyan
    )

    time.sleep(
        0.10
    )

    led.fill(
        white
    )

    time.sleep(
        0.12
    )

    led.off()

    time.sleep(
        0.10
    )
