# -*- coding: utf-8 -*-
"""
mongo.py
--------
MongoDB connection and collection accessors with graceful fallback
when MongoDB is not reachable locally.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

log = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "flood_vulnerability")

_client: Optional[Any] = None
_db: Optional[Any] = None


def get_db():
    """
    Returns the database handle, or None if MongoDB is unavailable.
    Does not crash the application if MongoDB is down.
    """
    global _client, _db
    if not PYMONGO_AVAILABLE:
        log.warning("pymongo is not installed; running in database-disabled mode.")
        return None

    if _db is not None:
        return _db

    try:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        # Verify connection
        _client.admin.command("ping")
        _db = _client[MONGO_DB_NAME]
        log.info("Successfully connected to MongoDB at %s (db=%s)", MONGO_URI, MONGO_DB_NAME)
        return _db
    except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as exc:
        log.warning("MongoDB unavailable at %s: %s. Continuing in offline mode.", MONGO_URI, exc)
        _client = None
        _db = None
        return None


def is_db_connected() -> bool:
    """Returns True if MongoDB is reachable, False otherwise."""
    db = get_db()
    if db is None:
        return False
    try:
        _client.admin.command("ping")
        return True
    except Exception:
        return False


def get_predictions_collection():
    db = get_db()
    return db["predictions"] if db is not None else None
