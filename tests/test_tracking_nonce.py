import asyncio
from unittest import TestCase

import async_utils.tracking_nonce as tracking_nonce


class TrackingNonceTest(TestCase):
    def setUp(self):
        super().setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.addCleanup(self.loop.close)
        self.addCleanup(asyncio.set_event_loop, None)

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

        tasks = [task(), task()]
        ret = self.loop.run_until_complete(asyncio.gather(*tasks))
        self.assertGreaterEqual(ret[1], ret[0])

    def test_get_concurrent_nonce_in_high_res(self):
        async def task():
            return tracking_nonce.get_tracking_nonce()

        tasks = [task(), task()]
        ret = self.loop.run_until_complete(asyncio.gather(*tasks))
        self.assertGreaterEqual(ret[1], ret[0])
