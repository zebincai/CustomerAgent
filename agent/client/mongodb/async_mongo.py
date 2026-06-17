import asyncio
from typing import Any, Dict, List, Optional

import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.operations import SearchIndexModel

from .utils import get_objectid
from .base import MongodbBase


class AsyncMongoClient(MongodbBase):
    _client = None
    _lock = asyncio.Lock()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = self.get_client()
        self.db = self._client[self.db_name]
        self.collection = self.db[self.collection_name]

    @staticmethod
    def parse_sort(sort: Dict):
        if not sort:
            return None
        new_sort = []
        for key, value in sort.items():
            if value == 1:
                direction = pymongo.ASCENDING
            else:
                direction = pymongo.DESCENDING
            new_sort.append((key, direction))
        return new_sort

    def get_client(self):
        """Get or create async MongoDB client with connection pooling"""
        if AsyncMongoClient._client is None:
            # Create a pooled async client with connection settings
            AsyncMongoClient._client = AsyncIOMotorClient(
                self.mongo_url,
                username=self.username,
                password=self.password,
                maxPoolSize=200,  # Increase pool size for better concurrency
                minPoolSize=50,
                maxIdleTimeMS=60000,
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=60000,
                connectTimeoutMS=10000,
                retryWrites=True,
                retryReads=True,
                # Add connection pool timeout to prevent hanging connections
                waitQueueTimeoutMS=10000,
                # Additional performance optimizations
                heartbeatFrequencyMS=10000,
            )
        return AsyncMongoClient._client

    async def drop_collection(self):
        """Drop the collection"""
        # collection = await self.get_collection()
        await self.collection.drop()

    async def find_one(self, *args: Any, **kwargs: Any) -> bool:
        """Check if document exists"""
        return await self.collection.find_one(*args, **kwargs)

    async def text_search(
        self,
        query: str,
        caseSensitive: bool = False,
        diacriticSensitive: bool = False,
        language: str = "none",
    ) -> List[Dict]:
        """Perform text search"""
        # collection = await self.get_collection()
        cursor = self.collection.find(
            {
                "$text": {
                    "$search": query,
                }
            }
        )
        return await cursor.to_list(length=None)

    async def regex_search(self, field: str, query: str) -> List[Dict]:
        """Perform regex search"""
        # collection = await self.get_collection()
        cursor = self.collection.find(
            {
                field: {
                    "$regex": f"{query}",
                    "$options": "is",
                }
            }
        )
        return cursor

    async def create_index(
        self,
        index_name: str,
        vector_field: str,
        vector_dimensions: int = 1024,
        definition: Dict = None,
        filter_fields: List[str] = None,
    ) -> None:

        def default_definition(vector_field: str, filter_fields: List[str] = None):
            filter_fields = [] if filter_fields is None else filter_fields
            fields = {
                vector_field: {
                    "type": "knnVector",
                    "dimensions": vector_dimensions,
                    "similarity": "cosine",
                },
            }
            for ff in filter_fields:
                fields[ff] = {"type": "token"}

            definition = {
                "mappings": {
                    "dynamic": True,
                    "fields": fields,
                },
                "algorithm": "hnsw",  # 显式指定算法
                "hnswOptions": {  # 可选，全部有默认值
                    "m": 16,  # 邻接表大小
                    "efConstruction": 200,  # 构建时候选集
                    "ef": 40,  # 查询时候选集
                },
            }
            return definition

        collections = await self.db.list_collection_names()
        if self.collection_name not in collections:
            await self.db.create_collection(
                self.collection_name,
                validator={  # 可选：JSON Schema 校验
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": [vector_field],
                        "properties": {vector_field: {"bsonType": "array"}},
                    }
                },
            )
        indexes = await self.collection.index_information()
        if index_name in indexes:
            return
        """Create index"""
        definition = default_definition(vector_field, filter_fields) if definition is None else definition
        model = SearchIndexModel(definition=definition, name=index_name)
        await self.collection.create_search_index(model)

    async def vector_search(
        self,
        vector_field: str,
        vector: List[float],
        top_k: int = 10,
        score_threshold: float = 0.0,
        pre_filter: Dict[str, Any] | None = None,
        index_name: str = "vector_index",
    ) -> List[Dict[str, Any]]:
        """
        向量近似检索 + 类别过滤
        pre_filter: 普通 MongoDB 查询表达式，如 {"category": "tech", "author": {"$in": ["sam", "bob"]}}
        """
        vs_stage = {
            "$vectorSearch": {
                "index": index_name,
                "path": vector_field,
                "queryVector": vector,
                "numCandidates": top_k * 10,
                "limit": top_k,
            }
        }
        # 如果有过滤条件，追加 filter 字段
        if pre_filter:
            vs_stage["$vectorSearch"]["filter"] = pre_filter

        pipeline = [
            vs_stage,
            {
                "$addFields": {  # 只加字段，不丢字段
                    "score": {"$meta": "vectorSearchScore"}
                }
            },
            {"$match": {"score": {"$gte": score_threshold}}},
            {"$project": {vector_field: 0}},
        ]
        return self.collection.aggregate(pipeline)

    async def close(self):
        self._client.close()

    async def sample(self, num: int) -> List[Dict]:
        """Get random sample of documents"""
        if num < 1:
            return []

        # collection = await self.get_collection()
        return self.collection.aggregate([{"$sample": {"size": num}}])

    async def update(self, document: Dict) -> None:
        """Update document by ID"""
        # collection = await self.get_collection()
        doc_id = document["_id"]
        doc_id = get_objectid(doc_id)
        query = {"_id": doc_id}
        document.pop("_id")
        await self.collection.update_one(query, {"$set": document})

    async def update_v2(self, query: Dict, document: Dict) -> None:
        """Update document with custom query"""
        # collection = await self.get_collection()
        await self.collection.update_one(query, {"$set": document})

    async def upsert(self, query: Dict, document: Dict) -> None:
        """Upsert document"""
        # collection = await self.get_collection()
        doc_query = await self.collection.find_one(query)
        if doc_query is None:
            await self.collection.insert_one(document)
        else:
            await self.collection.update_one({"_id": doc_query["_id"]}, {"$set": document})

    async def find_doc_by_id(self, doc_id: str) -> Optional[Dict]:
        """Find document by ID"""
        doc_id = get_objectid(doc_id)
        return await self.collection.find_one({"_id": doc_id})

    async def delete_doc_by_id(self, doc_id: str) -> None:
        """Delete document by ID"""
        doc_id = get_objectid(doc_id)
        await self.collection.delete_one({"_id": doc_id})

    async def find_many(
        self,
        query: Dict = {},
        limit: int = 0,
        sort: Dict = None,
        skip: int = 0,
    ):
        """Find multiple documents"""
        # collection = await self.get_collection()
        cursor = self.collection.find(query)
        new_sort = self.parse_sort(sort)
        if new_sort is not None:
            cursor = cursor.sort(new_sort)
        if skip > 0:
            cursor = cursor.skip(skip)
        if limit > 0:
            cursor = cursor.limit(limit)

        return cursor

    async def insert_one(self, document: Dict) -> str:
        """Insert a single document"""
        # collection = await self.get_collection()
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def insert_many(self, documents: List[Dict]) -> str:
        """Insert a single document"""
        # collection = await self.get_collection()
        result = await self.collection.insert_many(documents)
        return result.inserted_ids

    async def count_documents(self, query: Dict = {}) -> int:
        """Count documents matching query"""
        # collection = await self.get_collection()
        return await self.collection.count_documents(query)

    async def aggregate(self, pipeline: List[Dict]) -> List[Dict]:
        """Run aggregation pipeline"""
        # collection = await self.get_collection()
        cursor = self.collection.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def bulk_write(self, requests) -> None:
        """Perform bulk write operations"""
        # collection = await self.get_collection()
        await self.collection.bulk_write(requests)

    async def find_one_and_update(self, query: Dict, update: Dict) -> Optional[Dict]:
        """Find and update a single document"""
        # collection = await self.get_collection()
        return await self.collection.find_one_and_update(query, update, return_document=True)

    async def find_one_and_delete(self, query: Dict) -> Optional[Dict]:
        """Find and delete a single document"""
        # collection = await self.get_collection()
        return await self.collection.find_one_and_delete(query)
