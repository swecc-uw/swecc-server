import os
import django
import pika
import json

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq-host")


def callback(ch, method, properties, body):
    data = json.loads(body)
    print("Received:", data)


connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()

queue_name = "reviewed-feedback"
channel.queue_declare(queue=queue_name, durable=True)
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

print("Listening for messages...")
channel.start_consuming()
