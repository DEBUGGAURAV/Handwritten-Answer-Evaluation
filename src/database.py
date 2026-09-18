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
    value = os.environ.get(name)

    if value:
        return value

    try:
        import streamlit as st

        value = st.secrets.get(name)

        if value:
            return str(value)

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

    if not MONGODB_URI:
        _connection_error = (
            "MONGODB_URI is not configured. "
            "Add it to a local .env file or Streamlit Cloud secrets."
        )
        raise RuntimeError(_connection_error)

    if _db is None:

        _client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
        )

        # Test MongoDB connection
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
