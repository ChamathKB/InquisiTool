from datetime import datetime

from pydantic import BaseModel


class KnowledgebaseCollectionResponse(BaseModel):
    collection_id: str
    collection_name: str
    uploaded_at: datetime
