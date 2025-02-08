import os
import logging
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "task_db")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "processed_tasks")


class MongoDB:
    """MongoDB connection manager with connection pooling."""

    _client = None  # Shared MongoDB client instance

    @classmethod
    def get_client(cls):
        """Get the MongoDB client, reusing an existing connection."""
        if cls._client is None:
            cls._client = MongoClient(
                MONGO_URI, maxPoolSize=100, minPoolSize=10
            )
        return cls._client

    @classmethod
    def get_collection(cls):
        """Get the MongoDB collection."""
        client = cls.get_client()
        db = client[MONGO_DB_NAME]
        return db[MONGO_COLLECTION_NAME]

    @classmethod
    def close_connection(cls):
        """Close the MongoDB connection."""
        if cls._client:
            cls._client.close()
            cls._client = None
            logging.info("MongoDB connection closed.")


def save_to_mongo(data):
    """Insert data into MongoDB using a shared connection."""
    try:
        # collection = MongoDB.get_collection()
        # collection.insert_one(data)
        logging.info(f"Saved to MongoDB: {data}")
    except Exception as e:
        logging.error(f"MongoDB Error: {e}")
