import faust
from akira_env.envs.simple_env import SimpleGuessingEnv



class Order(faust.Record):
    agent_id: str
    symbol: str
    amount: int


app = faust.App('Env', broker='kafka://localhost')

action_topic = app.topic('action', key_type="agnet_id", value_type=Action)


@app.agent(orders_topic)
async def process_order(orders):
    async for order in orders:
        # process each order using regular Python
        total_price = order.price * order.quantity
        await send_order_received_email(order.account_id, order)
