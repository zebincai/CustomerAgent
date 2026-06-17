import os
import uuid

import pytest
from dotenv import load_dotenv
from pymongo import MongoClient as PyMongoClient
from pymongo.errors import PyMongoError


load_dotenv()


def mongo_connection_details():
    return {
        "mongo_url": os.getenv("MONGO_TEST_URL") or os.getenv("MONGO_URL") or "mongodb://localhost:27017",
        "username": os.getenv("MONGO_TEST_USER") or os.getenv("MONGO_USER"),
        "password": os.getenv("MONGO_TEST_PASSWORD") or os.getenv("MONGO_PASSWORD"),
    }


@pytest.fixture(scope="session")
def real_mongo_details():
    details = mongo_connection_details()
    client = PyMongoClient(
        details["mongo_url"],
        username=details["username"],
        password=details["password"],
        serverSelectionTimeoutMS=1000,
    )
    try:
        client.admin.command("ping")
    except PyMongoError as exc:
        pytest.skip(f"MongoDB integration tests require a reachable server: {exc}")
    finally:
        client.close()
    return details


@pytest.fixture
def real_mongo_names():
    return {
        "db_name": os.getenv("MONGO_TEST_DB", "customer_agent_test"),
        "collection_name": "test_collection_0001",
        # "collection_name": f"test_{uuid.uuid4().hex}",
    }
