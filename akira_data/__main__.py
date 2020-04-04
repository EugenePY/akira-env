
import datetime
import json
import os
import pickle as pkl
import sys
import types
from collections import defaultdict
from functools import update_wrapper

import arctic
import pandas as pd
import click
import pymongo
import yaml
from arctic import Arctic
from arctic.serialization.numpy_records import (DataFrameSerializer,
                                                SeriesSerializer)
from loguru import logger

from akira_data.data.web.pool import (EcoEventVariablePool,
                                      IntraDayVariablePool,
                                      InvestingDotVariablePool)
from akira_data.db.metadata import Connections


class Config(object):

    def __new__(cls):
        cls.load_config()
        return super(Config, cls).__new__(cls)

    @classmethod
    def load_config(cls):
        cls.MONGODB_URI = os.environ.get(
            "MONGODB_URI", "mongodb://localhost:27017")


def processor(f):
    """Helper decorator to rewrite a function so that it returns another
    function from it.
    """
    def new_func(*args, **kwargs):
        def processor(stream):
            return f(stream, *args, **kwargs)
        return processor
    return update_wrapper(new_func, f)


def generator(f):
    """Similar to the :func:`processor` but passes through old values
    unchanged and does not pass through the values as parameter.
    """
    @processor
    def new_func(stream, *args, **kwargs):
        for item in stream:
            yield item
        for item in f(*args, **kwargs):
            yield item
    return update_wrapper(new_func, f)


@click.group(chain=True)
@click.pass_context
def data_api_command(ctx):
    ctx.obj = dict()
    # add Plugin struscture at future
    ctx.obj["pools"] = [InvestingDotVariablePool,
                        EcoEventVariablePool,
                        IntraDayVariablePool]


@data_api_command.command()
@click.pass_context
def list_variable_pool(ctx):
    pools = ctx.obj["pools"]
    n = []
    for pool in pools:
        click.echo(f"{pool.__name__}:\n{list(pool.make_variables().keys())}")


@data_api_command.resultcallback()
def process_commands(processors):
    """This result callback is invoked with an iterable of all the chained
    subcommands.  As in this example each subcommand returns a function
    we can chain them together to feed one into the other, similar to how
    a pipe on unix works.
    """
    # Start with an empty iterable.
    stream = ()

    # Pipe it through all stream processors.
    for processor in processors:
        if processor is not None:
            stream = processor(stream)

    if isinstance(stream, types.GeneratorType):
        click.echo(list(stream))


@data_api_command.command("update-pool")
@click.option('-i', '--pool_id', 'pool_id', type=int, help='pool_id to proccess.')
@click.option('-s', '--start', 'start', type=str,
              help='start date of query, should be in dt fmt=YYYYMMDD')
@click.option('-e', '--end', 'end', type=str,
              help='end date of query, should be in dt fmt=YYYYMMDD')
@click.option('-l', '--libname', 'libname', type=str,
              help='load old data from arctic')
@click.option("--mongo_uri", "mongo_uri", envvar='MONGODB_URI',
              default="localhost:27017")
@generator
@click.pass_context
def update_pool_cmd(ctx, pool_id, start, end, libname, mongo_uri):
    config = Config()
    ctx.obj["start"] = start
    ctx.obj["end"] = end

    start, end = datetime.datetime.strptime(start, "%Y%m%d"), \
        datetime.datetime.strptime(end, "%Y%m%d")

    # for dumping usuage
    pool = ctx.obj["pools"][pool_id]()
    logger.info(f"Proccessing Pool: {pool.__class__.__name__.lower()}")
    symbols = pool.variables.keys()

    # if load we load from arctic mongodb, then filling the missing ones
    try:
        store = Arctic(mongo_uri)
        logger.info(f"Connecting mongodb from: URI={mongo_uri}.")

    # Here needs to be improved
    # for async to since evert symbol may have different length

        data_ = {}
        if store.library_exists(libname):
            lib = store.get_library(libname)
            start_ = start

            for sym in symbols:
                try:
                    d = lib.read(sym).data
                    data_[sym] = d
                    if d.index[-1] > start_:  # check db start is gt requested start
                        start_ = d.index[-1]
                except arctic.exceptions.NoDataFoundException as e:
                    logger.info(e)
            start = start_

    # update from start, in older to overide the start date data point]
    except pymongo.errors.ServerSelectionTimeoutError as e:
        click.echo(str(e))

    data = pool.get_batch(symbols, start, end)
    # merge data by replacing
    if data_:
        for sym, d in data.items():
            d = pd.merge(data_[sym], d)  # this will replace with new data
            data[sym] = d
    # dataset
    for symb, var in pool.variables.items():
        logger.info(f"symbol: {symb}")
        yield var, data[symb]


@data_api_command.command('save')
@click.option('--filename', "file", default='akira_data.csv',
              type=click.File("w"),
              help='{variable: key, data:data}',
              show_default=True)
@click.option('--stdout', "stdout", default=True,
              show_default=True)
@processor
@click.pass_context
def save_cmd(ctx, stream, file, stdout):
    dataset = {}

    for var, data in stream:
        # name = filename.format(
        dataset[var.symbol] = data  # .loc[data.index.duplicated()]
    
    data = pd.concat(dataset)

    if stdout:
        print(data.to_csv())
    else:
        file.writelines(data.to_csv())


class DataTaskCLI(click.MultiCommand):

    cmds = {"variable-task": data_api_command}  # adding variables

    def list_commands(self, ctx):
        cmd = list(self.cmds.keys())
        cmd.sort()
        return cmd

    def get_command(self, ctx, name):
        return self.cmds[name]


cli = DataTaskCLI()

if __name__ == "__main__":
    cli(prog_name="akira:data-task")
