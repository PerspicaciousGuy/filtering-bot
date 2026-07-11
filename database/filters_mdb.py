

import pymongo
from pymongo.errors import PyMongoError
from info import OTHER_DB_URI, DATABASE_NAME
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

myclient = pymongo.MongoClient(OTHER_DB_URI)
mydb = myclient[DATABASE_NAME]



async def find_filter(group_id, name):
    mycol = mydb[str(group_id)]

    try:
        file = mycol.find_one({"text": name})
        if file is None:
            return None, None, None, None
        return file["reply"], file["btn"], file.get("alert"), file["file"]
    except (KeyError, PyMongoError):
        logger.exception("Failed to find filter")
        return None, None, None, None


async def get_filters(group_id):
    mycol = mydb[str(group_id)]

    texts = []
    query = mycol.find()
    try:
        for file in query:
            text = file['text']
            texts.append(text)
    except (KeyError, PyMongoError):
        logger.exception("Failed to list filters")
    return texts


async def del_all(message, group_id, title):
    if str(group_id) not in mydb.list_collection_names():
        await message.edit_text(f"Nothing to remove in {title}!")
        return

    mycol = mydb[str(group_id)]
    try:
        mycol.drop()
        await message.edit_text(f"All filters from {title} has been removed")
    except PyMongoError:
        logger.exception("Failed to remove all filters")
        await message.edit_text("Couldn't remove all filters from group!")
        return


async def filter_stats():
    collections = mydb.list_collection_names()

    if "CONNECTION" in collections:
        collections.remove("CONNECTION")

    totalcount = 0
    for collection in collections:
        mycol = mydb[collection]
        count = mycol.count()
        totalcount += count

    totalcollections = len(collections)

    return totalcollections, totalcount
