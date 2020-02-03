import asyncio
import pytest
from akira_test.client import BackTestingSession
from akira_test.server.__main__ import Application
from akira_test.server.handlers import EnvTestHandler
from loguru import logger

app = Application()
app.listen(3000)

@pytest.fixture
def app():
    return app_


def test_remote_client():

    testing = BackTestingSession(
        host='localhost', port=3000, env_id="basket")

    async def backtesting():
        act = {"answer": 1}

        async with testing.set_mode("develop") as env:  # connect
            info = await env.reset()  # this request initial dataset for you
            logger.info(info)
            while True:
                msg = await env.step(act)
                logger.info(msg)
                if msg["done"]:
                    break
            return info

    info = asyncio.get_event_loop().run_until_complete(backtesting())


def test_multiple_users():
    pass