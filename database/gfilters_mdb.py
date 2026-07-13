import logging

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from database.filter_stats import build_filter_stats
from info import DATABASE_NAME, OTHER_DB_URI

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

client = AsyncIOMotorClient(OTHER_DB_URI)
database = client[DATABASE_NAME]


async def find_gfilter(gfilters, name):
    collection = database[str(gfilters)]
    try:
        file = await collection.find_one({"text": name})
        if file is None:
            return None, None, None, None
        return file["reply"], file["btn"], file.get("alert"), file["file"]
    except (KeyError, PyMongoError):
        logger.exception("Failed to find global filter")
        return None, None, None, None


async def get_gfilters(gfilters):
    collection = database[str(gfilters)]
    texts = []
    try:
        async for file in collection.find():
            texts.append(file["text"])
    except (KeyError, PyMongoError):
        logger.exception("Failed to list global filters")
    return texts


async def del_allg(message, gfilters):
    if str(gfilters) not in await database.list_collection_names():
        await message.edit_text("Nothing to Remove !")
        return

    collection = database[str(gfilters)]
    try:
        await collection.drop()
        await message.edit_text("All gfilters has been removed !")
    except PyMongoError:
        logger.exception("Failed to remove all global filters")
        await message.edit_text("Couldn't remove all gfilters !")


gfilter_stats = build_filter_stats(database)
