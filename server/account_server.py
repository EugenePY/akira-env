"""Account Server tracking agent position

"""
import faust
import os
from faust.types import StreamT
from typing import Mapping
from collections import defaultdict
from arctic import Arctic, TICK_STORE
from arctic.date import mktz

from faust.livecheck import Case, Signal

app = faust.App("akira-env-position-manager",
                origin='position-manager.livecheck')

store = Arctic(os.environ.get("MONGO_URI", "localhost:27017"))
libname = os.environ.get("ORDER_LIBNAME", "akira-env.order")

if store.library_exists(libname):
    lib = store[libname]

else:
    lib = store.initialize_library(
        libname, lib_type=TICK_STORE)


class Order(faust.Record):

    SIDE_SELL = 'long'
    SIDE_BUY = 'short'
    VALID_SIDES = {SIDE_SELL, SIDE_BUY}

    ASIA_PX_ORDER = "asia-mid"  # using mid price
    ALL_DAY_ORDER = "all-day-mid"  # using mid price
    VALID_ORDER_TYPE = {ALL_DAY_ORDER, ASIA_PX_ORDER}

    id: str
    order_type: str
    model_id: str
    symbol: str
    side: str
    amount: float
    price: float

    # paper orders are not executed.
    paper_trade: bool = False

    testing: bool = False


execution_topic = app.topic('order-execution', value_type=Order)
orders_executed_topic = app.topic('order-executed', value_type=Order)
orders_topic = app.topic('orders', value_type=Order)


class Position(faust.Record):
    amount: float = 0
    price: float = 0

    def __add__(self, order):
        old = self.amount
        self.amount += order.amount
        alpha = old/self.amount
        self.price += (1 - alpha) * (order.price - self.price)
        return self


class Account(faust.Record):
    account: Mapping[str, Position]


orders_for_account = app.Table(
    'order-count-by-account', value_type=Account,
    default=lambda: Account(account={}))


@app.agent(orders_topic)
async def process_order(orders):
    async for order in orders.group_by(Order.model_id):
        print("1. ORDER recevied.")

        if not order.testing:
            # [order.symbol]
            model_account = orders_for_account[order.model_id]

            print("1. Send to Arctic DB")
            data = order.asdict()
            data["index"] = datetime.datetime.fromtimestamp(
                int(order.timestamps) * 1000, tzinfo=mktz("UTC+8"))
            lib.write(symbol=f"ORDER:{Order.model_id}",
                      data=[order.asdict()])

            await test_order.order_send_to_db.send(order)

            account = model_account.account

            if account.get(order.symbol, None) is None:
                account[order.symbol] = Position(amount=0, price=0) + order
            else:
                account[order.symbol] += order
            model_account.account = account
            orders_for_account[order.model_id] = model_account

        await test_order.order_executed.send(order.id)
        yield order


# live check
livecheck = app.LiveCheck()


@app.on_rebalance_complete.connect
async def on_rebalance_complete(sender, **kwargs):
    print("Account Table:\n" + orders_for_account.as_ansitable(
        key='model',
        value='account',
        title='Model Position',
        sort=True)
    )


@app.timer(10.0)
async def dump_count():
    if not app.rebalancing:
        print("Account Table:\n" + orders_for_account.as_ansitable(
            key='model',
            value='account',
            title='Model Position',
            sort=True)
        )


@livecheck.case(warn_stalled_after=5.0, frequency=0.5, probability=0.5)
class test_order(Case):

    order_received: Signal[Order]
    order_send_to_db: Signal[Order]
    order_sent_to_kafka: Signal[None]
    order_executed: Signal[str]

    async def run(self, side: str) -> None:
        # 1) wait for order to be sent to database.
        order = await self.order_received.wait(timeout=30.0)

        await self.order_executed.wait(timeout=30.0)

    async def make_fake_request(self) -> None:
        order = Order(model_id="bmk", symbol='akira-symbol',
                      amount=1, price=300, id=faust.uuid(),
                      order_type="asia-mid", side="long", testing=True)
        await orders_topic.send(key=order.model_id, value=order)


if __name__ == "__main__":
    app.main()
