from pyrogram.errors import PeerIdInvalid, RPCError, UserIsBlocked
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from info import CHNL_LNK, GRP_LNK, OWNER_LNK


async def send_all(bot, userid, files, ident, chat_id, user_name, query):
    """Send all files to user directly (no shortlinks)"""
    try:
        for file in files:
            f_caption = file["caption"]
            await bot.send_cached_media(
                chat_id=userid,
                file_id=file["file_id"],
                caption=f_caption,
                protect_content=True if ident == "filep" else False,
                reply_markup=InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton('Support Group', url=GRP_LNK),
                        InlineKeyboardButton('Updates Channel', url=CHNL_LNK)
                    ],[
                        InlineKeyboardButton("Bot Owner", url=OWNER_LNK)
                    ]]
                )
            )
    except UserIsBlocked:
        await query.answer('Unblock the bot mahn !', show_alert=True)
    except PeerIdInvalid:
        await query.answer('Hey, Start Bot First And Click Send All', show_alert=True)
    except RPCError:
        await query.answer('Hey, Start Bot First And Click Send All', show_alert=True)
