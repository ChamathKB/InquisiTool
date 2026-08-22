import logging
from contextlib import asynccontextmanager
from pathlib import Path

import aiohttp
import click
import redis.asyncio as redis
import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from qdrant_client import QdrantClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from inquisitool.auth import limiter, require_auth
from inquisitool.constants import LOG_LEVELS, QDRANT_URL, REDIS_URL
from inquisitool.db.mongodb import mongodb
from inquisitool.routes import campaigns, knowledgebases, public, query


def create_app():
    """Application factory"""

    @asynccontextmanager
    async def lifespan(app: FastAPI):

        logging.info("🟢️ Starting up resources...")
        app.state.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        app.state.mongodb = mongodb
        await mongodb.connect()
        app.state.qdrant = QdrantClient(location=QDRANT_URL)
        app.state.session = aiohttp.ClientSession()
        yield
        logging.info("🔴️ Shutting down resources...")
        await app.state.redis_client.aclose()
        await app.state.mongodb.close()
        await app.state.session.close()

    app = FastAPI(lifespan=lifespan)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["X-API-Key", "Content-Type"],
    )
    app.include_router(campaigns.router, prefix="/campaigns", dependencies=[Depends(require_auth)])
    app.include_router(knowledgebases.router, prefix="/knowledgebases", dependencies=[Depends(require_auth)])
    app.include_router(query.router, prefix="/query", dependencies=[Depends(require_auth)])
    app.include_router(public.router, prefix="/public")

    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    return app


@click.group()
def inquisi():
    """Main CLI group for the application."""
    pass


@inquisi.command()
def version() -> None:
    """Display the version of the application."""
    from importlib.metadata import version

    PACKAGE = "inquisitool"
    click.echo(f"InquisiTool v{version(PACKAGE)}")
    return


@inquisi.command()
@click.option("--host", type=str, default="0.0.0.0")
@click.option("--port", type=int, default=8000)
@click.option("--log-level", type=click.Choice(LOG_LEVELS.keys()), default="info")
def run(host: str, port: int, log_level: str) -> None:
    """Main entry point for the inquisitool service"""
    logging.basicConfig(level=LOG_LEVELS[log_level.lower()], format="[*] %(message)s")
    logger = logging.getLogger(__name__)

    try:
        app = create_app()
        logging.info(f"Starting server on {host}:{port}")
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
        )
    except ValidationError as e:
        logger.error(f"❌️ Configuration error: {e}")
        raise click.Abort()
    except Exception as e:
        logger.error(f"❌️ Failed to start service: {e}")
        raise click.Abort()


if __name__ == "__main__":
    inquisi()
