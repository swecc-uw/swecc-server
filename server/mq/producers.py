import json

from mq.core.synchronous_producer import SynchronousRabbitProducer

from server.settings import DJANGO_DEBUG


def publish_verified_email(discord_id):
    producer_manager = SynchronousRabbitProducer()
    producer_manager.publish("server.verified-email", str(discord_id))


def dev_publish_to_review_resume(key):
    if not DJANGO_DEBUG:
        return
    producer_manager = SynchronousRabbitProducer()
    producer_manager.publish(
        "to-review", json.dumps({"key": key}), exchange="swecc-ai-exchange"
    )
