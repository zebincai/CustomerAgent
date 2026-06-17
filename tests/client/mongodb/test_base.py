import os

from agent.client.mongodb.base import MongodbBase


def test_base_builds_mongo_url_with_explicit_values():
    base = MongodbBase(
        db_name="customer",
        collection_name="events",
        mongo_url="mongodb://localhost:27017",
        username="explicit_user",
        password="explicit_password",
    )

    assert base.db_name == f"{os.getenv('MONGO_DB_PREFIX', '')}customer"
    assert base.collection_name == "events"
    assert base.mongo_url == (
        "mongodb://localhost:27017?"
        f"connectTimeoutMS={os.getenv('MONGO_CONNECT_TIMEOUT_MS', 10000)}&"
        f"socketTimeoutMS={os.getenv('MONGO_SOCKET_TIMEOUT_MS', 50000)}&"
        f"timeoutMS={os.getenv('MONGO_TIMEOUT_MS', 50000)}"
    )
    assert base.username == "explicit_user"
    assert base.password == "explicit_password"


def test_base_appends_timeout_params_to_existing_query():
    base = MongodbBase(
        db_name="customer",
        collection_name="events",
        mongo_url="mongodb://localhost:27017/?retryWrites=true",
        username="explicit_user",
        password="explicit_password",
    )

    assert base.mongo_url == (
        "mongodb://localhost:27017/?retryWrites=true&"
        f"connectTimeoutMS={os.getenv('MONGO_CONNECT_TIMEOUT_MS', 10000)}&"
        f"socketTimeoutMS={os.getenv('MONGO_SOCKET_TIMEOUT_MS', 50000)}&"
        f"timeoutMS={os.getenv('MONGO_TIMEOUT_MS', 50000)}"
    )
    assert base.username == "explicit_user"
    assert base.password == "explicit_password"
