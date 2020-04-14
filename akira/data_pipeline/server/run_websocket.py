import ssl
import sys
import uuid
import os

import numpy as np
import click
from twisted.internet import reactor, ssl
from akira_data.data.ws.investingdotcom import InvestingdotcomProtocol
from loguru import logger


@click.command()
@click.argument("listenid", nargs=-1)
@click.option('--kafka_host', "kafka_host", envvar='KAFKA_BOOSTRAPHOST', type=str)
@click.option("--max_retry", "max_retry", type=int)
def run_ws(listenid, kafka_host, max_retry):
    """
    Run a spider within Twisted. Once it completes,
    wait 5 seconds and run another spider.
    """
    from twisted.python import log
    from autobahn.twisted.websocket import (WebSocketClientProtocol,
                                            WebSocketClientFactory, connectWS)
    from twisted.internet.protocol import ReconnectingClientFactory

    class WsReconnectClientFactory(WebSocketClientFactory,
                                   ReconnectingClientFactory):

        def clientConnectionFailed(self, connector, reason):
            print(f"Client connection failed:{reason} .. retrying ..")
            self.retry(connector)

        def clientConnectionLost(self, connector, reason):
            print(f"Client connection lost:{reason} .. retrying ..")
            self.retry(connector)

    log.startLogging(sys.stdout)
    numb = np.random.randint(0, 1000)
    server_num = np.random.randint(0, 200)
    randstr = str(uuid.uuid1())[:8]

    url = f"wss://stream{server_num}.forexpros.com/echo/{numb}/{randstr}/websocket"

    factory = WsReconnectClientFactory(url)   # , #headers=headers)
    factory.setProtocolOptions(autoPingInterval=10)
    factory.protocol = InvestingdotcomProtocol.make_subids(listenid)

    if len(kafka_host) > 0:
        logger.info("Using Kafka-Backend")
        factory.protocol.produce_to_kafka(
            topic=os.environ.get("INVESTINGDOT_COM_TOPIC", "ticker-topic"), 
            max_retry=max_retry,
            bootstrap_servers=kafka_host)

    connectWS(factory)
    reactor.run()


if __name__ == "__main__":
    run_ws()
