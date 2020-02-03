import abc
import inspect
import pkgutil

import sqlalchemy as sa
from loguru import logger
from marshmallow import post_load, pre_dump
from marshmallow_sqlalchemy import ModelSchema
from sqlalchemy.orm import backref, relationship

from .base import Base


class BaseEnv(metaclass=abc.ABCMeta):
    def __init__(self, action_space, generator=None, info=None):
        self.action_space = action_space

    def reset(self):
        info = self.info.reset()
        obs = self.state.reset()
        return obs, info

    def step(self, action):
        datetime = self.state.current_state
        info = self.info.step(t)
        # calculate reward
        reward = self.reward(self.endog.state, action)
        # state forward
        state, last_state = self.endog.step(action)

        return reward, state, done, info

    def reward(self, state):
        pass

    def get_experiments(self, start, end):
        pass


class PluginCollection(object):
    """Upon creation, this class will read the plugins package for modules
    that contain a class definition that is inheriting from the Plugin class
    """

    def __init__(self, plugin_package):
        """Constructor that initiates the reading of all available plugins
        when an instance of the PluginCollection object is created
        """
        self.plugin_package = plugin_package
        self.reload_plugins()

    def reload_plugins(self):
        """Reset the list of all plugins and initiate the walk over the main
        provided plugin package to load all available plugins
        """
        self.plugins = {}
        self.seen_paths = []
        logger.info(f'Looking for plugins under package {self.plugin_package}')
        self.walk_package(self.plugin_package)

    def walk_package(self, package):
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
                        self.plugins[getattr(
                            c, "env_id", c.__name__.lower())] = c


class Experiment(Base):
    __tablename__ = "experiment"
    id = sa.Column(sa.Integer, primary_key=True)
    env = sa.Column(sa.String)
    owner = sa.Column(sa.String)
    model = sa.Column(sa.String)
    _try_number = sa.Column('try_number', sa.Integer, default=0)


class ExperimentSchema(ModelSchema):
    class Meta:
        model = Experiment

    @post_load
    def load_envs(self, data, **kwargs):
        env_id = data["env"]
        collection = PluginCollection("akira_test.envs")
        data["env"] = collection.plugins[env_id]
        return data

    @pre_dump
    def dump_env(self, data, **kwargs):
        if issubclass(getattr(data, "env", None), BaseEnv):
            data.env = data.env.env_id
        return data
