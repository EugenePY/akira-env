import asyncio
import pytest
from akira_test.client import BackTestingSession
from akira_test.server.__main__ import Application
from akira_test.server.handlers import EnvTestHandler
from loguru import logger
from tornado import testing, httpserver, gen, websocket


class TestEnvHandler(testing.AsyncHTTPTestCase):
    def get_app(self):
        # Required override for AsyncHTTPTestCase, sets up a dummy
        # webserver for this test.
        app = Application()
        return app

    def _mk_client(self):
        client = BackTestingSession(
            host='localhost', port=self.get_http_port(), env_id="guess_num")
        return client

    def test_backtesting_client(self):
        testing = self._mk_client()

        async def backtesting():
            act = {"answer": 2}
            history = []
            async with testing.set_mode({"max_num_guess": 5}) as env:  # connect
                info = await env.reset()  # this request initial dataset for you
                logger.info(info)
                while True:
                    msg = await env.step(act)
                    history.append(msg)
                    logger.info(msg)
                    if msg["done"]:
                        break
                return history

        hist = self.io_loop.run_sync(backtesting, timeout=3)

    def test_multiple_connection(self):
        pass
