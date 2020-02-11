import pytest
import pickle as pkl
from arctic import Arctic
import numpy as np
import datetime
import pandas as pd
import os
import tornado
from mock import patch
from loguru import logger


@pytest.fixture(scope="module")
def arctic_testdb():
    uri = os.environ.get("MONGODB_URI", "localhost")
    store = Arctic(uri)
    store.delete_library('test')
    store.initialize_library('test')
    lib = store.get_library('test')

    with open("test/test_data.pkl", 'rb') as f:
        data = pkl.load(f)

    for k, v in data.items():
        lib.write(k, v)

    yield lib

    store.delete_library('test')


def test_idxer():
    from akira_test.models.state import Indexer

    idxer = Indexer(list(range(100)), n_episode=4)
    while True:
        try:
            next(idxer)
        except IndexError:
            break


def state_forward(test_state):
    state, endog_state = test_state
    date = [datetime.datetime(2020, 1, 19), datetime.datetime(2020, 1, 20)]
    data = {'USDCAD INTRA15M Curncy': {'price': 1.3066999912262, 'cost': 1.3066999912262, 'inv': -0.1458415958734349, 'pnl': 0.0, 'return': 0.0, 'act': -0.1458415958734349, 'mk2mkt_pnl': 0.0},
            'USDCHF INTRA15M Curncy': {'price': 0.97030001878738, 'cost': 0.97030001878738, 'inv': 1.157563278162424, 'pnl': 0.0, 'return': 0.0, 'act': 1.157563278162424, 'mk2mkt_pnl': 0.0},
            'USDJPY INTRA15M Curncy': {'price': 110.0299987793, 'cost': 110.0299987793, 'inv': -0.9952328703440865, 'pnl': 0.0, 'return': 0.0, 'act': -0.9952328703440865, 'mk2mkt_pnl': 0.0},
            'USDKRW INTRA15M Curncy': {'price': 1156.5550537109, 'cost': 1156.5550537109, 'inv': -0.3856004927172629, 'pnl': 0.0, 'return': 0.0, 'act': -0.3856004927172629, 'mk2mkt_pnl': 0.0},
            'USDTWD INTRA15M Curncy': {'price': 29.90299987793, 'cost': 29.90299987793, 'inv': -0.9784626022530616, 'pnl': 0.0, 'return': 0.0, 'act': -0.9784626022530616, 'mk2mkt_pnl': 0.0},
            'USDIDR INTRA15M Curncy': {'price': 0, 'cost': 0.0, 'inv': 0, 'pnl': 0.0, 'return': 0.0, 'act': 0, 'mk2mkt_pnl': 0.0},
            'USDINR INTRA15M Curncy': {'price': 70.824996948242, 'cost': 70.824996948242, 'inv': -0.34021298301048963, 'pnl': 0.0, 'return': 0.0, 'act': -0.34021298301048963, 'mk2mkt_pnl': 0.0},
            'AUDUSD INTRA15M Curncy': {'price': 0.69045001268387, 'cost': 0.69045001268387, 'inv': -1.4280145174719718, 'pnl': 0.0, 'return': 0.0, 'act': -1.4280145174719718, 'mk2mkt_pnl': 0.0},
            'NZDUSD INTRA15M Curncy': {'price': 0.66135001182556, 'cost': 0.66135001182556, 'inv': 1.4872013631411893, 'pnl': 0.0, 'return': 0.0, 'act': 1.4872013631411893, 'mk2mkt_pnl': 0.0},
            'GBPUSD INTRA15M Curncy': {'price': 1.2990499734879, 'cost': 1.2990499734879, 'inv': 2.124826480551996, 'pnl': 0.0, 'return': 0.0, 'act': 2.124826480551996, 'mk2mkt_pnl': 0.0},
            'EURUSD INTRA15M Curncy': {'price': 1.1112999916077, 'cost': 1.1112999916077, 'inv': 1.2986442733329484, 'pnl': 0.0, 'return': 0.0, 'act': 1.2986442733329484, 'mk2mkt_pnl': 0.0}}
    assert data == state
    target_ccy = 'USDCAD INTRA15M Curncy'

    # under Short: add position
    action = {target_ccy: data[target_ccy]["inv"]}
    next_state = endog_state.step(action)
    assert next_state[target_ccy]["inv"] == data[target_ccy]["inv"] * 2

    # under Short: offset all
    action = {target_ccy: -next_state[target_ccy]["inv"]}
    next_state = endog_state.step(action)
    assert next_state[target_ccy]["inv"] == 0.
    assert abs(next_state[target_ccy]["pnl"]) > 0
    assert next_state[target_ccy]["mk2mkt_pnl"] == 0


@pytest.fixture
def plugins():
    from akira_test.models.env import PluginCollection
    PluginCollection()  # reload
    return PluginCollection.plugins


def test_serilization(plugins):
    data = {
        "guess_num": {'max_num_guess': 5, 'guess_record': [],
                      'env_id': 'guess_num'}}

    for k, v in plugins.items():
        if k == "guess_num":
            env = v.deserialize_env(data[k])
            d = v.serialize_env(env)
            assert d == data[k]


def test_step(plugins):
    for k, v in plugins.items():
        if k == "guess_num":
            env = v(max_num_guess=5)
            for _ in range(5):
                info = env.reset()
                logger.info(info)
                while True:
                    state = env.step(
                        action={"answer": 2})
                    logger.info(state)
                    if state["done"]:
                        break
                data = v.serialize_env(env)
                logger.info(data)


@pytest.fixture
def env(arctic_testdb):
    from akira_test.envs.trading import TradingEnv
    from akira_data.data.web.pool import IntraDayVariablePool
    from arctic.date import DateRange
    import datetime

    seed = 1990
    np.random.seed(seed=seed)

    pool = IntraDayVariablePool()

    date_range = {"start": datetime.datetime(
        2020, 1, 1), "end": datetime.datetime(2020, 1, 20)}

    symbols = [var.symbol for var in pool.variables.values()]

    env = TradingEnv(
        symbols=list(pool.variables.keys()),
        n_episode=5, libname="test", **date_range)

    action = {sym: np.random.normal() for sym in env.symbols}
    return env


def test_trading_pnl(env):
    action = {s: 1 for s in env.symbols}
    info = env.reset()
    px = env.data.loc[env.generator.seq]
    logger.info(info)
    inv_ = 1

    while True:

        logger.info(env.generator.step)
        timestep = env.timestep
        state = env.step(action)
        logger.info(env.episode_stack[timestep])
        inv = {s: state[s]["inv"] for s in env.symbols}

        for k, v in inv.items():
            if state["done"]:
                inv_ = 0  # house cleaning
            assert v == inv_

        inv_ += 1
        if state["done"]:
            break
    out = env.generate_tearsheet().unstack(level=1)["price"]
    assert all(out == px.xs("PX_OPEN", axis=1, level=1)[out.columns])
