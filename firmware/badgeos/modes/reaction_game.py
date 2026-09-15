"""
BadgeOS Reaction Game Mode.

A simple reaction-time game using the NeoPixel ring and one button.

Gameplay:
    - enter mode
    - red/yellow/green countdown
    - wait for the green target
    - short press as quickly as possible
    - reaction time is measured and displayed as a score bar

A premature press is treated as a false start.

Long-press mode switching is handled globally by ModeSwitchService.
"""

import time

from badgeos.core import Mode
from badgeos.logger import get_logger


class ReactionGameMode(Mode):
    """Single-button reaction-time game."""

    STATE_COUNTDOWN = 0
    STATE_WAITING = 1
    STATE_TARGET = 2
    STATE_RESULT = 3
    STATE_FALSE_START = 4

    COUNTDOWN_STEP_SECONDS = 0.55

    RESULT_SECONDS = 2.5
    FALSE_START_SECONDS = 1.5

    RED = (
        255,
        0,
        0,
    )

    YELLOW = (
        255,
        180,
        0,
    )

    GREEN = (
        0,
        255,
        0,
    )

    BLUE = (
        0,
        80,
        255,
    )

    OFF = (
        0,
        0,
        0,
    )

    def __init__(
        self,
        events,
        led,
    ):
        super().__init__(
            "ReactionGame"
        )

        self.events = events
        self.led = led

        self.log = get_logger(
            self.name
        )

        self.state = (
            self.STATE_COUNTDOWN
        )

        self._state_started = 0.0

        self._countdown_step = 0

        self._wait_seconds = 1.0

        self._target_started = 0.0

        self._reaction_ms = None

        self._round = 0

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def start(self):
        super().start()

        self.events.subscribe(
            "button.short_press",
            self._on_short_press,
        )

        self._round = 0

        self.log.info(
            "Reaction game started"
        )

        self.log.info(
            "Wait for green, then press!"
        )

        self._start_round()

    def stop(self):
        self.events.unsubscribe(
            "button.short_press",
            self._on_short_press,
        )

        self.led.off()

        self.log.info(
            "Reaction game stopped"
        )

        super().stop()

    # ---------------------------------------------------------
    # Round management
    # ---------------------------------------------------------

    def _start_round(self):
        self._round += 1

        self.state = (
            self.STATE_COUNTDOWN
        )

        self._state_started = (
            time.monotonic()
        )

        self._countdown_step = 0

        self._reaction_ms = None

        self.led.off()

        self.log.info(
            "Round {} starting".format(
                self._round
            )
        )

        self._render_countdown()

    def _begin_wait(self):
        self.state = (
            self.STATE_WAITING
        )

        self._state_started = (
            time.monotonic()
        )

        #
        # Generate a varying delay without depending on the
        # random module.
        #
        # Range:
        #     about 1.0 to 3.0 seconds
        #
        now_ms = int(
            time.monotonic()
            * 1000
        )

        variation = (
            now_ms % 2000
        ) / 1000.0

        self._wait_seconds = (
            1.0 + variation
        )

        self.led.off()

        self.log.info(
            "Waiting..."
        )

    def _show_target(self):
        self.state = (
            self.STATE_TARGET
        )

        self._state_started = (
            time.monotonic()
        )

        self._target_started = (
            self._state_started
        )

        self.led.fill(
            self.GREEN
        )

        self.log.info(
            "GO!"
        )

    # ---------------------------------------------------------
    # Update loop
    # ---------------------------------------------------------

    def update(self):
        if not self.active:
            return

        now = time.monotonic()

        elapsed = (
            now
            - self._state_started
        )

        if self.state == self.STATE_COUNTDOWN:
            self._update_countdown(
                elapsed
            )

        elif self.state == self.STATE_WAITING:
            if elapsed >= self._wait_seconds:
                self._show_target()

        elif self.state == self.STATE_RESULT:
            if elapsed >= self.RESULT_SECONDS:
                self._start_round()

        elif (
            self.state
            == self.STATE_FALSE_START
        ):
            if (
                elapsed
                >= self.FALSE_START_SECONDS
            ):
                self._start_round()

    # ---------------------------------------------------------
    # Countdown
    # ---------------------------------------------------------

    def _update_countdown(
        self,
        elapsed,
    ):
        expected_step = int(
            elapsed
            / self.COUNTDOWN_STEP_SECONDS
        )

        if expected_step > 2:
            self._begin_wait()
            return

        if (
            expected_step
            != self._countdown_step
        ):
            self._countdown_step = (
                expected_step
            )

            self._render_countdown()

    def _render_countdown(self):
        self.led.off()

        if self._countdown_step == 0:
            color = self.RED
            count = 4

        elif self._countdown_step == 1:
            color = self.YELLOW
            count = 8

        else:
            color = self.BLUE
            count = self.led.pixel_count

        for index in range(
            count
        ):
            if (
                index
                >= self.led.pixel_count
            ):
                break

            self.led.set_pixel(
                index,
                color,
            )

    # ---------------------------------------------------------
    # Button input
    # ---------------------------------------------------------

    def _on_short_press(
        self,
        event_name,
        data,
    ):
        if not self.active:
            return

        if self.state == self.STATE_TARGET:
            self._register_hit()

            return

        if (
            self.state
            == self.STATE_COUNTDOWN
            or self.state
            == self.STATE_WAITING
        ):
            self._false_start()

    # ---------------------------------------------------------
    # Results
    # ---------------------------------------------------------

    def _register_hit(self):
        now = time.monotonic()

        reaction_seconds = (
            now
            - self._target_started
        )

        self._reaction_ms = int(
            reaction_seconds
            * 1000
        )

        self.state = (
            self.STATE_RESULT
        )

        self._state_started = now

        self.log.info(
            "Reaction: {} ms".format(
                self._reaction_ms
            )
        )

        self._render_score(
            self._reaction_ms
        )

    def _false_start(self):
        self.state = (
            self.STATE_FALSE_START
        )

        self._state_started = (
            time.monotonic()
        )

        self.led.red()

        self.log.info(
            "FALSE START"
        )

    # ---------------------------------------------------------
    # Score visualization
    # ---------------------------------------------------------

    def _render_score(
        self,
        reaction_ms,
    ):
        self.led.off()

        #
        # Convert reaction time into 1-12 green LEDs.
        #
        # Faster reaction = more LEDs.
        #
        # <= 150 ms  -> 12
        # >= 1000 ms -> 1
        #

        minimum = 150
        maximum = 1000

        if reaction_ms <= minimum:
            score = (
                self.led.pixel_count
            )

        elif reaction_ms >= maximum:
            score = 1

        else:
            span = (
                maximum
                - minimum
            )

            value = (
                maximum
                - reaction_ms
            )

            score = (
                1
                + (
                    value
                    * (
                        self.led.pixel_count
                        - 1
                    )
                    // span
                )
            )

        for index in range(
            score
        ):
            self.led.set_pixel(
                index,
                self.GREEN,
            )

        self.log.info(
            "Score: {}/{}".format(
                score,
                self.led.pixel_count,
            )
        )
