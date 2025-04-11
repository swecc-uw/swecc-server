import logging

from mq.core.synchronous_producer import SynchronousRabbitProducer

logger = logging.getLogger(__name__)


def publish_verified_email(discord_id):
    producer_manager = SynchronousRabbitProducer()
    producer_manager.publish("server.verified-email", str(discord_id))


def publish_health_check():
    producer_manager = SynchronousRabbitProducer()
    producer_manager.publish("server.health-check", "health-check")

    logger.info("Health check message published to RabbitMQ")
