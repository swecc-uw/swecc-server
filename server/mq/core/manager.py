import os
import urllib.parse
import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any, Coroutine

import pika
from pika.exchange_type import ExchangeType

from .consumer import AsyncRabbitConsumer
from .producer import AsyncRabbitProducer
from .connection_manager import ConnectionManager

LOGGER = logging.getLogger(__name__)


class RabbitMQManager:

    def __init__(self):
        self.consumers: Dict[str, AsyncRabbitConsumer] = {}
        self.producers: Dict[str, AsyncRabbitProducer] = {}
        self.default_amqp_url = self._build_amqp_url()
        self.callbacks: Dict[str, Dict[str, Any]] = {}

        self.producer_factories: Dict[str, Callable] = {}

    def _build_amqp_url(self) -> str:
        user = os.getenv("SERVER_RABBIT_USER", "guest")
        password = os.getenv("SERVER_RABBIT_PASS", "guest")
        host = os.getenv("RABBIT_HOST", "rabbitmq-host")
        port = os.getenv("RABBIT_PORT", "5672")
        vhost = os.getenv("RABBIT_VHOST", "/")
        vhost = urllib.parse.quote(vhost, safe="")
        return f"amqp://{user}:{password}@{host}:{port}/{vhost}"

    def register_callback(
        self,
        exchange,
        declare_exchange,
        queue,
        routing_key,
        exchange_type=ExchangeType.topic,
    ):
        def decorator(callback):
            name = f"{callback.__module__}.{callback.__name__}"

            self.callbacks[name] = {
                "callback": callback,
                "exchange": exchange,
                "queue": queue,
                "routing_key": routing_key,
                "exchange_type": exchange_type,
                "declare_exchange": declare_exchange,
            }

            return callback

        return decorator

    def register_producer(
        self,
        exchange,
        exchange_type=ExchangeType.topic,
        routing_key=None,
    ):
        def decorator(func):
            producer_name = f"{func.__module__}.{func.__name__}"

            async def producer_factory(
                message, routing_key_override=None, properties=None
            ):
                producer = self.get_or_create_producer(
                    producer_name, exchange, exchange_type, routing_key
                )

                processed_message = await func(message)

                actual_routing_key = routing_key_override or routing_key

                return await producer.publish(
                    processed_message,
                    routing_key=actual_routing_key,
                    properties=properties,
                )

            self.producer_factories[producer_name] = producer_factory
            return producer_factory

        return decorator

    def get_or_create_producer(self, name, exchange, exchange_type, routing_key=None):
        if name not in self.producers:
            producer = AsyncRabbitProducer(
                amqp_url=self.default_amqp_url,
                exchange=exchange,
                exchange_type=exchange_type,
                routing_key=routing_key,
            )
            self.producers[name] = producer

        return self.producers[name]

    def create_consumers(self):

        for name, config in self.callbacks.items():

            self.add_consumer(
                name=name,
                callback=config["callback"],
                exchange=config["exchange"],
                queue=config["queue"],
                routing_key=config["routing_key"],
                exchange_type=config["exchange_type"],
                declare_exchange=config["declare_exchange"],
            )

    def add_consumer(
        self,
        name: str,
        callback: Callable[[bytes, Any], Coroutine],
        exchange: str,
        declare_exchange: bool,
        queue: str,
        routing_key: str,
        exchange_type: ExchangeType = ExchangeType.topic,
        amqp_url: Optional[str] = None,
        prefetch_count: int = 1,
    ) -> AsyncRabbitConsumer:
        if name in self.consumers:
            raise ValueError(f"Consumer with name '{name}' already exists")

        url = amqp_url or self.default_amqp_url

        consumer = AsyncRabbitConsumer(
            amqp_url=url,
            exchange=exchange,
            exchange_type=exchange_type,
            queue=queue,
            routing_key=routing_key,
            callback=callback,
            prefetch_count=prefetch_count,
            declare_exchange=declare_exchange,
        )

        self.consumers[name] = consumer
        return consumer

    async def start_consumers(self, loop):
        LOGGER.info(f"Starting {len(self.consumers)} RabbitMQ consumers")
        for name, consumer in self.consumers.items():
            LOGGER.info(f"Starting consumer: {name}")
            await consumer.connect(loop=loop)

    async def stop_all(self):
        await self.stop_consumers()
        await self.stop_producers()
        await ConnectionManager().close()

    async def stop_consumers(self):
        LOGGER.info(f"Stopping {len(self.consumers)} RabbitMQ consumers")
        for name, consumer in self.consumers.items():
            LOGGER.info(f"Stopping consumer: {name}")
            await consumer.shutdown()

        self.consumers.clear()

    async def stop_producers(self):
        LOGGER.info(f"Stopping {len(self.producers)} RabbitMQ producers")
        for name, producer in self.producers.items():
            LOGGER.info(f"Stopping producer: {name}")
            await producer.close()

        self.producers.clear()

    async def connect_producers(self, loop):
        LOGGER.info(f"Connecting {len(self.producers)} RabbitMQ producers")
        for name, producer in self.producers.items():
            if not producer._connected:
                LOGGER.info(f"Connecting producer: {name}")
                await producer.connect(loop=loop)

    async def start_health_monitor(self, loop):

        LOGGER.info("Starting RabbitMQ connection health monitor")

        async def health_monitor():
            while True:
                try:
                    LOGGER.info(ConnectionManager().is_connected())
                    if not ConnectionManager().is_connected():
                        LOGGER.warning(
                            "RabbitMQ connection lost, attempting to reconnect"
                        )
                        try:
                            await ConnectionManager().connect(loop=loop)
                        except Exception as e:
                            LOGGER.error(f"Failed to reconnect: {str(e)}")
                            await asyncio.sleep(20)
                            continue

                    for name, consumer in list(self.consumers.items()):
                        if not consumer._connection or not consumer._channel:
                            LOGGER.warning(
                                f"Consumer {name} disconnected, attempting to reconnect"
                            )
                            try:
                                await consumer.connect(loop=loop)
                            except Exception as e:
                                LOGGER.error(
                                    f"Failed to reconnect consumer {name}: {str(e)}"
                                )

                    for name, producer in list(self.producers.items()):
                        if not producer._connected or not producer._channel:
                            LOGGER.warning(
                                f"Producer {name} disconnected, attempting to reconnect"
                            )
                            try:
                                await producer.connect(loop=loop)
                            except Exception as e:
                                LOGGER.error(
                                    f"Failed to reconnect producer {name}: {str(e)}"
                                )

                    await asyncio.sleep(30)
                except Exception as e:
                    LOGGER.error(f"Error in health monitor: {str(e)}")
                    await asyncio.sleep(60)

        loop.create_task(health_monitor())
