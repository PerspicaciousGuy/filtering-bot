from database.users_chats_db import db


async def get_settings(group_id):
    settings = await db.get_settings(group_id)
    return settings

async def save_group_settings(group_id, key, value):
    current = await get_settings(group_id)
    current.update({key: value})
    await db.update_settings(group_id, current)
