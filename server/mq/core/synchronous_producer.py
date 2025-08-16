import os

import pika


class SynchronousRabbitProducer:

    _instance = None

    def __init__(self):
        if self._initialized:
            return

        self.host = os.getenv("RABBIT_HOST", "rabbitmq-host")
        self._initialized = True

        # Connection parameters with heartbeat and retry settings
        connection_params = pika.ConnectionParameters(
            host=self.host,
            heartbeat=600,  # 10 minutes
            blocked_connection_timeout=300,  # 5 minutes
            retry_delay=2,
            socket_timeout=10,
        )

        self._connection = pika.BlockingConnection(connection_params)
        self._channel = self._connection.channel()

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(SynchronousRabbitProducer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _reconnect(self):
        """Reconnect to RabbitMQ if connection is lost"""
        try:
            if self._connection and not self._connection.is_closed:
                self._connection.close()
        except:
            pass  # Ignore errors when closing

        # Use same connection parameters as __init__
        connection_params = pika.ConnectionParameters(
            host=self.host,
            heartbeat=600,  # 10 minutes
            blocked_connection_timeout=300,  # 5 minutes
            retry_delay=2,
            socket_timeout=10,
        )

        self._connection = pika.BlockingConnection(connection_params)
        self._channel = self._connection.channel()

    def close(self):
        """Properly close the connection"""
        try:
            if self._channel and not self._channel.is_closed:
                self._channel.close()
            if self._connection and not self._connection.is_closed:
                self._connection.close()
        except:
            pass  # Ignore errors when closing

    def publish(self, routing_key, body, exchange="swecc-server-exchange"):
        # Check if connection/channel is still open and reconnect if needed
        if (
            not self._connection
            or self._connection.is_closed
            or not self._channel
            or self._channel.is_closed
        ):
            self._reconnect()

        try:
            self._channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=body,
            )
        except Exception as e:
            # Try to reconnect once on failure
            try:
                self._reconnect()
                self._channel.basic_publish(
                    exchange=exchange,
                    routing_key=routing_key,
                    body=body,
                )
            except Exception as retry_e:
                raise Exception(
                    f"Failed to publish message after retry: {retry_e}"
                ) from e
