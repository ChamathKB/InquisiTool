import logging
import os

from dotenv import load_dotenv

load_dotenv()


LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash-preview-05-20")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-exp-03-07")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "agentic_rag_db")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}
