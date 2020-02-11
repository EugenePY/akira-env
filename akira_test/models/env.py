import abc
import inspect
import pkgutil

from loguru import logger
from marshmallow import post_load, pre_dump
import json
import marshmallow as me
from marshmallow import Schema, fields


class BaseEnv(metaclass=abc.ABCMeta):

    def __spec__(self):
        return {}

    @abc.abstractmethod
    def reset(self):
        pass

    @abc.abstractmethod
    def step(self, action, **kwargs):
        pass

    @abc.abstractclassmethod
    def serialize_env(cls, env):
        pass

    @abc.abstractclassmethod
    def deserialize_env(cls, env_data):
        pass


class PluginCollection:
    """Upon creation, this class will read the plugins package for modules
    that contain a class definition that is inheriting from the Plugin class
    """

    plugin_package = ["akira_test.envs"]

    def __new__(cls):
        cls.reload_plugins()

    @classmethod
    def get_env(cls, key):
        return cls.plugins[key]

    @classmethod
    def reload_plugins(cls):
        """Reset the list of all plugins and initiate the walk over the main
        provided plugin package to load all available plugins
        """
        cls.plugins = {}
        cls.seen_paths = []
        logger.info(f'Looking for plugins under package {cls.plugin_package}')

        for path in cls.plugin_package:
            cls.walk_package(path)

    @classmethod
    def walk_package(cls, package):
        """Recursively walk the supplied package to retrieve all plugins
        """
        imported_package = __import__(package, fromlist=['blah'])

        for _, pluginname, ispkg in pkgutil.iter_modules(imported_package.__path__,
                                                         imported_package.__name__ + '.'):
            if not ispkg:
                plugin_module = __import__(pluginname, fromlist=['blah'])
                clsmembers = inspect.getmembers(plugin_module, inspect.isclass)
                for (_, c) in clsmembers:
                    # Only add classes that are a sub class of Plugin, but NOT Plugin itself
                    if issubclass(c, BaseEnv) & (c is not BaseEnv):
                        logger.info(
                            f'    Found plugin class: {c.__module__}.{c.__name__}')
                        cls.plugins[getattr(
                            c, "env_id", c.__name__.lower())] = c


# record the experiment entry
class Episode(object):
    __tablename__ = "experiment"
    id = None
    env = None
    owner = None
    model = None
    # user space
    data = None
    meta = None
