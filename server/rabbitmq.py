import os

import django
import asyncio

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

import mq.consumers
import mq

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

loop.create_task(mq.initialize_rabbitmq(loop))

try:
    print("Running event loop")
    loop.run_forever()
except KeyboardInterrupt:
    print("Stopping event loop")
finally:
    loop.run_until_complete(mq.shutdown_rabbitmq())
