import mq


@mq.producer(
    exchange="swecc-server-exchange",
    routing_key="server.verified-school-email",
)
async def publish_verified_user(discord_id):
    return discord_id
