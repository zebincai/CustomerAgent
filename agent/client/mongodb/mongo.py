from typing import Any

from pymongo import MongoClient as PyMongoClient

from .utils import get_objectid
from .base import MongodbBase


class MongoClient(MongodbBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = PyMongoClient(self.mongo_url, username=self.username, password=self.password)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

    def drop_collection(self):
        self.collection.drop()

    def find_one(self, *args: Any, **kwargs: Any):
        return self.collection.find_one(*args, **kwargs)


    def text_search(
        self,
        query: str,
        caseSensitive: bool = False,
        diacriticSensitive: bool = False,
        language: str = "none",
    ):
        return self.collection.find(
            {
                "$text": {
                    "$search": query,
                    # "$language": language,
                    # "$caseSensitive": caseSensitive,
                    # "$diacriticSensitive": diacriticSensitive,
                }
            }
        )

    def regex_search(self, field: str, query: str):
        return self.collection.find(
            {
                field: {
                    "$regex": f"{query}",
                    "$options": "is",
                }
            }
        )

    def sample(self, num: int):
        if num < 1:
            return []

        return self.collection.aggregate(
            [
                {
                    "$sample": {
                        "size": num,
                    }
                }
            ]
        )

    def update(self, document):
        doc_id = get_objectid(document["_id"])
        query = {"_id": doc_id}
        document.pop("_id")
        self.collection.update_one(query, {"$set": document})

    def update_v2(self, query, document):
        self.collection.update_one(query, {"$set": document})

    def upsert(self, query, document):
        doc_query = self.collection.find_one(query)
        if doc_query is None:
            self.collection.insert_one(document)
        else:
            self.collection.update_one({"_id": doc_query["_id"]}, {"$set": document})

    def find_doc_by_id(self, doc_id: str):
        doc_id = get_objectid(doc_id)
        return self.collection.find_one({"_id": doc_id})

    def delete_doc_by_id(self, doc_id: str):
        doc_id = get_objectid(doc_id)
        return self.collection.delete_one({"_id": doc_id})


if __name__ == "__main__":
    mongo_client = MongoClient(db_name="test_db", collection_name="test_collection")
    # for index in mongo_client.collection.list_indexes():
    #     print(index)

    # data = [
    #     "129 Wheels on the bus-1.mp3",
    #     "100 Sing a song of six pence.mp3",
    #     "065 London bridge is falling down.mp3",
    #     "054 Ice cream song for children.mp3",
    # ]

    # data = ["你好，对，不，起", "对不起", "谢谢， 写", "再见，见", "请问", "没关系", "对不起", "没事", "不客气", "不谢"]
    # data = ["这是我的一个姐姐", "他不是你的妹妹", "我想要去北京玩", "这个copilt 合适"]
    # for item in data:
    #     mongo_client.collection.insert_one({"user_id": item, "audio_ids": []})
    # mongo_client.collection.update_search_index(name="user_id_text", field="user_id")
    output = mongo_client.search("合适")
    for item in output:
        print(item)
