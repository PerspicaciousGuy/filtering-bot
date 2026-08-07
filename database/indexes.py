"""Indexes required by high-frequency bot operations."""

import asyncio
from dataclasses import dataclass

from database.file_collections import (
    active_file_collections,
    checkpoint_col,
)
from database.users_chats_db import db


@dataclass(frozen=True)
class IndexRequirement:
    """One lookup index the bot needs, independent of its stored name."""

    collection: object
    keys: tuple[tuple[str, int], ...]
    name: str
    is_unique: bool = False


async def _ensure_index(requirement):
    existing_indexes = await requirement.collection.index_information()
    for existing_name, details in existing_indexes.items():
        if tuple(details["key"]) == requirement.keys:
            return existing_name
    return await requirement.collection.create_index(
        list(requirement.keys),
        unique=requirement.is_unique,
        name=requirement.name,
    )


async def ensure_core_indexes():
    """Create lookup indexes used by downloads, users, and checkpoints."""
    requirements = [
        IndexRequirement(
            db.col,
            (("id", 1),),
            "user_id_unique",
            is_unique=True,
        ),
        IndexRequirement(
            checkpoint_col,
            (("chat_id", 1),),
            "checkpoint_chat_id_unique",
            is_unique=True,
        ),
    ]
    for collection in active_file_collections():
        requirements.extend([
            IndexRequirement(
                collection,
                (("file_id", 1),),
                "file_id_unique",
                is_unique=True,
            ),
            IndexRequirement(
                collection,
                (("file_name", 1),),
                "file_name_lookup",
            ),
        ])
    await asyncio.gather(*(
        _ensure_index(requirement)
        for requirement in requirements
    ))
