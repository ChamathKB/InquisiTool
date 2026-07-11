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
- **Redis** - Caching and rate limiting
- **Google Gemini** - LLM and embeddings
- **Keycloak** - Authentication and authorization (OIDC / OAuth2)

## Development Setup

### Prerequisites

- Python 3.10+
- MongoDB
- Qdrant
- Redis
- Keycloak

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
    KEYCLOAK_URL=http://localhost:8080
    KEYCLOAK_REALM=inquisitool
    KEYCLOAK_CLIENT_ID=inquisitool-api
    KEYCLOAK_CLIENT_SECRET=your_client_secret
    ```

4. Start services:

    ```bash
    # MongoDB
    mongod

    # Qdrant
    docker run -p 6333:6333 qdrant/qdrant

    # Redis
    redis-server

    # Keycloak (with Postgres backend)
    docker-compose up -d keycloak
    ```

5. Set up Keycloak realm and client — see [docs/Keycloak_Auth.md](docs/Keycloak_Auth.md) for the full steps.

6. Run the application:

    ```bash
    inquisitool run --host 0.0.0.0 --port 8000
    ```

## Authentication

All API endpoints require a valid Bearer token issued by Keycloak. See [docs/Keycloak_Auth.md](docs/Keycloak_Auth.md) for setup details.

To get a token during development (when the frontend is not running):

```bash
# prints the full token + a ready-to-use curl example
python scripts/get_token.py

# raw token only — useful for piping
export TOKEN=$(python scripts/get_token.py --raw)
curl http://localhost:8000/campaigns/ -H "Authorization: Bearer $TOKEN"
```

## Deployment

### Docker Compose (Recommended)

```bash
docker-compose up -d
```

Includes: MongoDB, Redis, Qdrant, Keycloak (+ Postgres backend).

### Manual Deployment

1. Set environment variables
2. Ensure MongoDB, Qdrant, Redis, and Keycloak are accessible
3. Run with production ASGI server:

    ```bash
    gunicorn inquisitool.main:create_app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    ```

## API Endpoints

All endpoints require `Authorization: Bearer <token>`.

- `POST /campaigns/` - Create campaign
- `GET /campaigns/` - List campaigns
- `POST /knowledgebases/create_collection` - Create knowledge base
- `POST /knowledgebases/upload_docs` - Upload PDF documents
- `POST /query/survey` - Process survey interaction _(rate limited: 30 req/min)_

## Docs

- [Keycloak Auth](docs/Keycloak_Auth.md) — auth setup, realm/client config, production checklist
- [Rate Limits](docs/Rate_Limits.md) — current limits, how to add more, switching to user-based limiting
- [Redis Usage](docs/Redis_Usage.md) — caching strategy and monitoring
