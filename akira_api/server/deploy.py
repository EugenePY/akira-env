# -*- coding: utf-8 -*-

import datetime
import sys
from loguru import logger
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web

# make this as a class wrapper
class WSHandler(tornado.websocket.WebSocketHandler):
    clients = []

    def check_origin(self, origin):
        return True

    def open(self):
        logger.info("New client connected")
        #self.write_message("You are connected")
        WSHandler.clients.append(self)

    def on_message(self, message):
        self.write_message(message)

    def on_close(self):
        logger.info("Client disconnected")
        WSHandler.clients.remove(self)
        # check if the conversation is complete, dump the complete conversation
        pass

    @classmethod
    def write_to_clients(cls):
        logger.info("Writing to clients")
        for client in cls.clients:
            client.write_message("This is your reward")


application = tornado.web.Application([
    (r"/", WSHandler),
])

if __name__ == "__main__":
    try:
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(9000)
        main_loop = tornado.ioloop.IOLoop.instance()

        # Schedule event (5 seconds from now)
        #main_loop.add_timeout(datetime.timedelta(seconds=5), WSHandler.write_to_clients)

        # background update every x seconds
        # 固定每 5 秒鐘就呼叫一次 WSHandler.write_to_clients 廣播訊息
        task = tornado.ioloop.PeriodicCallback(
            WSHandler.write_to_clients,
            5 * 1000)
        task.start()

        # Start main loop
        # main_loop.start()
        main_loop.make_current()
    except KeyboardInterrupt:
        # print("KeyboardInterrupt")
        sys.exit()
