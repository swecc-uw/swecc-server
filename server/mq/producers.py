from mq.core.synchronous_producer import SynchronousRabbitProducer


def publish_verified_email(discord_id):
    producer_manager = SynchronousRabbitProducer()
    producer_manager.publish("server.verified-email", str(discord_id))
