import motor.motor_asyncio

from info import DATABASE_NAME, USER_DB_URI
from database.global_settings_db import GlobalSettingsMixin
from database.users_chats_premium_db import PremiumUsageMixin
from database.users_chats_settings_db import ChatSettingsMixin
from database.users_chats_user_db import UserRecordsMixin


class Database(
    PremiumUsageMixin,
    UserRecordsMixin,
    ChatSettingsMixin,
    GlobalSettingsMixin,
):
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.grp = self.db.groups
        self.users = self.db.uersz
        self.global_settings = self.db.global_settings
        self.global_settings_audit = self.db.global_settings_audit

db = Database(USER_DB_URI, DATABASE_NAME)
