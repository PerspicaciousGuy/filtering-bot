"""Indexes required by high-frequency bot operations."""

import asyncio

from database.file_collections import (
    active_file_collections,
    checkpoint_col,
)
from database.users_chats_db import db


async def ensure_core_indexes():
    """Create lookup indexes used by downloads, users, and checkpoints."""
    operations = [
        db.col.create_index("id", unique=True, name="user_id_unique"),
        checkpoint_col.create_index(
            "chat_id",
            unique=True,
            name="checkpoint_chat_id_unique",
        ),
    ]
    for collection in active_file_collections():
        operations.extend([
            collection.create_index(
                "file_id",
                unique=True,
                name="file_id_unique",
            ),
            collection.create_index(
                "file_name",
                name="file_name_lookup",
            ),
        ])
    await asyncio.gather(*operations)
