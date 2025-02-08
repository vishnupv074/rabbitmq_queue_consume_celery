import pika
import os
import json
import logging
from tasks import process_task
from publisher import publish_message

logging.basicConfig(level=logging.INFO)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
DLQ_NAME = os.getenv("RABBITMQ_DQL", "dlq_queue")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 5))


def process_failed_message(ch, method, properties, body):
    """
    Retries failed messages from DLQ via Celery and stops if max retries exceeded.
    """
    try:
        data = json.loads(body)
        retry_count = properties.headers.get("x-retry-count", 0) + 1

        logging.info(
            f"Retrying failed task from DLQ (Attempt {retry_count}/{MAX_RETRIES}): {data}"
        )

        if retry_count > MAX_RETRIES:
            logging.error(f"Max retries exceeded. Keeping task in DLQ: {data}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        process_task.apply_async(args=[json.dumps(data)])

        ch.basic_ack(delivery_tag=method.delivery_tag)
        logging.info(f"Requeued message for Celery processing: {data}")

    except Exception as e:
        logging.error(f"Failed to reprocess DLQ message: {e}")
        headers = properties.headers or {}
        headers["x-retry-count"] = retry_count

        publish_message(
            DLQ_NAME, data
        )  # Send back to DLQ with updated retry count
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    """Consume messages from DLQ."""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()

    channel.queue_declare(queue=DLQ_NAME, durable=True)
    channel.basic_consume(
        queue=DLQ_NAME,
        on_message_callback=process_failed_message,
        auto_ack=False,
    )

    logging.info("DLQ Consumer started. Waiting for messages...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
