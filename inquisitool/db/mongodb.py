import uuid
from datetime import datetime

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from qdrant_client import QdrantClient

from inquisitool.constants import (
    DOCUMENT_COLLECTIONS,
    KNOWLEDGEBASE_COLLECTIONS,
    MONGO_DB_NAME,
    MONGO_URL,
)
from inquisitool.tools.vector_search import (  # extract_text_from_pdf,
    create_collection,
    delete_collection,
    load_pdf_to_qdrant,
)


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


async def create_documents_collection(qdrant: QdrantClient, collection_name: str) -> dict:
    try:
        db = await get_mongodb()
        upload_entry = {
            "collection_name": collection_name,
            "uploaded_at": datetime.utcnow(),
        }
        result = await db[KNOWLEDGEBASE_COLLECTIONS].insert_one(upload_entry)

        # replace collection_name: str with mongodb object id from result.inserted_id
        create_collection(qdrant, result.inserted_id)

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


async def create_campaign(campaign_data: dict) -> dict:
    try:
        db = await get_mongodb()
        campaign_data["created_at"] = datetime.utcnow()
        campaign_data["campaign_id"] = str(uuid.uuid4())
        result = await db["campaigns"].insert_one(campaign_data)
        return {"inserted_id": result.inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign creation failed: {str(e)}")


async def get_campaign(campaign_id: str) -> dict:
    try:
        db = await get_mongodb()
        campaign = await db["campaigns"].find_one({"campaign_id": campaign_id})
        if campaign is None:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return campaign
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign retrieval failed: {str(e)}")


async def update_campaign(campaign_id: str, update_data: dict) -> dict:
    try:
        db = await get_mongodb()
        update_data["updated_at"] = datetime.utcnow()
        result = await db["campaigns"].update_one({"campaign_id": campaign_id}, {"$set": update_data})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return {"modified_count": result.modified_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign update failed: {str(e)}")


async def delete_campaign(campaign_id: str) -> dict:
    try:
        db = await get_mongodb()
        result = await db["campaigns"].delete_one({"campaign_id": campaign_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return {"deleted_count": result.deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign deletion failed: {str(e)}")


async def list_campaigns(skip: int = 0, limit: int = 10) -> list:
    try:
        db = await get_mongodb()
        cursor = db["campaigns"].find().skip(skip).limit(limit)
        campaigns = await cursor.to_list(length=limit)
        return campaigns
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign listing failed: {str(e)}")
