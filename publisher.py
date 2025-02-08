import os
import json
import pika

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")


def publish_message(queue_name, body):
    """Send a JSON message to RabbitMQ queue."""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=json.dumps(body),
        properties=pika.BasicProperties(
            delivery_mode=2
        ),  # Persistent messages
    )

    connection.close()
