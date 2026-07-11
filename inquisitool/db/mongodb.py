import logging
import uuid
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from qdrant_client import QdrantClient

from inquisitool.constants import (
    CAMPAIGN_INTERACTIONS_COLLECTION,
    CAMPAIGNS_COLLECTION,
    DOCUMENT_COLLECTION,
    KNOWLEDGEBASE_COLLECTION,
    MONGO_DB_NAME,
    MONGO_URL,
)
from inquisitool.tools.vector_search import (  # extract_text_from_pdf,
    create_collection,
    delete_collection,
    load_pdf_to_qdrant,
)

logger = logging.getLogger(__name__)


class MongoDB:
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db: AsyncIOMotorDatabase = None

    async def connect(self):
        if self.client is None:
            self.client = AsyncIOMotorClient(MONGO_URL, maxPoolSize=10)
            self.db = self.client[MONGO_DB_NAME]
            logger.info("MongoDB connected to %s", MONGO_DB_NAME)

    async def close(self):
        if self.client:
            self.client.close()
            self.client = None
            logger.info("MongoDB connection closed")


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


# documents
async def create_documents_collection(qdrant: QdrantClient, collection_name: str) -> dict:
    db = await get_mongodb()
    upload_entry = {
        "collection_name": collection_name,
        "uploaded_at": datetime.now(timezone.utc),
    }
    result = await db[KNOWLEDGEBASE_COLLECTION].insert_one(upload_entry)
    create_collection(qdrant, result.inserted_id)
    return {"inserted_id": result.inserted_id}


async def delete_documents_collection(qdrant: QdrantClient, collection_id: str) -> dict:
    db = await get_mongodb()
    result = await db[KNOWLEDGEBASE_COLLECTION].delete_one({"_id": collection_id})
    delete_collection(qdrant, collection_id)
    return {"deleted_count": result.deleted_count}


async def upload_document(file_path: str, qdrant: QdrantClient, collection_id: str) -> dict:
    db = await get_mongodb()
    load_pdf_to_qdrant(file_path, qdrant, collection_id)
    upload_entry = {
        "collection_id": collection_id,
        "file_path": file_path,
        "uploaded_at": datetime.now(timezone.utc),
    }
    result = await db[DOCUMENT_COLLECTION].insert_one(upload_entry)
    return {"inserted_id": result.inserted_id}


# campaigns
async def create_campaign(campaign_data: dict) -> dict:
    db = await get_mongodb()
    campaign_data["created_at"] = datetime.now(timezone.utc)
    campaign_data["updated_at"] = datetime.now(timezone.utc)
    campaign_data["campaign_id"] = str(uuid.uuid4())
    await db[CAMPAIGNS_COLLECTION].insert_one(campaign_data)
    return {"campaign_id": campaign_data["campaign_id"]}


async def get_campaign(campaign_id: str) -> dict:
    db = await get_mongodb()
    campaign_id = str(uuid.UUID(campaign_id))
    campaign = await db[CAMPAIGNS_COLLECTION].find_one({"campaign_id": campaign_id})
    if campaign is None:
        logger.warning("Campaign not found: %s", campaign_id)
        raise ValueError(f"Campaign not found: {campaign_id}")
    campaign["_id"] = str(campaign["_id"])
    return campaign


async def update_campaign(campaign_id: str, update_data: dict) -> dict:
    db = await get_mongodb()
    campaign_id = str(uuid.UUID(campaign_id))
    update_data["updated_at"] = datetime.now(timezone.utc)
    result = await db[CAMPAIGNS_COLLECTION].update_one({"campaign_id": campaign_id}, {"$set": update_data})
    if result.modified_count == 0:
        logger.warning("Campaign not found for update: %s", campaign_id)
        raise ValueError(f"Campaign not found: {campaign_id}")
    return {"modified_count": result.modified_count}


async def delete_campaign(campaign_id: str) -> dict:
    db = await get_mongodb()
    campaign_id = str(uuid.UUID(campaign_id))
    result = await db[CAMPAIGNS_COLLECTION].delete_one({"campaign_id": campaign_id})
    if result.deleted_count == 0:
        logger.warning("Campaign not found for deletion: %s", campaign_id)
        raise ValueError(f"Campaign not found: {campaign_id}")
    logger.info("Campaign deleted: %s", campaign_id)
    return {"deleted_count": result.deleted_count}


async def list_campaigns(skip: int = 0, limit: int = 10) -> list:
    db = await get_mongodb()
    cursor = db[CAMPAIGNS_COLLECTION].find().skip(skip).limit(limit)
    campaigns = await cursor.to_list(length=limit)
    for campaign in campaigns:
        campaign["_id"] = str(campaign["_id"])
    return campaigns


# Campaign run interactions
async def get_session_count(user_id: str, campaign_id: str) -> int:
    """Count how many sessions a user has had for a campaign"""
    db = await get_mongodb()
    return await db[CAMPAIGN_INTERACTIONS_COLLECTION].count_documents(
        {"user_id": str(uuid.UUID(user_id)), "campaign_id": str(uuid.UUID(campaign_id))}
    )


async def create_interaction(interaction_data: dict) -> dict:
    """Create a new user interaction record for a campaign run"""
    db = await get_mongodb()
    session_id = str(uuid.uuid4())
    session_number = await get_session_count(interaction_data["user_id"], interaction_data["campaign_id"]) + 1
    interaction_data["created_at"] = datetime.now(timezone.utc)
    interaction_data["interaction_id"] = str(uuid.uuid4())
    interaction_data["session_id"] = session_id
    interaction_data["session_number"] = session_number
    await db[CAMPAIGN_INTERACTIONS_COLLECTION].insert_one(interaction_data)
    return {"session_id": session_id, "session_number": session_number}


async def get_interaction(session_id: str) -> dict:
    """Get a specific interaction by session_id"""
    db = await get_mongodb()
    session_id = str(uuid.UUID(session_id))
    interaction = await db[CAMPAIGN_INTERACTIONS_COLLECTION].find_one({"session_id": session_id})
    if interaction is None:
        logger.warning("Interaction not found: %s", session_id)
        raise ValueError(f"Interaction not found: {session_id}")
    return interaction


async def update_interaction(session_id: str, update_data: dict) -> dict:
    """Update an existing interaction by session_id"""
    db = await get_mongodb()
    session_id = str(uuid.UUID(session_id))
    update_data["updated_at"] = datetime.now(timezone.utc)
    result = await db[CAMPAIGN_INTERACTIONS_COLLECTION].update_one({"session_id": session_id}, {"$set": update_data})
    if result.modified_count == 0:
        logger.warning("Interaction not found for update: %s", session_id)
        raise ValueError(f"Interaction not found: {session_id}")
    return {"modified_count": result.modified_count}


async def delete_interaction(interaction_id: str) -> dict:
    """Delete an interaction"""
    db = await get_mongodb()
    interaction_id = str(uuid.UUID(interaction_id))
    result = await db[CAMPAIGN_INTERACTIONS_COLLECTION].delete_one({"interaction_id": interaction_id})
    if result.deleted_count == 0:
        logger.warning("Interaction not found for deletion: %s", interaction_id)
        raise ValueError(f"Interaction not found: {interaction_id}")
    logger.info("Interaction deleted: %s", interaction_id)
    return {"deleted_count": result.deleted_count}


async def list_interactions(campaign_id: str, skip: int = 0, limit: int = 10) -> list:
    """List all interactions for a specific campaign"""
    db = await get_mongodb()
    campaign_id = str(uuid.UUID(campaign_id))
    cursor = db[CAMPAIGN_INTERACTIONS_COLLECTION].find({"campaign_id": campaign_id}).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)
