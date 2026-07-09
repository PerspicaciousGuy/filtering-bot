import re
from pymongo.errors import DuplicateKeyError
import motor.motor_asyncio
from pymongo import MongoClient
from info import DATABASE_NAME, USER_DB_URI, OTHER_DB_URI, CUSTOM_FILE_CAPTION, MELCOW_NEW_USERS, BUTTON_MODE, PROTECT_CONTENT, AUTO_DELETE, MAX_BTN, AUTO_FFILTER
import time
import datetime

 

default_setgs = {
    'button': BUTTON_MODE,
    'file_secure': PROTECT_CONTENT,
    'welcome': MELCOW_NEW_USERS,
    'auto_delete': AUTO_DELETE,
    'auto_ffilter': AUTO_FFILTER,
    'max_btn': MAX_BTN,
    'caption': CUSTOM_FILE_CAPTION,
    'fsub': None
}


class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.grp = self.db.groups
        self.users = self.db.uersz


    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            file_id=None,
            caption=None,
            message_command=None,
            save=False,
            ban_status=dict(
                is_banned=False,
                ban_reason="",
            ),
        )


    def new_group(self, id, title):
        return dict(
            id = id,
            title = title,
            chat_status=dict(
                is_disabled=False,
                reason="",
            ),
            settings=default_setgs
        )
    
    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)
    
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def remove_ban(self, id):
        ban_status = dict(
            is_banned=False,
            ban_reason=''
        )
        await self.col.update_one({'id': id}, {'$set': {'ban_status': ban_status}})
    
    async def ban_user(self, user_id, ban_reason="No Reason"):
        ban_status = dict(
            is_banned=True,
            ban_reason=ban_reason
        )
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        default = dict(
            is_banned=False,
            ban_reason=''
        )
        user = await self.col.find_one({'id':int(id)})
        if not user:
            return default
        return user.get('ban_status', default)

    async def get_all_users(self):
        return self.col.find({})
    

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})


    async def get_banned(self):
        users = self.col.find({'ban_status.is_banned': True})
        chats = self.grp.find({'chat_status.is_disabled': True})
        b_chats = [chat['id'] async for chat in chats]
        b_users = [user['id'] async for user in users]
        return b_users, b_chats
    


    async def add_chat(self, chat, title):
        chat = self.new_group(chat, title)
        await self.grp.insert_one(chat)
    

    async def get_chat(self, chat):
        chat = await self.grp.find_one({'id':int(chat)})
        return False if not chat else chat.get('chat_status')
    

    async def re_enable_chat(self, id):
        chat_status=dict(
            is_disabled=False,
            reason="",
            )
        await self.grp.update_one({'id': int(id)}, {'$set': {'chat_status': chat_status}})
        
    async def update_settings(self, id, settings):
        await self.grp.update_one({'id': int(id)}, {'$set': {'settings': settings}})
        
    
    async def get_settings(self, id):
        chat = await self.grp.find_one({'id':int(id)})
        if chat:
            settings = chat.get('settings', default_setgs)
            # Merge with defaults to ensure all keys exist
            for key, value in default_setgs.items():
                if key not in settings:
                    settings[key] = value
            return settings
        return default_setgs
    

    async def disable_chat(self, chat, reason="No Reason"):
        chat_status=dict(
            is_disabled=True,
            reason=reason,
            )
        await self.grp.update_one({'id': int(chat)}, {'$set': {'chat_status': chat_status}})
    

    async def total_chat_count(self):
        count = await self.grp.count_documents({})
        return count
    

    async def get_all_chats(self):
        return self.grp.find({})


    async def get_db_size(self):
        return (await self.db.command("dbstats"))['dataSize']

    async def get_user(self, user_id):
        user_data = await self.users.find_one({"id": user_id})
        return user_data
            
    async def update_user(self, user_data):
        await self.users.update_one({"id": user_data["id"]}, {"$set": user_data}, upsert=True)



    async def set_thumbnail(self, id, file_id):
        await self.col.update_one({'id': int(id)}, {'$set': {'file_id': file_id}})

    async def get_thumbnail(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('file_id', None)

    async def set_caption(self, id, caption):
        await self.col.update_one({'id': int(id)}, {'$set': {'caption': caption}})

    async def get_caption(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('caption', None)

    async def set_msg_command(self, id, com):
        await self.col.update_one({'id': int(id)}, {'$set': {'message_command': com}})

    async def get_msg_command(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('message_command', None)

    async def set_save(self, id, save):
        await self.col.update_one({'id': int(id)}, {'$set': {'save': save}})

    async def get_save(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('save', False) 
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ⭐ PREMIUM SYSTEM METHODS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def get_premium_status(self, user_id):
        """Get user's premium status and expiry date"""
        user = await self.col.find_one({'id': int(user_id)})
        if not user:
            return False, None
        
        is_premium = user.get('is_premium', False)
        premium_expiry = user.get('premium_expiry', None)
        
        # Check if premium has expired
        if is_premium and premium_expiry:
            if datetime.datetime.now() > premium_expiry:
                # Premium expired, update status
                await self.col.update_one(
                    {'id': int(user_id)},
                    {'$set': {'is_premium': False}}
                )
                return False, premium_expiry
        
        return is_premium, premium_expiry
    
    async def set_premium(self, user_id, days):
        """Set or extend premium for a user"""
        user = await self.col.find_one({'id': int(user_id)})
        if not user:
            return False
        
        current_expiry = user.get('premium_expiry', None)
        now = datetime.datetime.now()
        
        # If user has active premium, extend from current expiry
        if current_expiry and current_expiry > now:
            new_expiry = current_expiry + datetime.timedelta(days=days)
        else:
            # New premium or expired, start from now
            new_expiry = now + datetime.timedelta(days=days)
        
        await self.col.update_one(
            {'id': int(user_id)},
            {'$set': {
                'is_premium': True,
                'premium_expiry': new_expiry
            }}
        )
        return new_expiry
    
    async def get_daily_downloads(self, user_id):
        """Get user's download count for today"""
        user = await self.col.find_one({'id': int(user_id)})
        if not user:
            return 0
        
        last_download_date = user.get('last_download_date', None)
        today = datetime.date.today()
        
        # Reset count if it's a new day
        if last_download_date != str(today):
            await self.col.update_one(
                {'id': int(user_id)},
                {'$set': {'daily_downloads': 0, 'last_download_date': str(today)}}
            )
            return 0
        
        return user.get('daily_downloads', 0)
    
    async def get_user_last_download_time(self, user_id):
        """Get user's last download timestamp (for rate limiting)"""
        user = await self.col.find_one({'id': int(user_id)})
        if not user:
            return None
        return user.get('last_download_time', None)
    
    async def set_user_last_download_time(self, user_id):
        """Update user's last download timestamp"""
        await self.col.update_one(
            {'id': int(user_id)},
            {'$set': {'last_download_time': datetime.datetime.now()}}
        )
    
    async def increment_downloads(self, user_id):
        """Increment download count for today"""
        today = str(datetime.date.today())
        user = await self.col.find_one({'id': int(user_id)})
        
        if not user:
            return 1
        
        last_download_date = user.get('last_download_date', None)
        
        if last_download_date != today:
            # New day, reset to 1
            await self.col.update_one(
                {'id': int(user_id)},
                {'$set': {'daily_downloads': 1, 'last_download_date': today}}
            )
            return 1
        else:
            # Same day, increment
            new_count = user.get('daily_downloads', 0) + 1
            await self.col.update_one(
                {'id': int(user_id)},
                {'$set': {'daily_downloads': new_count}}
            )
            return new_count
    
    async def get_remaining_conversions(self, user_id):
        """Get remaining conversions for today (limit: 3/day for premium)"""
        user = await self.col.find_one({'id': int(user_id)})
        if not user:
            return 3
        today = str(datetime.date.today())
        if user.get('last_conversion_date') != today:
            return 3
        return max(0, 3 - user.get('daily_conversions', 0))

    async def increment_conversions(self, user_id):
        """Increment daily conversion count for user"""
        today = str(datetime.date.today())
        user = await self.col.find_one({'id': int(user_id)})
        if not user:
            return
        if user.get('last_conversion_date') != today:
            await self.col.update_one(
                {'id': int(user_id)},
                {'$set': {'daily_conversions': 1, 'last_conversion_date': today}}
            )
        else:
            await self.col.update_one(
                {'id': int(user_id)},
                {'$inc': {'daily_conversions': 1}, '$set': {'last_conversion_date': today}}
            )

    async def get_premium_stats(self):
        """Get premium user statistics"""
        total_premium = await self.col.count_documents({'is_premium': True})
        return total_premium

    async def get_banned_users_count(self):
        """Get total number of banned users"""
        return await self.col.count_documents({'ban_status.is_banned': True})

    async def get_today_total_downloads(self):
        """Get total downloads across all users for today"""
        today = str(datetime.date.today())
        pipeline = [
            {'$match': {'last_download_date': today}},
            {'$group': {'_id': None, 'total': {'$sum': '$daily_downloads'}}}
        ]
        result = await self.col.aggregate(pipeline).to_list(length=1)
        return result[0]['total'] if result else 0
    

db = Database(USER_DB_URI, DATABASE_NAME)
