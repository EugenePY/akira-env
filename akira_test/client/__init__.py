#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from tornado.ioloop import IOLoop, PeriodicCallback
from tornado import gen
from tornado.websocket import websocket_connect
from loguru import logger
import json


class Client(object):
    def __init__(self, url, timeout):

        self.url = url
        self.timeout = timeout
        self.ioloop = IOLoop.instance()
        self.ws = None
        self.connect()
        self.guess = 87

        PeriodicCallback(
            self.keep_alive, 20000).start()

        self.ioloop.start()

    @gen.coroutine
    def connect(self):
        logger.info("trying to connect")
        try:
            self.ws = yield websocket_connect(self.url)
        except Exception:
            logger.info("connection error")
        else:
            logger.info("connected")
            self.run()

    @gen.coroutine
    def run(self):
        while True:
            msg = yield self.ws.read_message()
            if msg is None:
                logger.info("connection closed")
                self.ws = None
                break
            else:
                logger.info(msg)

    def keep_alive(self):
        if self.ws is None:
            self.connect()
        else:
            self.ws.write_message(json.dumps({"answer": self.guess}))

if __name__ == "__main__":
    try:
        client = Client("ws://localhost:3000", 5)
    except KeyboardInterrupt:
        #print("KeyboardInterrupt")
        sys.exit()