# InquisiTool

AI-powered survey application that generates dynamic, context-aware survey questions using CrewAI agents and semantic search over knowledge bases.




## Features

- Dynamic question generation based on campaign objectives and user responses
- Semantic search over PDF knowledge bases using Qdrant vector database
- Campaign management with configurable question limits and target audiences
- Session-based survey interactions with response tracking

## Tech Stack

- **FastAPI** - Web framework
- **CrewAI** - Multi-agent orchestration
- **MongoDB** - Document storage
- **Qdrant** - Vector database for semantic search
- **Redis** - Caching layer
- **Google Gemini** - LLM and embeddings

## Development Setup

### Prerequisites

- Python 3.10+
- MongoDB
- Qdrant
- Redis

### Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -e .
```

3. Create `.env` file:
```env
GEMINI_API_KEY=your_api_key
LLM_MODEL=gemini-2.5-flash-preview-05-20
EMBEDDING_MODEL=gemini-embedding-exp-03-07
MONGO_URL=mongodb://localhost:27017
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
```

4. Start services:
```bash
# MongoDB
mongod

# Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Redis
redis-server
```

5. Run the application:
```bash
inquisitool run --host 0.0.0.0 --port 8000
```

## Deployment

### Docker Compose (Recommended)

```bash
docker-compose up -d
```

### Manual Deployment

1. Set environment variables
2. Ensure MongoDB, Qdrant, and Redis are accessible
3. Run with production ASGI server:
```bash
gunicorn inquisitool.main:create_app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## API Endpoints

- `POST /campaigns/` - Create campaign
- `GET /campaigns/` - List campaigns
- `POST /knowledgebases/create_collection` - Create knowledge base
- `POST /knowledgebases/upload_docs` - Upload PDF documents
- `POST /query/survey` - Process survey interaction
