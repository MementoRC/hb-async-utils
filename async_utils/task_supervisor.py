"""
A supervisor for long-running periodic async checks (health polling, liveness
probes, etc).

Several consumers hand-roll the same shape of boilerplate: create a background
``asyncio.Task`` that wakes up on an interval, runs a check, counts consecutive
failures, and triggers a recovery action (e.g. a restart) once a failure
threshold is reached — with idempotent start/stop and clean cancellation.
``TaskSupervisor`` factors that shape out into a single reusable primitive.
"""

import asyncio
import contextlib
import inspect
import logging
from collections.abc import Awaitable, Callable

from async_utils.hb_compat import get_logger

_LOGGER = get_logger("task_supervisor")

# A health/liveness check. Should return ``True`` when healthy, ``False`` when
# not. Raising an exception is also treated as a failed check (the exception
# is logged and swallowed) so callers do not need their own try/except.
CheckFunc = Callable[[], Awaitable[bool]]

# Invoked once ``failure_threshold`` consecutive failures have been observed.
# May be a plain callable or an async callable; both are supported.
ThresholdCallback = Callable[[], "Awaitable[None] | None"]


class TaskSupervisor:
    """
    Runs ``check`` on a fixed ``interval`` inside a background task, tracking
    consecutive failures and invoking ``on_threshold_reached`` once
    ``failure_threshold`` consecutive failures have been observed.

    Lifecycle is managed with :meth:`start` / :meth:`stop`, both of which are
    idempotent. ``stop`` cancels the background task and waits for it to
    finish, suppressing the resulting ``CancelledError``, mirroring the
    pattern used for other supervised background tasks throughout the
    Hummingbot sub-packages.

    :param check: zero-arg async callable returning ``True`` when healthy.
        Exceptions raised by ``check`` are treated as a failed check.
    :param interval: seconds to sleep between checks.
    :param failure_threshold: number of *consecutive* failed checks required
        before ``on_threshold_reached`` fires. The counter resets to zero
        both on a successful check and immediately after the callback fires.
    :param on_threshold_reached: optional callable (sync or async) invoked
        when ``failure_threshold`` is reached. If omitted, the supervisor
        only tracks/logs failures without taking any recovery action.
    :param logger: logger to use; defaults to a module-level logger.
    :param name: name assigned to the background ``asyncio.Task``, useful for
        debugging (e.g. ``asyncio.all_tasks()``).
    """

    def __init__(
        self,
        check: CheckFunc,
        *,
        interval: float,
        failure_threshold: int = 1,
        on_threshold_reached: ThresholdCallback | None = None,
        logger: logging.Logger | None = None,
        name: str = "task-supervisor",
    ) -> None:
        if interval <= 0:
            raise ValueError("interval must be > 0")
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")

        self._check = check
        self._interval = interval
        self._failure_threshold = failure_threshold
        self._on_threshold_reached = on_threshold_reached
        self._logger = logger or _LOGGER
        self._name = name

        self._task: asyncio.Task[None] | None = None
        self._running: bool = False
        self._consecutive_failures: int = 0

    @property
    def is_running(self) -> bool:
        """Whether the supervisor's background task is currently active."""
        return self._running

    @property
    def consecutive_failures(self) -> int:
        """Current count of consecutive failed checks (resets on success)."""
        return self._consecutive_failures

    def start(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        """
        Start the background supervision task. Idempotent: calling ``start``
        while already running is a no-op.

        :param loop: event loop to schedule the task on; defaults to the
            currently running loop.
        """
        if self._running:
            return
        loop = loop if loop is not None else asyncio.get_event_loop()
        self._consecutive_failures = 0
        self._task = loop.create_task(self._run(), name=self._name)
        self._running = True

    async def stop(self) -> None:
        """
        Stop the background supervision task. Idempotent: calling ``stop``
        while not running is a no-op. Never raises.
        """
        if not self._running:
            return
        if self._task is not None and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self._task = None
        self._running = False

    async def _run(self) -> None:
        try:
            while True:
                await asyncio.sleep(self._interval)
                healthy = await self._run_check()
                if healthy:
                    self._consecutive_failures = 0
                    continue

                self._consecutive_failures += 1
                self._logger.warning(
                    "%s: consecutive check failures: %d/%d",
                    self._name,
                    self._consecutive_failures,
                    self._failure_threshold,
                )
                if self._consecutive_failures >= self._failure_threshold:
                    self._consecutive_failures = 0
                    await self._fire_threshold_callback()
        except asyncio.CancelledError:
            pass

    async def _run_check(self) -> bool:
        try:
            return bool(await self._check())
        except asyncio.CancelledError:
            raise
        except Exception:
            self._logger.debug("%s: check raised, treating as failure", self._name, exc_info=True)
            return False

    async def _fire_threshold_callback(self) -> None:
        if self._on_threshold_reached is None:
            return
        self._logger.error("%s: failure threshold reached — invoking recovery callback", self._name)
        try:
            result = self._on_threshold_reached()
            if inspect.isawaitable(result):
                await result
        except asyncio.CancelledError:
            raise
        except Exception:
            self._logger.error(
                "%s: on_threshold_reached callback raised", self._name, exc_info=True
            )
