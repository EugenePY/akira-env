#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import json
from loguru import logger
from tornado.options import define, options
from .handlers import EnvTestHandler, EnvDeployHandler, IndexHandler

define("port", default=3000, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/backtest/(?P<env_id>.*)", EnvTestHandler),
            (r"/deploy/(?P<env_id>.*)/(?P<model_id>.*)", EnvDeployHandler),
            (r"/", IndexHandler)]
        settings = dict(debug=True)
        tornado.web.Application.__init__(
            self, handlers, **settings)


def main():
    tornado.options.parse_command_line()
    logger.info(f"Starting websocket server @port={options.port}")
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()