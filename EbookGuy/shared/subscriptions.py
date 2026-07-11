import logging

from pyrogram import enums
from pyrogram.errors import RPCError, UserNotParticipant
from pyrogram.types import InlineKeyboardButton
from pymongo.errors import PyMongoError

from database.join_reqs import JoinReqs
from info import AUTH_CHANNEL, REQUEST_TO_JOIN_MODE

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
join_db = JoinReqs


async def pub_is_subscribed(bot, query, channel):
    btn = []
    for id in channel:
        chat = await bot.get_chat(int(id))
        try:
            await bot.get_chat_member(id, query.from_user.id)
        except UserNotParticipant:
            btn.append(
                [InlineKeyboardButton(f'Join {chat.title}', url=chat.invite_link)]
            )
        except RPCError:
            logger.warning("Failed to check public-channel subscription", exc_info=True)
    return btn


async def is_subscribed(bot, query):
    if REQUEST_TO_JOIN_MODE == True and join_db().isActive():
        try:
            user = await join_db().get_user(query.from_user.id)
            if user and user["user_id"] == query.from_user.id:
                return True
            else:
                try:
                    user_data = await bot.get_chat_member(AUTH_CHANNEL, query.from_user.id)
                except UserNotParticipant:
                    logger.debug("User has not joined the force-subscription channel")
                except RPCError:
                    logger.exception("Failed to check force-subscription member status")
                else:
                    if user_data.status != enums.ChatMemberStatus.BANNED:
                        return True
        except (PyMongoError, RPCError):
            logger.exception("Failed to validate request-to-join subscription")
            return False
    else:
        try:
            user = await bot.get_chat_member(AUTH_CHANNEL, query.from_user.id)
        except UserNotParticipant:
            logger.debug("User has not joined the subscription channel")
        except RPCError:
            logger.exception("Failed to check subscription member status")
        else:
            if user.status != enums.ChatMemberStatus.BANNED:
                return True
        return False
