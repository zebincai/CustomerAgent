from bson.objectid import ObjectId

from agent.client.mongodb.utils import get_objectid


def test_get_objectid_returns_existing_objectid():
    oid = ObjectId()

    assert get_objectid(oid) is oid


def test_get_objectid_converts_valid_string():
    oid = ObjectId()

    assert get_objectid(str(oid)) == oid

