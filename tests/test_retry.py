"""
Unit tests for async_utils.retry
"""

import asyncio
import unittest

from async_utils.retry import AllTriesFailedError, async_retry


class FooError(Exception):
    """
    foo_three_times throws this exception, and we set async_retry to use this to trigger a retry
    """

    pass


class BarError(Exception):
    """
    bar_three_times throws this exception, but we do not set async_retry to use this to trigger
    a retry
    """

    pass


class AsyncRetryTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.foo_counter = 0
        self.bar_counter = 0

    @async_retry(3, exception_types=[FooError], raise_exp=True, retry_interval=0)
    async def foo_three_times(self, target):
        """
        This function runs three times. It raises FooError when the target is not met.
        When FooError is called, async_retry increments a counter and logs the error,
        if the counter is three and foo_three_times still fails, then it will raise
        AllTriesFailedError.
        """
        if self.foo_counter >= target:
            return self.foo_counter
        else:
            self.foo_counter += 1
            raise FooError

    @async_retry(3, raise_exp=False, retry_interval=0)
    async def bar_three_times(self, target):
        """
        This function runs three times. It raises BarError when the target is not met.
        When FooError is called, async_retry increments a counter, if the counter is
        three and foo_three_times still fails, then it will raise AllTriesFailedError.
        """
        if self.bar_counter >= target:
            return self.bar_counter
        else:
            self.bar_counter += 1
            raise BarError

    def test_async_retry(self):
        """
        Unit tests for async_retry.
        """
        # run foo_three_times successfully
        self.foo_counter = 0
        foo_result = asyncio.get_event_loop().run_until_complete(self.foo_three_times(2))
        self.assertEqual(foo_result, 2)

        # pass a target to foo_three_times that it won't reach. This should raise the error
        # from async_retry.
        self.foo_counter = 0
        self.assertRaises(
            AllTriesFailedError,
            asyncio.get_event_loop().run_until_complete,
            self.foo_three_times(5),
        )

        # bar_three_times has raise_exp=False on async_retry. It will return None instead of
        # raising an exception if it fails to meet its condition in the three tries.
        # First run it in a case that passes.
        self.bar_counter = 0
        bar_result = asyncio.get_event_loop().run_until_complete(self.bar_three_times(2))
        self.assertEqual(bar_result, 2)

        # run bar_three_times so that it does not meet its expected conditions.
        # It will not raise an error.
        self.bar_counter = 0
        bar_result = asyncio.get_event_loop().run_until_complete(self.bar_three_times(5))
        self.assertEqual(bar_result, None)
