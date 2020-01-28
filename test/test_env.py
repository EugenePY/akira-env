import pytest
import pickle as pkl
from arctic import Arctic
import numpy as np
import datetime
import pandas as pd
import os


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
    from akira_api.client.base import Indexer

    idxer = Indexer(list(range(100)), n_episode=4)
    while True:
        try:
            next(idxer)
        except IndexError:
            break


@pytest.fixture(scope="module")
def test_state(arctic_testdb):
    from akira_api.client.base import EndogState
    from akira_data.data.web.pool import IntraDayVariablePool
    from arctic.date import DateRange
    import datetime
    seed = 1990
    np.random.seed(seed=seed)
    pool = IntraDayVariablePool()
    date_range = DateRange(start=datetime.datetime(
        2020, 1, 1), end=datetime.datetime(2020, 1, 20))
    symbols = [var.symbol for var in pool.variables.values()]

    endog_state = EndogState(variables=list(pool.variables.values()),
                             date_range=date_range, n_episode=100, libname="test")
    action = {sym: np.random.normal() for sym in symbols}
    state = endog_state.step(action)
    return state, endog_state


def test_state_forward(test_state):
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
    print(state)
    assert data == state
    target_ccy = 'USDCAD INTRA15M Curncy'

    # under Short: add position
    action = {target_ccy: data[target_ccy]["inv"]}
    next_state = endog_state.step(action)
    print(next_state[target_ccy])
    assert next_state[target_ccy]["inv"] == data[target_ccy]["inv"] * 2

    # under Short: offset all
    action = {target_ccy: -next_state[target_ccy]["inv"]}
    next_state = endog_state.step(action)
    print(next_state)
    assert next_state[target_ccy]["inv"] == 0.
    assert abs(next_state[target_ccy]["pnl"]) > 0
    assert next_state[target_ccy]["mk2mkt_pnl"] == 0

    # neutural:
