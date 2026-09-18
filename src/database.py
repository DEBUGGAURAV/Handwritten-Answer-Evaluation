import os
import datetime
import hashlib
import re
import random
import secrets
from typing import Optional, List

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

import email_utils

load_dotenv()


def _setting(name: str, default: str = "") -> str:
    """
    Read configuration from:
    1. Environment variables
    2. Streamlit Cloud Secrets
    3. Default value
    """

    # Local / server environment variable
    value = os.environ.get(name)
    if value:
        return str(value).strip()

    # Streamlit Cloud Secrets
    try:
        import streamlit as st

        if name in st.secrets:
            value = st.secrets[name]

            if value is not None and str(value).strip():
                return str(value).strip()

    except Exception:
        pass

    return default


# MongoDB configuration
MONGODB_URI = _setting("MONGODB_URI")
DB_NAME = _setting("GRADESENSE_DB_NAME", "gradesense")

_client = None
_db = None
_connection_error = ""


def get_db():
    global _client, _db, _connection_error

    # Check MongoDB URI
    if not MONGODB_URI:
        _connection_error = (
            "MONGODB_URI is not configured. "
            "Please add MONGODB_URI in Streamlit Cloud → "
            "Settings → Secrets."
        )
        raise RuntimeError(_connection_error)

    # Reuse existing connection
    if _db is not None:
        return _db

    try:
        _client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
        )

        # Test connection
        _client.admin.command("ping")

        # Select database
        _db = _client[DB_NAME]

        # Create indexes
        _db.users.create_index("username", unique=True)
        _db.users.create_index("email", unique=True)

        _db.results.create_index("created_at")
        _db.results.create_index("username")

        _db.logs.create_index("timestamp")

        return _db

    except (PyMongoError, RuntimeError, OSError) as error:
        _connection_error = f"MongoDB connection failed: {error}"

        if _client is not None:
            try:
                _client.close()
            except Exception:
                pass

        _client = None
        _db = None

        raise RuntimeError(_connection_error)


def check_connection() -> bool:
    """
    Check whether MongoDB is available.
    """

    global _client, _db, _connection_error

    try:
        db = get_db()

        db.client.admin.command("ping")

        _connection_error = ""

        return True

    except (PyMongoError, RuntimeError, OSError) as error:

        _connection_error = str(error)

        if _client is not None:
            try:
                _client.close()
            except Exception:
                pass

        _client = None
        _db = None

        return False


def connection_error() -> str:
    """
    Return the latest MongoDB connection error.
    """

    return _connection_error or "MongoDB connection is unavailable."
