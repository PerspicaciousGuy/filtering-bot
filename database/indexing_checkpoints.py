from datetime import datetime

from database.file_collections import checkpoint_col


async def save_checkpoint(chat_id, current_msg, stats):
    """Save indexing progress for later resumption."""
    await checkpoint_col.update_one(
        {"chat_id": chat_id},
        {"$set": {
            "current_msg": current_msg,
            "stats": stats,
            "updated_at": datetime.utcnow(),
        }},
        upsert=True,
    )


async def get_checkpoint(chat_id):
    """Return the saved checkpoint for one channel."""
    return await checkpoint_col.find_one({"chat_id": chat_id})


async def delete_checkpoint(chat_id):
    """Remove a channel's completed or discarded checkpoint."""
    await checkpoint_col.delete_one({"chat_id": chat_id})


async def get_all_checkpoints():
    """Return all active indexing checkpoints."""
    return await checkpoint_col.find().to_list(length=None)
