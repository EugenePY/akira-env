from akira_test.client import BackTestingSession
from akira_test.agent.simple import RandomAgent


env = BackTestingSession(host="localhost", port="3000",
                         env_id="trading", mode="deploy")


# testing and deploying using the same code only changing the code
# xgboost

class SklearnAgent(object):
    pass


sess = BackTestingSession(host="localhost", port="3000",
                          env_id="trading")


def deploying():
    async def deploy():
        async with sess.set_meta(
                start="20200101", end="20200111", mode="test",
                libname="test") as env:

            # initial condition, this simply fetch the deployment sets
            info = await env.reset()  # re-train model
            action = await agent.fit_act(info)  # initial condition
            while True:
                # end of day + before trade information
                obs = await env.step(action)
                # do not partial fit in deploy mode
                action = await agent.act(obs)
                if obs["done"]:
                    break

    start_server = websockets.serve(deploy, "localhost", 8765)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


def backtesting():
    async def testing():
        async with sess.set_meta(
            start="20200101", end="20200111", mode="test") as env:
            # initial condition, this simply fetch the deployment sets
            info = await env.reset()
            action = await agent.fit_act(info)  # initial condition
            while True:
                # end of day + before trade information
                obs = await env.step(action)
                action = await agent.fit_act(obs)  # partial_fit
                if obs["done"]:
                    break

    for _ in range(n_epoch):
        asyncio.get_event_loop().run_until_complete(start_server)


if __name__ == "__main__":
