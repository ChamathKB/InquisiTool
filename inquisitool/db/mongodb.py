from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from qdrant_client import QdrantClient

from inquisitool.constants import DOCUMENT_COLLECTIONS, MONGO_DB_NAME, MONGO_URL, KNOWLEDGEBASE_COLLECTIONS
from inquisitool.tools.vector_search import create_collection, extract_text_from_pdf, load_pdf_to_qdrant, delete_collection
from fastapi import HTTPException
from datetime import datetime
import uuid

class MongoDB:
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db: AsyncIOMotorDatabase = None

    async def connect(self):
        if self.client is None:
            self.client = AsyncIOMotorClient(MONGO_URL, maxPoolSize=10)
            self.db = self.client[MONGO_DB_NAME]

    async def close(self):
        if self.client:
            self.client.close()
            self.client = None


mongodb = MongoDB()


async def get_mongodb() -> AsyncIOMotorDatabase:
    """
    Get MongoDB database connection
    Returns:
        AsyncIOMotorDatabase: MongoDB database connection object
    Raises:
        Exception: If MongoDB client is not connected
    """
    if mongodb.db is None:
        raise Exception("MongoDB client is not connected.")
    return mongodb.db


async def create_documents_collection(collection_name: str) -> dict:
    try:
        db = await get_mongodb()
        upload_entry = {
            "collection_name": collection_name,
            "uploaded_at": datetime.utcnow(),
        }
        result = await db[KNOWLEDGEBASE_COLLECTIONS].insert_one(upload_entry)

        # replace collection_name: str with mongodb object id from result.inserted_id
        create_collection(result.inserted_id)

        return {"inserted_id": result.inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collection creation failed: {str(e)}")
    

async def delete_documents_collection(qdrant: QdrantClient, collection_id: str) -> dict:
    try:
        db = await get_mongodb()
        result = await db[KNOWLEDGEBASE_COLLECTIONS].delete_one({"_id": collection_id})
        delete_collection(qdrant, collection_id)
        return {"deleted_count": result.deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collection deletion failed: {str(e)}")
    

async def upload_document(file_path: str, qdrant: QdrantClient, collection_id: str) -> dict:
    try:
        db = await get_mongodb()
        
        # text = extract_text_from_pdf(file_path)

        load_pdf_to_qdrant(file_path, qdrant, collection_id)

        upload_entry = {
            "collection_id": collection_id,
            "file_path": file_path,
            # "text": text,
            "uploaded_at": datetime.utcnow(),
        }
        result = await db[DOCUMENT_COLLECTIONS].insert_one(upload_entry)
        return {"inserted_id": result.inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")
