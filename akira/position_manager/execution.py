# get execution price
import faust
import os
from akira.position_manager.models import ExecutedPrice, Order, Tick
from mode.utils.logging import get_logger
from datetime import timedelta

logger = get_logger(__name__)

app = faust.App('akira-data',
                broker=f"kafka://{os.environ.get('KAFKA_BOOSTRAPHOST', 'localhost:9092')}")

# META Data
EXEC_ORDER_TOPIC = os.environ.get("EXEC_ORDER_TOPIC", "exec-order-topic")
SINK = os.environ.get("EXEC_PRICE", "exec-price-topic")

TABLE = os.environ.get("EXEC_PRICE_TABLE", "daily-exec-price-table")

order_execute_topic = app.topic(EXEC_ORDER_TOPIC, value_type=Order)

# dataticker
ticker_topic = app.topic(EXEC_ORDER_TOPIC, value_type=Tick)
sink = app.topic(SINK, value_type=ExecutedPrice)


def mean_price_execution(key, events):
    timestamp = key[1][0]
    values = [event.value for event in events]
    count = len(values)
    mean = sum(values) / count

    print(
        f'processing window:'
        f'{len(values)} events,'
        f'mean: {mean:.2f},'
        f'timestamp {timestamp}',
    )

    sink.send_soon(value=AggModel(date=timestamp, count=count, mean=mean))


execution_table = (
    app.Table(
        TABLE,
        default=list,
        on_window_close=mean_price_execution,
    )
    .tumbling(10, expires=timedelta(seconds=1000))
    .relative_to_field(Tick.timestamp)
)


@app.agent(ticker_topic)
async def print_windowed_events(stream):
    async for event in stream:
        value_list = tumbling_table['events'].value()
        value_list.append(event)
        tumbling_table['events'] = value_list
