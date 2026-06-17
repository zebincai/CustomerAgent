import os
import asyncio

from bson.objectid import ObjectId
from pymongo import ASCENDING, DESCENDING, InsertOne
import pytest

from agent.client.mongodb import AsyncMongoClient, build_mongodb
from agent.utils.async_utils import async_run


def make_client(real_mongo_details, real_mongo_names):
    AsyncMongoClient._client = None
    return AsyncMongoClient(
        db_name=real_mongo_names["db_name"],
        collection_name=real_mongo_names["collection_name"],
        **real_mongo_details,
    )


def close_client(client):
    async_run(client.close())
    AsyncMongoClient._client = None


def test_parse_sort_returns_motor_sort_pairs():
    assert AsyncMongoClient.parse_sort({}) is None
    assert AsyncMongoClient.parse_sort({"name": 1, "age": -1}) == [
        ("name", ASCENDING),
        ("age", DESCENDING),
    ]


def test_client_initializes_database_and_collection(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)

    try:
        assert client.db.name.endswith(real_mongo_names["db_name"])
        assert client.collection.name == real_mongo_names["collection_name"]
        assert async_run(client._client.admin.command("ping"))["ok"] == 1.0
    finally:
        async_run(client.drop_collection())
        close_client(client)


def test_client_reuses_pooled_client(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)
    second_client = AsyncMongoClient(
        db_name=real_mongo_names["db_name"],
        collection_name=f"{real_mongo_names['collection_name']}_second",
        **real_mongo_details,
    )

    try:
        assert client._client is second_client._client
        assert second_client.collection.name.endswith("_second")
    finally:
        async_run(client.drop_collection())
        async_run(second_client.drop_collection())
        close_client(client)


def test_build_mongodb_returns_async_client(real_mongo_details, real_mongo_names):
    AsyncMongoClient._client = None
    client = build_mongodb(
        db_name=real_mongo_names["db_name"],
        collection_name=real_mongo_names["collection_name"],
        **real_mongo_details,
    )

    try:
        assert isinstance(client, AsyncMongoClient)
        assert async_run(client._client.admin.command("ping"))["ok"] == 1.0
    finally:
        async_run(client.drop_collection())
        close_client(client)


def test_async_find_one(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)

    try:
        assert async_run(client.find_one({"name": "missing"})) is None
        async_run(client.collection.insert_one({"name": "present"}))
        assert async_run(client.find_one({"name": "present"})) is not None
    finally:
        async_run(client.drop_collection())
        close_client(client)


def test_async_search_methods_return_real_results(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)

    try:
        awaitable_name = client.collection.create_index([("content", "text")])
        async_run(awaitable_name)
        async_run(
            client.collection.insert_many(
                [
                    {"name": "alice", "content": "hello customer"},
                    {"name": "bob", "content": "different text"},
                ]
            )
        )

        text_results = async_run(client.text_search("hello"))
        regex_cursor = async_run(client.regex_search("name", "ali"))
        regex_results = async_run(regex_cursor.to_list(length=None))

        assert [doc["name"] for doc in text_results] == ["alice"]
        assert [doc["name"] for doc in regex_results] == ["alice"]
    finally:
        async_run(client.drop_collection())
        close_client(client)


def test_create_index_skips_existing_real_index(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)

    try:
        async_run(client.collection.create_index([("name", ASCENDING)], name="vector_index"))
        async_run(client.create_index("vector_index", {"fields": []}))

        assert "vector_index" in async_run(client.collection.index_information())
    finally:
        async_run(client.drop_collection())
        close_client(client)


def test_vector_search_requires_configured_atlas_vector_index(real_mongo_details, real_mongo_names):
    if os.getenv("MONGO_TEST_VECTOR_SEARCH") != "1":
        pytest.skip("Set MONGO_TEST_VECTOR_SEARCH=1 and provide an Atlas vector index to run this test")
    vector_index_name = os.getenv("MONGO_TEST_VECTOR_INDEX", "vector_index")
    real_mongo_names["collection_name"] = "collection_vector_index"
    client = make_client(real_mongo_details, real_mongo_names)

    async_run(
        client.create_index(
            index_name=vector_index_name,
            vector_field="embedding",
            vector_dimensions=2,
        )
    )
    try:
        async_run(
            client.collection.insert_many(
                [
                    {"name": "near", "embedding": [0.1, 0.2], "category": "docs"},
                    {"name": "far", "embedding": [0.9, 0.8], "category": "docs"},
                ]
            )
        )
        cursor = async_run(
            client.vector_search(
                vector_field="embedding",
                vector=[0.8, 0.8],
                top_k=1,
                pre_filter={},
                index_name=vector_index_name,
            )
        )
        results = async_run(cursor.to_list(length=None))

        assert results
        assert results[0]["name"] == "far"
        assert "embedding" not in results[0]
        print(results[0])
    finally:
        # async_run(client.drop_collection())
        close_client(client)


def test_async_sample_returns_empty_list_for_non_positive_size(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)

    try:
        async_run(client.collection.insert_one({"name": "alice"}))
        assert async_run(client.sample(0)) == []
    finally:
        async_run(client.drop_collection())
        close_client(client)


def test_async_sample_uses_real_collection(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)

    try:
        async_run(client.collection.insert_many([{"name": f"user_{index}"} for index in range(5)]))
        cursor = async_run(client.sample(3))
        results = async_run(cursor.to_list(length=None))

        assert len(results) == 3
        assert {doc["name"] for doc in results}.issubset({f"user_{index}" for index in range(5)})
    finally:
        async_run(client.drop_collection())
        close_client(client)


def test_async_update_methods(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)
    oid = ObjectId()
    document = {"_id": str(oid), "name": "alice"}

    try:
        async_run(client.collection.insert_one({"_id": oid, "name": "before", "age": 1}))
        async_run(client.update(document))
        async_run(client.update_v2({"name": "alice"}, {"age": 3}))
        updated = async_run(client.collection.find_one({"_id": oid}))

        assert document == {"name": "alice"}
        assert updated["name"] == "alice"
        assert updated["age"] == 3
    finally:
        async_run(client.drop_collection())
        close_client(client)


def test_async_upsert_inserts_when_missing(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)
    document = {"name": "alice"}

    try:
        async_run(client.upsert({"name": "alice"}, document))

        assert async_run(client.collection.count_documents({"name": "alice"})) == 1
    finally:
        async_run(client.drop_collection())
        close_client(client)


def test_async_upsert_updates_existing_document(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)

    try:
        async_run(client.collection.insert_one({"name": "alice", "age": 1}))
        async_run(client.upsert({"name": "alice"}, {"age": 3}))

        assert async_run(client.collection.count_documents({"name": "alice"})) == 1
        assert async_run(client.collection.find_one({"name": "alice"}))["age"] == 3
    finally:
        async_run(client.drop_collection())
        close_client(client)


def test_async_document_helpers(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)
    oid = ObjectId()

    try:
        async_run(client.collection.insert_one({"_id": oid, "name": "alice", "active": True}))

        assert async_run(client.find_doc_by_id(str(oid)))["_id"] == oid
        assert async_run(client.insert_one({"name": "bob", "active": True}))
        inserted_ids = async_run(client.insert_many([{"name": "carl"}, {"name": "dana"}]))
        assert len(inserted_ids) == 2
        assert async_run(client.count_documents({"active": True})) == 2
        assert async_run(client.aggregate([{"$match": {"active": True}}]))

        async_run(client.bulk_write([InsertOne({"name": "eve", "active": False})]))
        assert async_run(client.collection.count_documents({"name": "eve"})) == 1

        updated = async_run(client.find_one_and_update({"name": "bob"}, {"$set": {"updated": True}}))
        assert updated["updated"] is True
        deleted = async_run(client.find_one_and_delete({"name": "eve"}))
        assert deleted["name"] == "eve"

        async_run(client.delete_doc_by_id(str(oid)))
        assert async_run(client.find_doc_by_id(str(oid))) is None
    finally:
        async_run(client.drop_collection())
        close_client(client)


def test_find_many_applies_sort_skip_and_limit(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)

    try:
        async_run(
            client.collection.insert_many(
                [
                    {"name": "anna", "active": True},
                    {"name": "bob", "active": True},
                    {"name": "carl", "active": True},
                    {"name": "dana", "active": False},
                ]
            )
        )

        cursor = async_run(
            client.find_many(
                query={"active": True},
                sort={"name": 1},
                skip=1,
                limit=2,
            )
        )
        results = async_run(cursor.to_list(length=None))

        assert [doc["name"] for doc in results] == ["bob", "carl"]
    finally:
        async_run(client.drop_collection())
        close_client(client)
