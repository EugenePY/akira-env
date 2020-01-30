#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import json

from tornado.options import define, options

define("port", default=3000, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler)]
        settings = dict(debug=True)
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        logging.info("A client connected.")

    def on_close(self):
        logging.info("A client disconnected")

    def on_message(self, message):
        logging.info("Request:{}".format(repr(self.request)))
        answer = json.loads(message)
        logging.info("Client Answer: {}".format(answer["answer"]))
        ans = answer["answer"]
        if ans != 1:
            self.write_message("Your Answer:{} is Wrong".format(ans))
        else:
            self.write_message("Your Answer:{} is Correct".format(ans))

def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()