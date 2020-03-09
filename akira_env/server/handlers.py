import tornado
import json
from loguru import logger
from akira_test.models.env import PluginCollection


class EnvTestHandler(tornado.websocket.WebSocketHandler):
    clients_space = {}  # In memory, Space
    plugin = PluginCollection

    def open(self, env_id):
        args = self.request.arguments
        args = json.loads(args["data"][0])
        logger.info("A client connected.")
        logger.info("env_id={}, args={}".format(env_id, args))
        self.plugin()  # reload
        # checking requeset env_id
        EnvTestHandler.clients_space[self] = {
            "env": self.plugin.get_env(env_id)(**args)}

    def on_close(self):
        logger.info(f"close-code={self.close_code}")
        resource = EnvTestHandler.clients_space.pop(self)
        if self.close_code == 1000:
            logger.info("A client complete test")
            # dumping the session
            self.dump_resource(resource)
        else:
            logger.info("A client disconnected without complete")
            # drop out resource

    def dump_resource(self, resource):
        env = resource["env"]
        logger.debug(env.serialize_env(env))

    def on_message(self, message):
        # check env_id
        logger.debug("receive:{}".format(message))

        input_ = json.loads(message)

        fn = input_["fn"]
        kwargs = input_["args"]
        out = {}

        try:
            result = getattr(EnvTestHandler.clients_space[self]["env"],
                             fn)(**kwargs)
            out.update(result)

        except Exception as e:
            logger.info(e)
            out["done"] = True
            out["info"] = str(e)

        if hasattr(out, "dump"):
            out = out.dumps()
        else:
            out = json.dumps(out)
        self.write_message(out)


class EnvDeployHandler(EnvTestHandler):
    clients_space = {}
    plugin = PluginCollection

    def dump_resource(self): # dump to database
        pass


class EnvSpecHandler(tornado.web.RequestHandler):
    def get(self, env_id):
        # return action_space_id, indexer_id
        pass


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("template/index.html", endpoints={})
