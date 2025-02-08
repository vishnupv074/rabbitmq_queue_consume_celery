import os
import json
import pika
import logging
from tasks import process_task  # Import the Celery task

# RabbitMQ Config
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
QUEUE_NAME = os.getenv("RABBITMQ_MAIN_QUEUE", "task_queue")

logging.basicConfig(level=logging.INFO)


def callback(ch, method, properties, body):
    """Consume messages from RabbitMQ and send them to Celery."""
    try:
        data = json.loads(body.decode())
        logging.info(f"Received message: {data}")

        # Pass the raw JSON to Celery for processing
        process_task.apply_async(args=[data])

        # Acknowledge the message after sending to Celery
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logging.error(f"Error processing message: {e}")
        ch.basic_nack(
            delivery_tag=method.delivery_tag, requeue=False
        )  # Dead Letter Queue


def start_consumer():
    """Start the RabbitMQ consumer to listen for raw JSON messages."""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    logging.info(f"Listening for messages on '{QUEUE_NAME}'...")

    channel.basic_consume(
        queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False
    )
    channel.start_consuming()


if __name__ == "__main__":
    start_consumer()
