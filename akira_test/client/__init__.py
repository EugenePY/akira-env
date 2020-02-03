# -*- coding: utf-8 -*-
import sys
from tornado.websocket import websocket_connect
from loguru import logger
import json
import uuid
import time
import asyncio
from urllib import parse


class BackTestingSession(object):
    def __init__(self, env_id, host, port, retry=3):
        self.host = host
        self.port = port
        self.env_id = env_id
        self.ws = None

        # msci
        self.retry = retry

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            logger.info("Back Test Complete")
            logger.info("=========== AKIRA-Testing END =========")
            self.ws.write_message("cleanup")

    async def connect(self):
        logger.info("============= AKIRA-Testing ============")
        logger.info("trying to connect: {endpoint}. query={query}".format(
            endpoint=self.endpoint, query=self.query))
        # retry times
        n = 0
        while True:
            try:
                self.ws = await websocket_connect(self.endpoint)
            except Exception:
                logger.debug("connection error")
                time.sleep(3)
                n += 1
                if n >= self.retry:
                    raise ValueError("Not connection")
            else:
                logger.debug("connected")
                break

    async def step(self, action):
        logger.debug("Sending Action:{}".format(action))

        msg = {"fn": "step"}
        if hasattr(action, "dump"):
            msg["args"] = {"action": action.dump()}
        else:
            msg["args"] = {"action": action}

        await self.ws.write_message(json.dumps(msg))

        msg = await self.ws.read_message()
        msg = json.loads(msg)
        return msg

    async def reset(self):
        msg = {"fn": "reset", "args": {}}
        await self.connect()
        await self.ws.write_message(json.dumps(msg))
        msg = await self.ws.read_message()
        logger.debug("Reset got: data={}".format(msg))
        return msg

    def set_mode(self, query):
        query_token = parse.urlencode({"data": json.dumps(query)})
        self.query = query
        self.endpoint = "ws://{host}:{port}/backtest/{env_id}?{query}".format(
            host=self.host, port=self.port, env_id=self.env_id, 
            query=query_token)

        return self


if __name__ == "__main__":
    def test():
        try:
            testing = BackTestingSession(
                host='localhost', port=3000, env_id="bmk")

            async def backtesting():
                act = {"answer": 1}
                async with testing.set_mode(guess, mode="develop") as env:  # connect
                    info = await env.reset()  # this request initial dataset for you
                    logger.info(info)
                    while True:
                        msg = await env.step(act)
                        logger.info(msg)
                        if msg["done"]:
                            break
                    return info

            info = asyncio.get_event_loop().run_until_complete(backtesting())
        except KeyboardInterrupt as e:
            print("KeyboardInterrupt")
            sys.exit()
