"""
Unit tests for async_utils.task_supervisor
"""

import asyncio
import unittest

from async_utils.task_supervisor import TaskSupervisor


class TaskSupervisorConstructionTest(unittest.TestCase):
    def test_rejects_non_positive_interval(self):
        with self.assertRaises(ValueError):
            TaskSupervisor(check=self._noop_check, interval=0)
        with self.assertRaises(ValueError):
            TaskSupervisor(check=self._noop_check, interval=-1)

    def test_rejects_non_positive_failure_threshold(self):
        with self.assertRaises(ValueError):
            TaskSupervisor(check=self._noop_check, interval=1, failure_threshold=0)

    @staticmethod
    async def _noop_check() -> bool:
        return True


class TaskSupervisorLifecycleTest(unittest.IsolatedAsyncioTestCase):
    async def test_start_is_idempotent(self):
        supervisor = TaskSupervisor(check=self._always_healthy, interval=0.01)
        self.assertFalse(supervisor.is_running)
        supervisor.start()
        first_task = supervisor._task
        supervisor.start()
        self.assertIs(supervisor._task, first_task)
        self.assertTrue(supervisor.is_running)
        await supervisor.stop()

    async def test_stop_is_idempotent_and_never_raises(self):
        supervisor = TaskSupervisor(check=self._always_healthy, interval=0.01)
        await supervisor.stop()
        self.assertFalse(supervisor.is_running)

        supervisor.start()
        await supervisor.stop()
        await supervisor.stop()
        self.assertFalse(supervisor.is_running)

    async def test_stop_cancels_background_task_cleanly(self):
        supervisor = TaskSupervisor(check=self._always_healthy, interval=0.01)
        supervisor.start()
        task = supervisor._task
        # Let the background task actually start running (reach its internal
        # try/except around the sleep) before cancelling it, so its own
        # CancelledError handling has a chance to run.
        await asyncio.sleep(0)
        await supervisor.stop()
        # The supervisor's own CancelledError is swallowed internally, so the
        # task completes normally rather than surfacing as cancelled.
        self.assertTrue(task.done())
        self.assertFalse(task.cancelled())
        self.assertIsNone(supervisor._task)

    @staticmethod
    async def _always_healthy() -> bool:
        return True


class TaskSupervisorFailureTrackingTest(unittest.IsolatedAsyncioTestCase):
    async def test_successful_checks_keep_failure_count_at_zero(self):
        supervisor = TaskSupervisor(check=self._always_healthy, interval=0.01, failure_threshold=3)
        supervisor.start()
        await asyncio.sleep(0.05)
        await supervisor.stop()
        self.assertEqual(supervisor.consecutive_failures, 0)

    async def test_consecutive_failures_trigger_threshold_callback(self):
        calls = 0

        async def on_threshold_reached():
            nonlocal calls
            calls += 1

        supervisor = TaskSupervisor(
            check=self._always_unhealthy,
            interval=0.01,
            failure_threshold=2,
            on_threshold_reached=on_threshold_reached,
        )
        supervisor.start()
        # 2 checks per threshold cycle; wait long enough for a couple of cycles.
        await asyncio.sleep(0.09)
        await supervisor.stop()
        self.assertGreaterEqual(calls, 1)

    async def test_sync_threshold_callback_is_supported(self):
        calls = 0

        def on_threshold_reached():
            nonlocal calls
            calls += 1

        supervisor = TaskSupervisor(
            check=self._always_unhealthy,
            interval=0.01,
            failure_threshold=1,
            on_threshold_reached=on_threshold_reached,
        )
        supervisor.start()
        await asyncio.sleep(0.05)
        await supervisor.stop()
        self.assertGreaterEqual(calls, 1)

    async def test_success_after_failures_resets_counter(self):
        healthy = False

        async def flaky_check():
            return healthy

        supervisor = TaskSupervisor(check=flaky_check, interval=0.01, failure_threshold=5)
        supervisor.start()
        await asyncio.sleep(0.03)
        self.assertGreater(supervisor.consecutive_failures, 0)

        healthy = True
        await asyncio.sleep(0.03)
        await supervisor.stop()
        self.assertEqual(supervisor.consecutive_failures, 0)

    async def test_exception_from_check_counts_as_failure(self):
        async def raising_check():
            raise RuntimeError("boom")

        supervisor = TaskSupervisor(check=raising_check, interval=0.01, failure_threshold=100)
        supervisor.start()
        await asyncio.sleep(0.03)
        await supervisor.stop()
        self.assertGreater(supervisor.consecutive_failures, 0)

    async def test_threshold_callback_exception_does_not_kill_supervisor(self):
        def raising_callback():
            raise RuntimeError("callback boom")

        supervisor = TaskSupervisor(
            check=self._always_unhealthy,
            interval=0.01,
            failure_threshold=1,
            on_threshold_reached=raising_callback,
        )
        supervisor.start()
        await asyncio.sleep(0.05)
        self.assertTrue(supervisor.is_running)
        await supervisor.stop()

    @staticmethod
    async def _always_healthy() -> bool:
        return True

    @staticmethod
    async def _always_unhealthy() -> bool:
        return False


if __name__ == "__main__":
    unittest.main()
