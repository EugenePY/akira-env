import pytest
import datetime


@pytest.fixture
def pool_classes():
    from akira_data.data.web.pool import (
        EcoEventVariablePool, InvestingDotVariablePool)
    return [EcoEventVariablePool, InvestingDotVariablePool]


def test_variable(pool_classes):
    start = datetime.datetime(2020, 1, 1)
    end = datetime.datetime(2020, 1, 20)
    for cls_ in pool_classes:
        pool = cls_()
        symbol = [i.symbol for i in pool.variables.values()][:3]
        data = pool.get_batch(symbol, start, end)
        for k, v in data.items():
            assert v is not None


def test_api():
    from akira_data.data.web import InvestingDotComAPI
    import requests
    api = InvestingDotComAPI()

    with requests.Session() as sess:
        data = api.get(sess, "AUDUSD",
                       datetime.datetime(2020, 1, 1),
                       datetime.datetime(2020, 1, 20), resolution="15")