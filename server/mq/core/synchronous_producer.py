import os

import pika


class SynchronousRabbitProducer:

    _instance = None

    def __init__(self):
        if self._initialized:
            return

        self.host = os.getenv("RABBIT_HOST", "rabbitmq-host")
        self._initialized = True
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host)
        )
        self._channel = self._connection.channel()

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(SynchronousRabbitProducer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def publish(self, routing_key, body, exchange="swecc-server-exchange"):
        self._channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=body,
        )
