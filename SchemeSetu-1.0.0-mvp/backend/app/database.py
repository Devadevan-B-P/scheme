"""Database import shim pointing to app.core.database."""
from app.core.database import (
    connect_to_mongo,
    close_mongo_connection,
    get_database,
    get_client,
    init_indexes,
    db_manager,
)
