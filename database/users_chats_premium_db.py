import datetime


class PremiumUsageMixin:
    async def ensure_premium_expiry_index(self):
        """Create the index used by the premium expiry worker."""
        await self.col.create_index([
            ('is_premium', 1),
            ('premium_expiry', 1),
        ])

    def get_expiring_premium_users(self, cutoff):
        """Return active premium users expiring by the supplied cutoff."""
        now = datetime.datetime.now()
        return self.col.find(
            {
                'is_premium': True,
                'premium_expiry': {'$gt': now, '$lte': cutoff},
            },
            {
                'id': 1,
                'premium_expiry': 1,
                'premium_expiry_notified_for': 1,
            },
        )

    async def mark_premium_expiry_notified(self, user_id, expiry):
        """Record the expiry timestamp for which a warning was sent."""
        await self.col.update_one(
            {'id': int(user_id)},
            {'$set': {'premium_expiry_notified_for': expiry}},
        )

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

    async def get_remaining_conversions(self, user_id, daily_limit):
        """Get remaining conversions for the configured daily limit."""
        if daily_limit == 0:
            return -1
        user = await self.col.find_one({'id': int(user_id)})
        if not user:
            return daily_limit
        today = str(datetime.date.today())
        if user.get('last_conversion_date') != today:
            return daily_limit
        return max(0, daily_limit - user.get('daily_conversions', 0))

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
