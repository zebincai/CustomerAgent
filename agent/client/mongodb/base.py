import os
from typing import Optional


class MongodbBase:
    def __init__(
        self,
        db_name: str,
        collection_name: str,
        mongo_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        super().__init__()
        self.db_name = f"{os.getenv('MONGO_DB_PREFIX', '')}{db_name}"
        self.collection_name = collection_name
        mongo_url = mongo_url or os.environ.get("MONGO_URL")
        connectTimeoutMS = os.getenv("MONGO_CONNECT_TIMEOUT_MS", 10000)
        socketTimeoutMS = os.getenv("MONGO_SOCKET_TIMEOUT_MS", 50000)
        timeoutMS = os.getenv("MONGO_TIMEOUT_MS", 50000)
        if "?" not in mongo_url:
            mongo_url = f"{mongo_url}?"
        else:
            mongo_url = f"{mongo_url}&"
        self.mongo_url = (
            f"{mongo_url}connectTimeoutMS={connectTimeoutMS}&socketTimeoutMS={socketTimeoutMS}&timeoutMS={timeoutMS}"
        )
        self.username = username or os.environ.get("MONGO_USER")
        self.password = password or os.environ.get("MONGO_PASSWORD")
