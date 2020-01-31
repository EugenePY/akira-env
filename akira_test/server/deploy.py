#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import json
from loguru import logger
from tornado.options import define, options

define("port", default=3000, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", EnvTestHandler)]
        settings = dict(debug=True)
        tornado.web.Application.__init__(
            self, handlers, **settings)


class EnvTestHandler(tornado.websocket.WebSocketHandler):
    clients_space = {}

    def open(self):
        logging.info("A client connected.")
        # checking requeset env_id
        EnvTestHandler.clients_space[self] = {"env": 0}
        self.write_message("This initial data")

    def on_close(self):
        logging.info("A client disconnected")
        # dumping the session
        resource = EnvTestHandler.clients_space.pop(self)
        self._dump_resource(resource)
    
    def _dump_resource(self, resource):
        logger.info("dumpping: Env={}".format(str(resource)))

    def on_message(self, message):
        # check env_id

        logging.info("Request:{}".format(repr(self.request.body)))
        answer = json.loads(message)
        logging.info("Client Answer: {}".format(answer["answer"]))
        ans = answer["answer"]

        if ans != 1:
            self.write_message("Your Answer:{} is Wrong.".format(ans))
        else:
            self.write_message("Your Answer:{} is Correct.".format(ans))

        EnvTestHandler.clients_space[self] += 1
        guess_count = EnvTestHandler.clients_space[self]
        
        self.write_message("Your already guess {} times.".format(
            guess_count))

def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()