import os
from celery import Celery

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

app = Celery(
    "tasks",
    broker=f"pyamqp://guest@{RABBITMQ_HOST}//",
    include=["tasks"],
)

# Celery Configurations
app.conf.update(
    task_acks_late=True,  # Ensure tasks are acknowledged only after completion
    worker_prefetch_multiplier=1,  # Process tasks one by one to avoid starvation
    task_routes={
        "tasks.process_task": {
            "queue": "celery"
        }
    },  # Route tasks to correct queue
)

app.autodiscover_tasks()
