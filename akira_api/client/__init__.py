#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from tornado.ioloop import IOLoop, PeriodicCallback
from tornado import gen
from tornado.websocket import websocket_connect


class Client(object):
    def __init__(self, url, timeout):
        self.url = url
        self.timeout = timeout
        self.ioloop = IOLoop.instance()
        self.ws = None
        self.connect()

        # 每 20 秒發送一次 ping
        PeriodicCallback(self.keep_alive, 20000, io_loop=self.ioloop).start()

        self.ioloop.start()

    @gen.coroutine
    def connect(self):
        print "trying to connect"
        try:
            self.ws = yield websocket_connect(self.url)
        except Exception, e:
            print "connection error"
        else:
            print "connected"
            self.run()

    @gen.coroutine
    def run(self):
        while True:
            msg = yield self.ws.read_message()
            if msg is None:
                print "connection closed"
                self.ws = None
                break
            else:
                print msg

    def keep_alive(self):
        if self.ws is None:
            self.connect()
        else:
            self.ws.write_message("ping")

if __name__ == "__main__":
    try:
        client = Client("ws://localhost:9000", 5)
    except KeyboardInterrupt:
        #print("KeyboardInterrupt")
        sys.exit()