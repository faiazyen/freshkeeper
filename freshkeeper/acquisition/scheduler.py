"""Background scheduler for measurement cycles.

Runs the acquisition loop on its own thread so it cannot block Flask request
handling. The default cadence is thirty minutes, which is the interval the
power budget and the MQ heater duty cycle were designed around.

``max_instances=1`` and ``coalesce=True`` matter more than they look. A cycle
that overruns its slot must not have a second copy started on top of it: two
threads reading the same load cell at once produce readings that belong to
neither, and on a real Pi the gas heaters would be commanded on and off
simultaneously.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_MINUTES = 30


class AcquisitionScheduler:
    def __init__(self, inference_service, interval_minutes: int = DEFAULT_INTERVAL_MINUTES):
        self.service = inference_service
        self.interval_minutes = interval_minutes
        self._scheduler = BackgroundScheduler(daemon=True)

    def _tick(self) -> None:
        try:
            result = self.service.run_cycle()
            logger.info("cycle complete: %d slots, %d items",
                        result["slots"], len(result["items"]))
        except Exception:
            # A failed cycle must not kill the scheduler thread. A sensor that
            # throws once every few days is normal; a monitoring system that
            # silently stops monitoring is not.
            logger.exception("measurement cycle failed; will retry next interval")

    def start(self) -> None:
        self._scheduler.add_job(
            self._tick, "interval", minutes=self.interval_minutes,
            id="measurement_cycle", max_instances=1, coalesce=True,
            next_run_time=None,
        )
        self._scheduler.start()
        logger.info("acquisition scheduler started (%d minute interval)",
                    self.interval_minutes)

    def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def run_once(self) -> dict:
        """Trigger a cycle immediately, for testing and the /api/cycle route."""
        return self.service.run_cycle()
