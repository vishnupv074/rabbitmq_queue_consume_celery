import os
from celery_app import app
import json
import logging
import time
from database import save_to_mongo
from publisher import publish_message

logging.basicConfig(level=logging.WARNING)

DLQ_NAME = os.getenv("RABBITMQ_DQL", "dlq_queue")
RABBITMQ_SUCCESS_QUEUE = os.getenv("RABBITMQ_SUCCESS_QUEUE", "success_queue")


@app.task(bind=True, name="tasks.process_task", max_retries=int(os.getenv("MAX_RETRIES", 5)))
def process_task(self, data):
    """Process the JSON task, retry failures, and send to DLQ if needed."""
    try:
        parsed_data = json.loads(data)
        logging.info(f"Processing: {parsed_data}")

        # Simulating processing delay
        time.sleep(3)

        # Store processed data in MongoDB
        save_to_mongo(parsed_data)

        # Publish success info to another queue
        publish_message(RABBITMQ_SUCCESS_QUEUE, parsed_data)

        logging.info(f"Task successfully processed: {parsed_data}")

    except Exception as e:
        retries = self.request.retries
        logging.error(f"Task failed: {e} (Retry {retries}/{self.max_retries})")

        if retries < self.max_retries:
            raise self.retry(
                exc=e, countdown=2**retries
            )  # Exponential backoff
        else:
            logging.error(f"Max retries reached. Sending to DLQ: {data}")
            publish_message(DLQ_NAME, parsed_data)  # Send to DLQ
