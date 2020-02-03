import tornado
import json
from loguru import logger
from akira_test.models.env import PluginCollection


class EnvTestHandler(tornado.websocket.WebSocketHandler):
    clients_space = {}

    def open(self, env_id):
        args = self.request.arguments

        print(str(args["data"][0]))
        args = json.loads(args["data"][0])
        logger.info("A client connected.")
        logger.info("env_id={}, args={}".format(env_id, args))
        PluginCollection()  # reload
        # checking requeset env_id
        EnvTestHandler.clients_space[self] = {
            "env": PluginCollection.get_env(env_id)(**args)}

    def on_close(self):
        if hasattr(self, "close_type"):
            logger.info("A client complete test")
        else:
            logger.info("A client disconnected without complete")

        # dumping the session
        resource = EnvTestHandler.clients_space.pop(self)
        self.dump_resource(resource)

    def dump_resource(self, resource):
        env = resource["env"]

    def on_message(self, message):
        # check env_id
        logger.debug("receive:{}".format(message))

        input_ = json.loads(message)

        fn = input_["fn"]
        kwargs = input_["args"]
        try:
            out = getattr(EnvTestHandler.clients_space[self]["env"],
                          fn)(**kwargs)

        except Exception as e:
            logger.info(e)

        if hasattr(out, "dump"):
            out = out.dumps()
        else:
            out = json.dumps(out)
        self.write_message(out)


class EnvSpecHandler(tornado.web.RequestHandler):
    def get(self, env_id):
        pass


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("template/index.html", endpoints={})
