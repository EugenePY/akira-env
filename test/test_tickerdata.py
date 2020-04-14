from unittest.mock import Mock, patch

import pytest
import datetime
from akira.data_pipeline.server.app import app, proccess_tick_data, Ticker

data = {'symbol': 'FEED:pid-2',
        'data': {'pid': '2', 'last_dir': 'redBg', 'last_numeric': 1.2285,
                 'last': '1.2285', 'bid': '1.2283', 'ask': '1.2286', 'high': '1.2327',
                 'low': '1.2210', 'last_close': '1.2260', 'pc': '+0.0025', 'pcp': '+0.20%',
                 'pc_col': 'greenFont', 'turnover': '77.51K', 'turnover_numeric': '77512',
                 'time': '12:16:48', 'timestamp': 1586175406},
        'index': datetime.datetime.utcfromtimestamp(1586175406), 'metadata': None}

def test_serilize():
    tick = Ticker(**data)
    print(tick)
    raise
    

@pytest.fixture()
def test_app(event_loop):
    """passing in event_loop helps avoid 'attached to a different loop' error"""
    app.finalize()
    app.conf.store = 'memory://'
    app.flow_control.resume()
    return app

@pytest.mark.asyncio()
async def test_proccess_tickr_data(test_app):
    async with proccess_tick_data.test_context() as agent:
        event = await agent.put(data)
        assert agent.results[event.message.offset] == 'heyYOLO'
