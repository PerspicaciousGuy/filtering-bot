import motor.motor_asyncio

from info import DATABASE_NAME, USER_DB_URI
from database.users_chats_premium_db import PremiumUsageMixin
from database.users_chats_settings_db import ChatSettingsMixin, default_setgs
from database.users_chats_user_db import UserRecordsMixin


class Database(PremiumUsageMixin, UserRecordsMixin, ChatSettingsMixin):
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.grp = self.db.groups
        self.users = self.db.uersz

db = Database(USER_DB_URI, DATABASE_NAME)
