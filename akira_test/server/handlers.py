import tornado
import json
from loguru import logger


class EnvTestHandler(tornado.websocket.WebSocketHandler):
    clients_space = {}

    def open(self, env_id):
        logger.info("A client connected.")
        logger.info("env_id={}".format(env_id))
        # checking requeset env_id
        EnvTestHandler.clients_space[self] = {}

    def on_close(self):
        if hasattr(self, "close_type"):
            logger.info("A client complete test")
        else:
            logger.info("A client disconnected without complete")

        # dumping the session
        resource = EnvTestHandler.clients_space.pop(self)
        self._dump_resource(resource)

    def _dump_resource(self, resource):
        logger.info("dumpping: Env={}".format(str(resource)))

    def on_message(self, message):
        # check env_id
        logger.info("Request:{}".format(message))

        if message == "reset":
            EnvTestHandler.clients_space[self] = {"guess": 0}
            self.write_message({"guess": 0, "done": False})

        elif message == "cleanup":
            self.close_type = "normal"

        else:
            answer = json.loads(message)
            logger.info("Client Answer: {}".format(answer["answer"]))

            ans = answer["answer"]
            response = {}
            if ans != 1:
                response.update({"correct": False})
            else:
                response.update({"correct": True})

            # update client space
            EnvTestHandler.clients_space[self]["guess"] += 1
            guess_count = EnvTestHandler.clients_space[self]["guess"]
            logger.info(EnvTestHandler.clients_space)
            response["num_guess"] = guess_count

            if guess_count >= 30 or response["correct"]:
                response["done"] = True
            else:
                response["done"] = False
            self.write_message(json.dumps(response))


class EnvSpecHandler(tornado.web.RequestHandler):
    def get(self, env_id):
        pass


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("template/index.html", endpoints={})
