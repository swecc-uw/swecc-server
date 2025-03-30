import asyncio
import os

import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

import logging

import mq

# Import consumers so that the decorator runs.
# If you want to define callbacks elsewhere, make sure to import them here.
import mq.consumers

logger = logging.getLogger(__name__)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

loop.create_task(mq.initialize_rabbitmq(loop))

try:
    logger.info("Running event loop")
    loop.run_forever()
except KeyboardInterrupt:
    logger.info("Stopping event loop")
finally:
    loop.run_until_complete(mq.shutdown_rabbitmq())
