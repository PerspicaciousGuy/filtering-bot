import logging

from database.users_chats_db import db

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def handle_add_premium_command(client, message):
    """Admin command to add premium to a user"""
    if len(message.command) < 3:
        return await message.reply_text("Usage: /addpremium <user_id> <days>")
    
    try:
        user_id = int(message.command[1])
        days = int(message.command[2])
        
        new_expiry = await db.set_premium(user_id, days)
        if new_expiry:
            await message.reply_text(f"✅ Premium added!\n\n👤 User: {user_id}\n📅 Days: {days}\n⏰ Expires: {new_expiry.strftime('%d %B %Y, %I:%M %p')}")
            
            # Notify user
            try:
                await client.send_message(
                    user_id,
                    f"🎉 <b>You've been gifted Premium!</b>\n\n📅 <b>Duration:</b> {days} days\n⏰ <b>Valid Until:</b> {new_expiry.strftime('%d %B %Y, %I:%M %p')}\n\n<i>Enjoy unlimited downloads!</i>"
                )
            except Exception:
                pass
        else:
            await message.reply_text("❌ Error adding premium. User may not exist in database.")
    except ValueError:
        await message.reply_text("Invalid user_id or days. Both must be numbers.")

async def handle_remove_premium_command(client, message):
    """Admin command to remove premium from a user"""
    if len(message.command) < 2:
        return await message.reply_text("Usage: /removepremium <user_id>")
    
    try:
        user_id = int(message.command[1])
        
        from database.users_chats_db import db
        await db.col.update_one(
            {'id': int(user_id)},
            {'$set': {'is_premium': False, 'premium_expiry': None}}
        )
        
        await message.reply_text(f"✅ Premium removed from user {user_id}")
    except ValueError:
        await message.reply_text("Invalid user_id. Must be a number.")

async def handle_premium_users_command(client, message):
    """Admin command to list premium users"""
    total_premium = await db.get_premium_stats()
    
    if total_premium == 0:
        return await message.reply_text("No premium users found.")
    
    premium_users = db.col.find({'is_premium': True})
    
    text = f"<b>⭐ Premium Users ({total_premium})</b>\n\n"
    count = 0
    async for user in premium_users:
        if count >= 20:  # Limit to 20 users
            text += f"\n<i>...and {total_premium - 20} more</i>"
            break
        
        user_id = user.get('id')
        name = user.get('name', 'Unknown')
        expiry = user.get('premium_expiry')
        expiry_str = expiry.strftime('%d %b %Y') if expiry else 'N/A'
        
        text += f"• <code>{user_id}</code> - {name} (expires: {expiry_str})\n"
        count += 1
    
    await message.reply_text(text)

async def handle_stars_balance_command(client, message):
    """Admin command to check bot's Star balance and recent transactions"""
    try:
        # Get star transactions
        transactions = await client.get_star_transactions(limit=10)
        
        text = "<b>⭐ Bot Stars Dashboard</b>\n\n"
        
        # Total balance
        if hasattr(transactions, 'star_count'):
            text += f"💰 <b>Current Balance:</b> ⭐ {transactions.star_count}\n\n"
        
        text += "<b>📊 Recent Transactions:</b>\n"
        
        if transactions.transactions:
            for txn in transactions.transactions:
                # Transaction direction
                if txn.source:
                    direction = "📥 IN"
                    user_info = ""
                    if hasattr(txn.source, 'user') and txn.source.user:
                        user_info = f" from {txn.source.user.first_name} ({txn.source.user.id})"
                else:
                    direction = "📤 OUT"
                    user_info = ""
                
                # Format date
                txn_date = txn.date.strftime('%d %b %Y, %I:%M %p') if txn.date else 'N/A'
                
                text += f"\n{direction} ⭐ {txn.amount}{user_info}\n"
                text += f"   📅 {txn_date}\n"
        else:
            text += "\n<i>No transactions found.</i>"
        
        await message.reply_text(text)
        
    except Exception:
        logger.exception("Failed to get star transactions")
        await message.reply_text("Could not fetch star data right now. Please try again later.")

async def handle_stars_history_command(client, message):
    """Admin command to get detailed star transaction history"""
    try:
        limit = 25
        if len(message.command) > 1:
            try:
                limit = min(int(message.command[1]), 100)
            except Exception:
                pass
        
        transactions = await client.get_star_transactions(limit=limit)
        
        text = f"<b>⭐ Star Transaction History (Last {limit})</b>\n\n"
        
        if hasattr(transactions, 'star_count'):
            text += f"💰 <b>Current Balance:</b> ⭐ {transactions.star_count}\n\n"
        
        total_in = 0
        total_out = 0
        
        if transactions.transactions:
            for txn in transactions.transactions:
                if txn.source:
                    total_in += txn.amount
                else:
                    total_out += txn.amount
            
            text += f"📥 <b>Total Received:</b> ⭐ {total_in}\n"
            text += f"📤 <b>Total Withdrawn:</b> ⭐ {total_out}\n"
            text += f"📊 <b>Transactions:</b> {len(transactions.transactions)}\n"
        else:
            text += "<i>No transactions found.</i>"
        
        await message.reply_text(text)
        
    except Exception:
        logger.exception("Failed to get star history")
        await message.reply_text("Could not fetch star history right now. Please try again later.")
