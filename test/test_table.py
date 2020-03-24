import faust
from faust.types import StreamT
import pytest
from server.account_server import (
    Order, app, orders_for_account, 
    orders_topic, process_order,
    Position)
from collections import defaultdict


@pytest.fixture()
def test_app(event_loop):
    """passing in event_loop helps avoid 'attached to a different loop' error"""
    app.finalize()
    app.conf.store = 'memory://'
    app.flow_control.resume()
    return app


@pytest.mark.asyncio()
async def test_process_order(test_app):

    async with process_order.test_context() as agent:

        order = Order(model_id="bmk", symbol='akira-symbol',
                      amount=1, price=300, id=faust.uuid(),
                      order_type="asia-mid", side="long")
        event = await agent.put(order)
        # windowed table: we select window relative to the current event
        assert orders_for_account[order.model_id].account[order.symbol] == \
            (Position(amount=0, price=0) + order)
        # in the window 3 hours ago there were no orders:
        order.symbol = "new-symbol"
        event = await agent.put(order)
 
# order count within the last hour (window is a 1-hour TumblingWindow).

# async def run_tests():
#    app.conf.store = 'memory://'   # tables must be in-memory
#    await test_process_order()

# if __name__ == '__main__':
#    import asyncio
#    loop = asyncio.get_event_loop()
#    loop.run_until_complete(run_tests())
