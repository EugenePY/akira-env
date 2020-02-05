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
            self.ws.close(1000)

    def send(self, dict_):
        msg = json.dumps(dict_)
        self.ws.write_message(msg)

    def send_fn_call(self, fn, kwarg):
        pass

    async def connect(self):
        logger.info("============= AKIRA-Testing ============")
        logger.info("trying to connect: {endpoint}. query={query}".format(
            endpoint=self.endpoint, query=self.meta))
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

    def set_meta(self, meta):
        query_token = parse.urlencode({"data": json.dumps(meta)})
        self.meta = meta
        self.endpoint = \
            f"ws://{self.host}:{self.port}/backtest/{self.env_id}?{query_token}"
        return self
