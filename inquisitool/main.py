import logging
from contextlib import asynccontextmanager

import aiohttp
import click
import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI
from pydantic import ValidationError
from qdrant_client import QdrantClient

from inquisitool.constants import LOG_LEVELS, QDRANT_URL, REDIS_URL
from inquisitool.db import mongodb
from inquisitool.routes import campaings, knowledgebases


def create_app():
    """Application factory"""

    @asynccontextmanager
    async def lifespan(app: FastAPI):

        logging.info("🟢️ Starting up resources...")
        app.state.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        app.state.mongodb = mongodb
        app.state.qdrant = QdrantClient(location=QDRANT_URL)
        app.state.session = aiohttp.ClientSession()
        yield
        logging.info("🔴️ Shutting down resources...")
        await app.state.redis_client.aclose()
        await app.state.mongodb.close()
        await app.state.session.close()

    app = FastAPI(lifespan=lifespan)
    app.include_router(campaings.router, prefix="/campaings")
    app.include_router(knowledgebases.router, prefix="/knowledgebases")
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
            reload=True,
            log_level=log_level,
            factory=True,
        )
    except ValidationError as e:
        logger.error(f"❌️ Configuration error: {e}")
        raise click.Abort()
    except Exception as e:
        logger.error(f"❌️ Failed to start service: {e}")
        raise click.Abort()


if __name__ == "__main__":
    inquisi()
