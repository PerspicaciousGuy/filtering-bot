from dataclasses import dataclass

import motor.motor_asyncio
from pymongo.errors import DuplicateKeyError
from info import AUTH_CHANNEL, OTHER_DB_URI


@dataclass(frozen=True)
class JoinRequestUser:
    user_id: int
    first_name: str
    username: str | None
    date: object

class JoinReqs:

    def __init__(self):
        if OTHER_DB_URI:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(OTHER_DB_URI)
            self.db = self.client["JoinReqs"]
            self.col = self.db[str(AUTH_CHANNEL)]
        else:
            self.client = None
            self.db = None
            self.col = None

    def is_active(self):
        return self.client is not None

    def isActive(self):
        """Compatibility alias for the original camel-case API."""
        return self.is_active()

    async def add_user(self, user, *legacy_fields):
        """Store a join request, accepting both request objects and legacy fields."""
        if not isinstance(user, JoinRequestUser):
            first_name, username, date = legacy_fields
            user = JoinRequestUser(user, first_name, username, date)
        try:
            await self.col.insert_one({
                "_id": int(user.user_id),
                "user_id": int(user.user_id),
                "first_name": user.first_name,
                "username": user.username,
                "date": user.date,
            })
        except DuplicateKeyError:
            return

    async def get_user(self, user_id):
        return await self.col.find_one({"user_id": int(user_id)})

    async def get_all_users(self):
        return await self.col.find().to_list(None)

    async def delete_user(self, user_id):
        await self.col.delete_one({"user_id": int(user_id)})

    async def delete_all_users(self):
        await self.col.delete_many({})

    async def get_all_users_count(self):
        return await self.col.count_documents({})
