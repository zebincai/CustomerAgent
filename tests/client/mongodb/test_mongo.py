from bson.objectid import ObjectId

from agent.client.mongodb import MongoClient, build_mongodb


def make_client(real_mongo_details, real_mongo_names):
    return MongoClient(
        db_name=real_mongo_names["db_name"],
        collection_name=real_mongo_names["collection_name"],
        **real_mongo_details,
    )


def test_client_initializes_database_and_collection(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)

    try:
        assert client.db.name.endswith(real_mongo_names["db_name"])
        assert client.collection.name == real_mongo_names["collection_name"]
        assert client.client.admin.command("ping")["ok"] == 1.0
    finally:
        client.collection.drop()
        client.client.close()


def test_build_mongodb_returns_sync_client(real_mongo_details, real_mongo_names):
    client = build_mongodb(
        db_name=real_mongo_names["db_name"],
        collection_name=real_mongo_names["collection_name"],
        async_call=False,
        **real_mongo_details,
    )

    try:
        assert isinstance(client, MongoClient)
        assert client.client.admin.command("ping")["ok"] == 1.0
    finally:
        client.collection.drop()
        client.client.close()


def test_find_one_returns(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)

    try:
        assert client.find_one({"name": "missing"}) is None
        client.collection.insert_one({"name": "present"})
        assert client.find_one({"name": "present"}) is not None
    finally:
        client.collection.drop()
        client.client.close()


def test_search_methods_return_real_results(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)

    try:
        client.collection.create_index([("content", "text")])
        client.collection.insert_many(
            [
                {"name": "alice", "content": "hello customer"},
                {"name": "bob", "content": "different text"},
            ]
        )

        text_results = list(client.text_search("hello"))
        regex_results = list(client.regex_search("name", "ali"))

        assert [doc["name"] for doc in text_results] == ["alice"]
        assert [doc["name"] for doc in regex_results] == ["alice"]
    finally:
        client.collection.drop()
        client.client.close()


def test_sample_returns_empty_list_for_non_positive_size(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)

    try:
        client.collection.insert_one({"name": "alice"})
        assert client.sample(0) == []
    finally:
        client.collection.drop()
        client.client.close()


def test_sample_uses_real_collection(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)

    try:
        client.collection.insert_many([{"name": f"user_{index}"} for index in range(5)])
        results = list(client.sample(3))

        assert len(results) == 3
        assert {doc["name"] for doc in results}.issubset({f"user_{index}" for index in range(5)})
    finally:
        client.collection.drop()
        client.client.close()


def test_update_uses_object_id_and_sets_remaining_fields(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)
    oid = ObjectId()
    document = {"_id": str(oid), "name": "alice"}

    try:
        client.collection.insert_one({"_id": oid, "name": "before"})
        client.update(document)

        assert document == {"name": "alice"}
        assert client.collection.find_one({"_id": oid})["name"] == "alice"
    finally:
        client.collection.drop()
        client.client.close()


def test_update_v2_wraps_document_in_set(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)

    try:
        client.collection.insert_one({"name": "alice", "age": 1})
        client.update_v2({"name": "alice"}, {"age": 3})

        assert client.collection.find_one({"name": "alice"})["age"] == 3
    finally:
        client.collection.drop()
        client.client.close()


def test_upsert_inserts_when_document_does_not_exist(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)
    document = {"name": "alice"}

    try:
        client.upsert({"name": "alice"}, document)

        assert client.collection.count_documents({"name": "alice"}) == 1
    finally:
        client.collection.drop()
        client.client.close()


def test_upsert_updates_existing_document_by_id(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)

    try:
        client.collection.insert_one({"name": "alice", "age": 1})
        client.upsert({"name": "alice"}, {"age": 3})

        assert client.collection.count_documents({"name": "alice"}) == 1
        assert client.collection.find_one({"name": "alice"})["age"] == 3
    finally:
        client.collection.drop()
        client.client.close()


def test_find_and_delete_by_id_convert_to_object_id(real_mongo_details, real_mongo_names):
    client = make_client(real_mongo_details, real_mongo_names)
    oid = ObjectId()

    try:
        client.collection.insert_one({"_id": oid, "name": "alice"})

        assert client.find_doc_by_id(str(oid))["_id"] == oid
        delete_result = client.delete_doc_by_id(str(oid))
        assert delete_result.deleted_count == 1
        assert client.collection.find_one({"_id": oid}) is None
    finally:
        client.collection.drop()
        client.client.close()
