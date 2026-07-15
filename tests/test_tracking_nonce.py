import asyncio
from unittest import TestCase

import async_utils.tracking_nonce as tracking_nonce


class TrackingNonceTest(TestCase):
    def test_get_tracking_nonce(self):
        nonce = tracking_nonce.get_tracking_nonce()
        self.assertIsNotNone(nonce)
        new_nonce = tracking_nonce.get_tracking_nonce()
        self.assertGreater(new_nonce, nonce)

    def test_get_low_res_tracking_nonce(self):
        nonce = tracking_nonce.get_tracking_nonce_low_res()
        self.assertIsNotNone(nonce)
        new_nonce = tracking_nonce.get_tracking_nonce_low_res()
        self.assertGreater(new_nonce, nonce)

    def test_get_concurrent_nonce_in_low_res(self):
        async def task():
            return tracking_nonce.get_tracking_nonce_low_res()

        async def gather_tasks():
            return await asyncio.gather(task(), task())

        ret = asyncio.run(gather_tasks())
        self.assertGreaterEqual(ret[1], ret[0])

    def test_get_concurrent_nonce_in_high_res(self):
        async def task():
            return tracking_nonce.get_tracking_nonce()

        async def gather_tasks():
            return await asyncio.gather(task(), task())

        ret = asyncio.run(gather_tasks())
        self.assertGreaterEqual(ret[1], ret[0])
