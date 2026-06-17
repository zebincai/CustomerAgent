from typing import Union

from bson.objectid import ObjectId


def get_objectid(oid: Union[str, ObjectId]):
    if isinstance(oid, ObjectId):
        return oid
    return ObjectId(oid)
