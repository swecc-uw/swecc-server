import functools
import logging
import os
import threading

import pika

logger = logging.getLogger(__name__)


class SynchronousRabbitProducer:

    _instance = None
    _lock = threading.RLock()

    def __init__(self):
        if self._initialized:
            return

        self.host = os.getenv("RABBIT_HOST", "rabbitmq-host")
        self._initialized = True
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host)
        )
        self._channel = self._connection.channel()
        self._connection_thread_id = threading.get_ident()

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(SynchronousRabbitProducer, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def publish(self, routing_key, body, exchange="swecc-server-exchange"):
        current_thread_id = threading.get_ident()

        if current_thread_id == self._connection_thread_id:
            self._channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=body,
            )
        else:
            # in a different thread, need to use add_callback_threadsafe
            try:
                self._connection.add_callback_threadsafe(
                    functools.partial(
                        self._channel.basic_publish,
                        exchange=exchange,
                        routing_key=routing_key,
                        body=body,
                    )
                )
            except Exception as e:
                logger.error(f"Error publishing message: {str(e)}")
                if self._connection.is_closed:  # attempt to reconnect
                    logger.info("Attempting to reconnect...")
                    self._reopen_connection()
                    # try again after reconnection
                    self._connection.add_callback_threadsafe(
                        functools.partial(
                            self._channel.basic_publish,
                            exchange=exchange,
                            routing_key=routing_key,
                            body=body,
                        )
                    )

    def _reopen_connection(self):
        with self._lock:
            if self._connection.is_closed:
                try:
                    self._connection = pika.BlockingConnection(
                        pika.ConnectionParameters(host=self.host)
                    )
                    self._channel = self._connection.channel()
                    self._connection_thread_id = threading.get_ident()
                except Exception as e:
                    logger.error(f"Failed to reopen connection: {str(e)}")
