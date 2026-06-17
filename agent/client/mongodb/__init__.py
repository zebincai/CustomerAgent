from .async_mongo import AsyncMongoClient
from .mongo import MongoClient

__all__ = [
    "AsyncMongoClient",
    "MongoClient",
]


def build_mongodb(db_name, collection_name: str, async_call=True, **kwargs):
    if not async_call:
        return MongoClient(
            db_name=db_name,
            collection_name=collection_name,
            **kwargs,
        )
    else:
        return AsyncMongoClient(
            db_name=db_name,
            collection_name=collection_name,
            **kwargs,
        )
