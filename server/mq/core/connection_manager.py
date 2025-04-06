import asyncio
import logging
import os
import threading
import urllib

import pika
from pika.adapters.asyncio_connection import AsyncioConnection

logger = logging.getLogger(__name__)


class ConnectionManager:
    instance = None
    _instance_lock = threading.RLock()

    def __init__(self):
        if not ConnectionManager.instance._initialized:
            self._connection = None
            self._closing = False
            self._ready = asyncio.Event()
            self._connected = False
            self._loop = None
            self._url = self._build_amqp_url()
            self._connection_thread_id = None
            self._initialized = True

    async def connect(self, loop=None):
        logger.info(f"Connecting to {self._url}.")

        try:
            if self._connection and not (
                self._connection.is_closed or self._connection.is_closing
            ):
                logger.info("Using existing connection.")
                return self._connection

            self._ready.clear()

            future_connection = AsyncioConnection(
                parameters=pika.URLParameters(self._url),
                on_open_callback=self.on_connection_open,
                on_open_error_callback=self.on_connection_open_error,
                on_close_callback=self.on_connection_closed,
                custom_ioloop=loop,
            )

            self._loop = loop or asyncio.get_event_loop()
            self._connection_thread_id = threading.get_ident()

            await self._ready.wait()

            self._connection = future_connection
            return self._connection
        except Exception as e:
            logger.error(f"Failed to create connection: {str(e)}")
            self._connection = None
            raise

    def on_connection_open(self, connection):
        logger.info(f"Connection opened for {self._url}")
        self._ready.set()
        self._connected = True
        logger.info(self.is_connected())

    def on_connection_open_error(self, connection, err):
        logger.error(f"Failed to open connection: {err}")
        self._ready.set()
        self._connected = False

    def _build_amqp_url(self) -> str:
        user = os.getenv("SERVER_RABBIT_USER", "guest")
        password = os.getenv("SERVER_RABBIT_PASS", "guest")
        host = os.getenv("RABBIT_HOST", "rabbitmq-host")
        port = os.getenv("RABBIT_PORT", "5672")
        vhost = os.getenv("RABBIT_VHOST", "/")
        vhost = urllib.parse.quote(vhost, safe="")
        return f"amqp://{user}:{password}@{host}:{port}/{vhost}"

    def on_connection_closed(self, connection, reason):
        self._connected = False
        if self._closing:
            logger.info("Connection to RabbitMQ closed.")
        else:
            logger.warning(f"Connection closed unexpectedly: {reason}")

    async def close(self):
        self._closing = True
        logger.info("Closing connection...")
        if self._connection and not (
            self._connection.is_closing or self._connection.is_closed
        ):
            current_thread_id = threading.get_ident()
            if current_thread_id == self._connection_thread_id:
                self._connection.close()
            else:
                # in a different thread, need to use add_callback_threadsafe
                close_event = asyncio.Event()

                def threadsafe_close():
                    try:
                        self._connection.close()
                    except Exception as e:
                        logger.error(f"Error closing connection: {str(e)}")
                    finally:
                        # signal completion
                        asyncio.run_coroutine_threadsafe(
                            self._set_event(close_event), self._loop
                        )

                try:
                    self._connection.add_callback_threadsafe(threadsafe_close)
                    await close_event.wait()
                except Exception as e:
                    logger.error(f"Failed to schedule connection close: {str(e)}")

        self._connected = False

    async def _set_event(self, event):
        event.set()

    def is_connected(self):
        return self._connected

    def __new__(cls):
        with cls._instance_lock:
            if cls.instance is None:
                cls.instance = super(ConnectionManager, cls).__new__(cls)
                cls.instance._initialized = False
            return cls.instance
