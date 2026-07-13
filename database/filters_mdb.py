import logging

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from database.filter_stats import build_filter_stats
from info import DATABASE_NAME, OTHER_DB_URI

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

client = AsyncIOMotorClient(OTHER_DB_URI)
database = client[DATABASE_NAME]


async def find_filter(group_id, name):
    collection = database[str(group_id)]
    try:
        file = await collection.find_one({"text": name})
        if file is None:
            return None, None, None, None
        return file["reply"], file["btn"], file.get("alert"), file["file"]
    except (KeyError, PyMongoError):
        logger.exception("Failed to find filter")
        return None, None, None, None


async def get_filters(group_id):
    collection = database[str(group_id)]
    texts = []
    try:
        async for file in collection.find():
            texts.append(file["text"])
    except (KeyError, PyMongoError):
        logger.exception("Failed to list filters")
    return texts


async def del_all(message, group_id, title):
    if str(group_id) not in await database.list_collection_names():
        await message.edit_text(f"Nothing to remove in {title}!")
        return

    collection = database[str(group_id)]
    try:
        await collection.drop()
        await message.edit_text(f"All filters from {title} has been removed")
    except PyMongoError:
        logger.exception("Failed to remove all filters")
        await message.edit_text("Couldn't remove all filters from group!")


filter_stats = build_filter_stats(database)
