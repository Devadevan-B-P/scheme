"""
Database layer using PyMongo Async.

Architecture Directives:
  - Worker-local AsyncMongoClient instance per FastAPI event loop
  - ServerApi("1") enabled for MongoDB Atlas compatibility
  - Idempotent index initialization on boot (TTL on expires_at, 2dsphere on partners)
"""

import asyncio
import logging
from typing import Optional
from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    client: Optional[AsyncMongoClient] = None
    db: Optional[AsyncDatabase] = None


db_manager = DatabaseManager()


async def connect_to_mongo() -> None:
    """Initialize worker-local AsyncMongoClient and connect to database."""
    try:
        current_loop = asyncio.get_running_loop()
        if db_manager.client is not None:
            client_loop = getattr(db_manager.client, "_loop", None)
            if client_loop is not None and client_loop != current_loop:
                db_manager.client = None
                db_manager.db = None
            else:
                return

        logger.info("Connecting to MongoDB via PyMongo Async at %s", settings.MONGODB_URI)
        client = AsyncMongoClient(
            settings.MONGODB_URI,
            server_api=ServerApi("1"),
            serverSelectionTimeoutMS=2000,
        )

        # Verify connectivity
        await client.admin.command("ping")
        db_manager.client = client
        db_manager.db = client[settings.MONGODB_DB_NAME]
        logger.info("Successfully connected to MongoDB (%s)", settings.MONGODB_DB_NAME)

        # Idempotently initialize indexes
        await init_indexes(db_manager.db)

        # Initialize Beanie Document Models
        await init_beanie_models(db_manager.db)
    except Exception as exc:
        db_manager.client = None
        db_manager.db = None
        logger.warning(
            "Could not connect to MongoDB (%s). Operating in degraded mode if offline: %s",
            settings.MONGODB_URI,
            exc,
        )



async def init_indexes(db: AsyncDatabase) -> None:
    """Idempotently create required indexes without dropping existing ones."""
    try:
        # 1. Geospatial index on channel_partners / partners
        partners_col = db["partners"]
        await partners_col.create_index([("location", "2dsphere")])
        logger.info("Ensured 2dsphere index on partners collection")

        # 2. Absolute 24-hour TTL index on sessions.expires_at
        sessions_col = db["sessions"]
        await sessions_col.create_index(
            "expires_at",
            expireAfterSeconds=0,
            name="session_expires_at_ttl"
        )
        logger.info("Ensured absolute TTL index on sessions.expires_at")

        # 3. TTL index on ocr_confirmations.expires_at
        ocr_col = db["ocr_confirmations"]
        await ocr_col.create_index(
            "expires_at",
            expireAfterSeconds=0,
            name="ocr_token_expires_at_ttl"
        )
        logger.info("Ensured TTL index on ocr_confirmations.expires_at")

        # 4. Audit indexes
        audit_col = db["audit_logs"]
        await audit_col.create_index([("sequence_id", 1)], unique=True, sparse=True)
        await audit_col.create_index([("session_id", 1)])
        logger.info("Ensured sequence and session indexes on audit_logs")

        # 5. Audit chain heads
        heads_col = db["audit_chain_heads"]
        await heads_col.create_index([("chain_id", 1)], unique=True)
        logger.info("Ensured unique chain_id index on audit_chain_heads")

        # 6. Schemes index
        schemes_col = db["schemes"]
        await schemes_col.create_index([("scheme_id", 1)], unique=True)
        logger.info("Ensured unique scheme_id index on schemes")

    except Exception as err:
        logger.warning("Index initialization notice (may be read-only or index exists): %s", err)


async def init_beanie_models(db: AsyncDatabase) -> None:
    """Initialize Beanie document models on the connected MongoDB instance."""
    try:
        from beanie import init_beanie
        from app.models.user import User
        from app.models.beneficiary import BeneficiaryProfile
        from app.models.partner import ChannelPartner
        from app.models.scraper import (
            SchemeSource,
            ScrapeJob,
            ScrapedScheme,
            SchemeVersion,
            ScrapeChange,
            AuditLog,
        )

        await init_beanie(
            database=db,
            document_models=[
                User,
                BeneficiaryProfile,
                ChannelPartner,
                SchemeSource,
                ScrapeJob,
                ScrapedScheme,
                SchemeVersion,
                ScrapeChange,
                AuditLog,
            ],
        )
        logger.info("Successfully initialized Beanie document models")
    except Exception as exc:
        logger.warning("Beanie model initialization warning: %s", exc)


async def init_db() -> None:
    """Ensure database connection and Beanie models are initialized."""
    try:
        current_loop = asyncio.get_running_loop()
        if db_manager.client is not None:
            client_loop = getattr(db_manager.client, "_loop", None)
            if client_loop is not None and client_loop != current_loop:
                db_manager.client = None
                db_manager.db = None
    except Exception:
        pass

    if db_manager.db is None:
        await connect_to_mongo()


async def close_mongo_connection() -> None:
    """Close MongoDB connection pool."""
    if db_manager.client is not None:
        logger.info("Closing MongoDB connection")
        await db_manager.client.close()
        db_manager.client = None
        db_manager.db = None


def get_database() -> Optional[AsyncDatabase]:
    """Return active AsyncDatabase instance."""
    return db_manager.db


def get_client() -> Optional[AsyncMongoClient]:
    """Return active AsyncMongoClient instance."""
    return db_manager.client

