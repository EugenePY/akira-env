# get execution price
import faust
import os
from akira.position_manager.models import ExecutedPrice, Order, Tick
from akira.position_manager.account_server import orders_executed_topic
from akira.position_manager.bots import run_agent

from mode.utils.logging import get_logger
from datetime import timedelta
import time
import numpy as np
import asyncio
import uuid

logger = get_logger(__name__)

app = faust.App('order-execution',
                broker=f"kafka://{os.environ.get('KAFKA_BOOSTRAPHOST', 'localhost:9092')}",
                version=1, topic_partitions=1)

# META Data
EXEC_ORDER_TOPIC = os.environ.get("EXEC_ORDER_TOPIC", "exec-order-topic")
order_execute_topic = app.topic(EXEC_ORDER_TOPIC, value_type=Order)

TICK_DATA_TOPIC = os.environ.get("TICK_DATA_TOPIC", "tick-topic")
SINK = os.environ.get("EXEC_PRICE", "exec-price-topic")
TABLE = os.environ.get("EXEC_PRICE_TABLE", "daily-exec-price-table")

INTERVAL = 100

ASIA_TRADING_TIME = (60 * 60 * 9, 60 * 60 * 15)  # timestamp offset

# Execution interval, durning this interval the trading agent will execut ur order
# Daily=86400

app.conf.table_cleanup_interval = 1.0


# dataticker
ticker_topic = app.topic(TICK_DATA_TOPIC, value_type=Tick)
sink = app.topic(SINK, value_type=ExecutedPrice)


def price_summary_execution(key, events):
    timestamp = key[1][0]
    values = [(event.ask + event.bid)/2 for event in events]
    spread = [(event.ask - event.bid) for event in events]
    avg_spread = np.mean(spread)
    count = len(values)
    mean = sum(values) / count
    variance = np.std(values)
    median = np.median(values)

    logger.info(
        f'symbol={events[0].symbol},'
        f'processing window:'
        f'{len(values)} events,'
        f'mean: {mean:.2f},'
        f'time interval: start={key[1][0]}, end={key[1][1]}',
    )

    sink.send_soon(
        value=ExecutedPrice(symbol=events[0].symbol,
                            window_start=int(key[1][0]),
                            window_end=int(key[1][-1]),
                            tick_count=count,
                            execute_px=mean,
                            median=median,
                            std=variance,
                            avg_spread=avg_spread,
                            method="MEAN")
    )


execution_table = (
    app.Table(
        TABLE,
        default=list,
        partitions=1,
        on_window_close=price_summary_execution,
    )
    .tumbling(INTERVAL, expires=timedelta(seconds=10))  # daily, table
    .relative_to_field(Tick.timestamp)
)

@app.agent(ticker_topic)
async def windowed_events(stream):
    async for tick in stream:
        logger.info(f"got={tick}")
        value_list = execution_table[tick.symbol].value()
        value_list.append(tick)
        execution_table[tick.symbol] = value_list


@app.agent(order_execute_topic, concurrency=100)
async def order_collecting(order_stream):
    async for order in order_stream:
        logger.info(f"got={order}")
        factory, host, port, ctx = run_agent([int(order.symbol)], 5)
        loop = asyncio.get_event_loop()
        transport = await loop.create_connection(
            factory, host, 443, ssl=ctx)
        result = await transport[1].is_closed
        print(f"executed_price={result.execute_px[0]}")
        order.exec_price = result.execute_px[0]

@app.timer(5)
async def test_order():
    await order_collecting.send(
        value=Order(id=uuid.uuid1(), model_id="bmk", agent_type="MEAN", 
                    symbol=1, side="LONG", amount=10., testing=True)
        )

if __name__ == "__main__":
    app.main()
