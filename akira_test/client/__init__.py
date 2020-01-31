#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.websocket import websocket_connect
from tornado import gen
from loguru import logger
import json
import uuid
import asyncio

def add_callback():
    pass

class EnvSession(object):
    def __init__(self, env_id, host, port):
        self.env_id = env_id
        self.host = host
        self.port = port
        self.endpoint = "ws://{host}:{port}".format(
                host=host, port=port, env_id=env_id)
        self.ws = None
        self.guess = 87

    def __enter__(self):
        self.ioloop = IOLoop.instance()
        return self
   
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ioloop.spawn_callback(self.keep_alive)

        try:
            self.ioloop.start()
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt")
            self.ioloop.stop()
            sys.exit()

    def connect(self):
        logger.info("trying to connect: {endpoint}".format(
            endpoint=self.endpoint))
        try:
            self.ws = websocket_connect(self.endpoint)
        except Exception:
            logger.info("connection error")
        else:
            logger.info("connected")

    async def keep_alive(self):
        while True:
            if self.ws is None:
                await self.connect()
            else:
                logger.info("connection is healthy")
            await gen.sleep(5)

    def step(self, action):
        self.guess -= 1
        logger.info(action)
        return self.ws.write_message(action)

    def reset(self):
        self.connect()
        msg = self.ws.read_message()
        logger.info(msg)
        return msg


if __name__ == "__main__":
    try:
        async def test_testing():
            env = EnvSession(host="localhost", port=3000, env_id="bmk") 
            async with env:
                info = await env.reset()
                logger.info(info)
    except KeyboardInterrupt as e:
        print("KeyboardInterrupt")
        sys.exit()