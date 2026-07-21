"""
BadgeOS Scheduler

A cooperative scheduler for BadgeOS.

The scheduler manages a collection of services. Each service is
initialized once, updated every scheduler tick, and optionally
shut down when the scheduler exits.

Designed for CircuitPython.

Version:
    0.1.0-dev
"""

import time

from badgeos.logger import get_logger

from badgeos.core.service import Service

log = get_logger("SCHEDULER")


class Scheduler:
    """
    Cooperative task scheduler.
    """

    def __init__(self, tick_interval=0.01):
        """
        Parameters
        ----------
        tick_interval : float
            Delay between scheduler iterations in seconds.
        """
        self.tick_interval = tick_interval
        self.services = []
        self.running = False

    # ---------------------------------------------------------
    # Service Management
    # ---------------------------------------------------------

    def register(self, service):
    """
    Register a Service instance with the scheduler.
    """

    if not isinstance(service, Service):
        raise TypeError(
            "Registered object must inherit from Service."
        )

    log.info(f"Registering service: {service.name}")

    self.services.append(service)

    # ---------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------

    def initialize(self):
        """
        Initialize all registered services.
        """

        log.info("Initializing services")

        for service in self.services:

            try:

                service.initialize()

                log.info(f"{service.name} initialized")

            except Exception as exc:

                log.error(
                    f"{service.name} failed to initialize: {exc}"
                )

    # ---------------------------------------------------------
    # Main Loop
    # ---------------------------------------------------------

    def run(self):
        """
        Start the scheduler.
        """

        self.running = True

        self.initialize()

        log.info("Scheduler started")

        while self.running:

            start = time.monotonic()

            for service in self.services:

                if not getattr(service, "enabled", True):
                    continue

                try:

                    service.update()

                except Exception as exc:

                    log.error(
                        f"{service.name}: {exc}"
                    )

            elapsed = time.monotonic() - start

            remaining = self.tick_interval - elapsed

            if remaining > 0:
                time.sleep(remaining)

        self.shutdown()

    # ---------------------------------------------------------
    # Shutdown
    # ---------------------------------------------------------

    def stop(self):
        """
        Request scheduler shutdown.
        """

        self.running = False

    def shutdown(self):
        """
        Shut down all services.
        """

        log.info("Stopping services")

        for service in reversed(self.services):

            try:

                service.shutdown()

            except Exception as exc:

                log.error(
                    f"{service.name}: {exc}"
                )

        log.info("Scheduler stopped")
