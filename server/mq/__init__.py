import logging
from typing import Callable
from pika.exchange_type import ExchangeType
from mq.core.manager import RabbitMQManager
from mq.core.connection_manager import ConnectionManager

LOGGER = logging.getLogger(__name__)

_manager = RabbitMQManager()

DEFAULT_EXCHANGE = "swecc-bot-exchange"


def consumer(
    queue,
    routing_key,
    exchange=DEFAULT_EXCHANGE,
    exchange_type=ExchangeType.topic,
    needs_context=False,
    declare_exchange=True,
) -> Callable:
    """decorator for registering consumers"""
    return _manager.register_callback(
        exchange, declare_exchange, queue, routing_key, exchange_type, needs_context
    )


def producer(
    exchange=DEFAULT_EXCHANGE,
    exchange_type=ExchangeType.topic,
    declare_exchange=True,
    routing_key=None,
    needs_context=False,
) -> Callable:
    """decorator for registering producers"""
    return _manager.register_producer(
        exchange, exchange_type, routing_key, needs_context
    )


async def publish_raw(exchange, routing_key, message, properties=None):
    """convenience function for ad-hoc publishing"""
    producer_name = f"raw.{exchange}.{routing_key}"
    producer = _manager.get_or_create_producer(
        producer_name, exchange, ExchangeType.topic, routing_key
    )
    return await producer.publish(message, properties=properties)


def setup(bot, bot_context):
    """
    setup function for the module, called in bot entrypoint to hook
    into lifecycle management, inject deps, etc.
    """
    LOGGER.info("Setting up RabbitMQ")

    # bot has a rabbit parasite. "what's mine is yours", it says.
    _manager.set_context(bot, bot_context)

    from mq import consumers, producers

    bot_setup_hook = getattr(bot, "setup_hook", None)

    async def wrapped_setup_hook():
        if bot_setup_hook:
            if callable(bot_setup_hook):
                await bot_setup_hook()  # type: ignore

        await initialize_rabbitmq(bot)

    bot.setup_hook = wrapped_setup_hook
    bot_close = bot.close

    async def wrapped_close():
        await shutdown_rabbitmq()
        await bot_close()

    bot.close = wrapped_close

    return _manager


async def initialize_rabbitmq(bot):
    global _manager

    await ConnectionManager().connect(loop=bot.loop)

    _manager.create_consumers()

    try:
        await _manager.start_consumers(bot.loop)
        await _manager.connect_producers(bot.loop)
        LOGGER.info("RabbitMQ consumers and producers initialized")
    except Exception as e:
        LOGGER.error(f"Error initializing RabbitMQ: {str(e)}")
        LOGGER.info("Will continue to retry connections in the background")
    finally:
        LOGGER.info("Starting health monitor")
        await _manager.start_health_monitor(bot)


async def shutdown_rabbitmq():
    global _manager

    if _manager:
        await _manager.stop_all()
