


import pymongo
from pymongo.errors import PyMongoError
from info import OTHER_DB_URI, DATABASE_NAME
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

myclient = pymongo.MongoClient(OTHER_DB_URI)
mydb = myclient[DATABASE_NAME]



async def find_gfilter(gfilters, name):
    mycol = mydb[str(gfilters)]

    try:
        file = mycol.find_one({"text": name})
        if file is None:
            return None, None, None, None
        return file["reply"], file["btn"], file.get("alert"), file["file"]
    except (KeyError, PyMongoError):
        logger.exception("Failed to find global filter")
        return None, None, None, None


async def get_gfilters(gfilters):
    mycol = mydb[str(gfilters)]

    texts = []
    query = mycol.find()
    try:
        for file in query:
            text = file['text']
            texts.append(text)
    except (KeyError, PyMongoError):
        logger.exception("Failed to list global filters")
    return texts


async def del_allg(message, gfilters):
    if str(gfilters) not in mydb.list_collection_names():
        await message.edit_text("Nothing to Remove !")
        return

    mycol = mydb[str(gfilters)]
    try:
        mycol.drop()
        await message.edit_text(f"All gfilters has been removed !")
    except PyMongoError:
        logger.exception("Failed to remove all global filters")
        await message.edit_text("Couldn't remove all gfilters !")
        return

async def gfilter_stats():
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
