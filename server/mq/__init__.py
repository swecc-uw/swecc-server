import logging
from typing import Callable
from pika.exchange_type import ExchangeType
from mq.core.manager import RabbitMQManager
from mq.core.connection_manager import ConnectionManager

LOGGER = logging.getLogger(__name__)

_manager = RabbitMQManager()

DEFAULT_EXCHANGE = "swecc-server-exchange"


def consumer(
    queue,
    routing_key,
    exchange=DEFAULT_EXCHANGE,
    exchange_type=ExchangeType.topic,
    declare_exchange=True,
) -> Callable:
    """decorator for registering consumers"""
    return _manager.register_callback(
        exchange, declare_exchange, queue, routing_key, exchange_type
    )


def producer(
    exchange=DEFAULT_EXCHANGE,
    exchange_type=ExchangeType.topic,
    declare_exchange=True,
    routing_key=None,
) -> Callable:
    """decorator for registering producers"""
    return _manager.register_producer(exchange, exchange_type, routing_key)


async def publish_raw(exchange, routing_key, message, properties=None):
    """convenience function for ad-hoc publishing"""
    producer_name = f"raw.{exchange}.{routing_key}"
    producer = _manager.get_or_create_producer(
        producer_name, exchange, ExchangeType.topic, routing_key
    )
    return await producer.publish(message, properties=properties)


async def initialize_rabbitmq(loop):
    global _manager

    await ConnectionManager().connect(loop=loop)

    print("Done?")

    _manager.create_consumers()
    try:
        await _manager.start_consumers(loop)
        await _manager.connect_producers(loop)
        LOGGER.info("RabbitMQ consumers and producers initialized")
    except Exception as e:
        LOGGER.error(f"Error initializing RabbitMQ: {str(e)}")
        LOGGER.info("Will continue to retry connections in the background")
    finally:
        LOGGER.info("Starting health monitor")
        await _manager.start_health_monitor(loop)


async def shutdown_rabbitmq():
    global _manager

    if _manager:
        await _manager.stop_all()
