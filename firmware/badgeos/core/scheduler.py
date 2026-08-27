"""
BadgeOS Scheduler

Cooperative scheduler for BadgeOS services.
"""

import time

from badgeos.core.service import Service
from badgeos.logger import get_logger


log = get_logger("SCHEDULER")


class Scheduler:
    """
    Cooperative BadgeOS service scheduler.
    """

    def __init__(self, tick_interval=0.01):
        self.tick_interval = tick_interval
        self.services = []
        self.running = False

    def register(self, service):
        """
        Register a Service with the scheduler.
        """

        if not isinstance(service, Service):
            raise TypeError(
                "Registered object must inherit from Service."
            )

        log.info(
            "Registering service: {}".format(
                service.name
            )
        )

        self.services.append(service)

    def initialize(self):
        """
        Initialize all registered services.
        """

        log.info("Initializing services")

        for service in self.services:
            try:
                service.initialize()

                log.info(
                    "{} initialized".format(
                        service.name
                    )
                )

            except Exception as exc:
                service.enabled = False

                log.error(
                    "{} failed to initialize: {}".format(
                        service.name,
                        exc,
                    )
                )

    def run(self):
        """
        Start the cooperative scheduler.
        """

        self.running = True

        self.initialize()

        log.info("Scheduler started")

        try:
            while self.running:
                start = time.monotonic()

                for service in self.services:
                    if not service.enabled:
                        continue

                    try:
                        service.update()

                    except Exception as exc:
                        log.error(
                            "{} update failed: {}".format(
                                service.name,
                                exc,
                            )
                        )

                elapsed = time.monotonic() - start
                remaining = self.tick_interval - elapsed

                if remaining > 0:
                    time.sleep(remaining)

        except KeyboardInterrupt:
            log.info("Scheduler interrupted")

        finally:
            self.shutdown()

    def stop(self):
        """
        Request scheduler shutdown.
        """

        self.running = False

    def shutdown(self):
        """
        Shut down registered services in reverse order.
        """

        log.info("Stopping services")

        for service in reversed(self.services):
            try:
                service.shutdown()

            except Exception as exc:
                log.error(
                    "{} shutdown failed: {}".format(
                        service.name,
                        exc,
                    )
                )

        log.info("Scheduler stopped")
