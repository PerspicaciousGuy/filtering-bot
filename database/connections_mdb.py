import logging

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from info import DATABASE_NAME, OTHER_DB_URI

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

client = AsyncIOMotorClient(OTHER_DB_URI)
database = client[DATABASE_NAME]
collection = database["CONNECTION"]


async def add_connection(group_id, user_id):
    query = await collection.find_one(
        {"_id": user_id},
        {"_id": 0, "active_group": 0},
    )
    if query is not None:
        group_ids = [item["group_id"] for item in query["group_details"]]
        if group_id in group_ids:
            return False

    group_details = {"group_id": group_id}
    data = {
        "_id": user_id,
        "group_details": [group_details],
        "active_group": group_id,
    }

    if query is None:
        try:
            await collection.insert_one(data)
            return True
        except PyMongoError:
            logger.exception("Failed to add connection")
    else:
        try:
            await collection.update_one(
                {"_id": user_id},
                {
                    "$push": {"group_details": group_details},
                    "$set": {"active_group": group_id},
                },
            )
            return True
        except PyMongoError:
            logger.exception("Failed to update connection")


async def active_connection(user_id):
    query = await collection.find_one(
        {"_id": user_id},
        {"_id": 0, "group_details": 0},
    )
    if not query:
        return None

    group_id = query["active_group"]
    return int(group_id) if group_id is not None else None


async def all_connections(user_id):
    query = await collection.find_one(
        {"_id": user_id},
        {"_id": 0, "active_group": 0},
    )
    if query is None:
        return None
    return [item["group_id"] for item in query["group_details"]]


async def if_active(user_id, group_id):
    query = await collection.find_one(
        {"_id": user_id},
        {"_id": 0, "group_details": 0},
    )
    return query is not None and query["active_group"] == group_id


async def make_active(user_id, group_id):
    update = await collection.update_one(
        {"_id": user_id},
        {"$set": {"active_group": group_id}},
    )
    return update.modified_count != 0


async def make_inactive(user_id):
    update = await collection.update_one(
        {"_id": user_id},
        {"$set": {"active_group": None}},
    )
    return update.modified_count != 0


async def delete_connection(user_id, group_id):
    try:
        update = await collection.update_one(
            {"_id": user_id},
            {"$pull": {"group_details": {"group_id": group_id}}},
        )
        if update.modified_count == 0:
            return False

        query = await collection.find_one({"_id": user_id}, {"_id": 0})
        if query["group_details"]:
            if query["active_group"] == group_id:
                previous_group_id = query["group_details"][-1]["group_id"]
                await collection.update_one(
                    {"_id": user_id},
                    {"$set": {"active_group": previous_group_id}},
                )
        else:
            await collection.update_one(
                {"_id": user_id},
                {"$set": {"active_group": None}},
            )
        return True
    except (KeyError, TypeError, PyMongoError):
        logger.exception("Failed to delete connection")
        return False
