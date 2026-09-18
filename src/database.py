import os
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import PyMongoError


def _setting(name: str, default: str = "") -> str:

    value = os.environ.get(name)

    if value:
        return value

    try:
        value = st.secrets.get(name)

        if value:
            return str(value)

    except Exception:
        pass

    return default


MONGODB_URI = _setting("MONGODB_URI")
DB_NAME = _setting("GRADESENSE_DB_NAME", "gradesense")

_client = None
_db = None
_connection_error = ""


def get_db():

    global _client, _db, _connection_error

    if not MONGODB_URI:
        _connection_error = "MONGODB_URI is not configured."
        raise RuntimeError(_connection_error)

    if _db is None:

        _client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
        )

        _client.admin.command("ping")

        _db = _client[DB_NAME]

        _db.users.create_index(
            "username",
            unique=True
        )

        _db.users.create_index(
            "email",
            unique=True
        )

        _db.results.create_index(
            "created_at"
        )

        _db.results.create_index(
            "username"
        )

        _db.logs.create_index(
            "timestamp"
        )

    return _db


def check_connection() -> bool:

    global _client, _db, _connection_error

    try:

        get_db().client.admin.command("ping")

        _connection_error = ""

        return True

    except (
        PyMongoError,
        RuntimeError,
        OSError
    ) as error:

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

    return (
        _connection_error
        or "MongoDB connection is unavailable."
    )
