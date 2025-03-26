import os

import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

import pika
import json
import logging
from resume_review.models import Resume

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq-host")


# Sample callback, will fill in later
def callback(ch, method, properties, body):
    expected_fields = ["user_id", "resume_id", "feedback", "error"]

    # Validate body
    try:
        data = json.loads(body)
        for field in expected_fields:
            if field not in data:
                raise ValueError(f"Field {field} not found in message")
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
        return
    except ValueError as e:
        logging.error(f"Error validating message: {e}")
        return

    if data["error"]:
        logging.info(f"Received error message: {data['error']}")
        return

    resume_object = Resume.objects.filter(id=data["resume_id"]).first()

    if not resume_object:
        logging.error(
            f"Resume with ID {data['resume_id']} not found"
        )  # Technically unreachable, though can't hurt to check for
        return

    resume_object.feedback = data["feedback"]
    resume_object.save()

    logging.info(
        f"Feedback for resume {data['resume_id']} updated with value {data['feedback']}"
    )


connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()

queue_name = "reviewed-feedback"
channel.queue_declare(queue=queue_name, durable=True)
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

logging.info("Listening for messages...")
channel.start_consuming()
