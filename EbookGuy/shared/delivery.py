from dataclasses import dataclass

from pyrogram.errors import PeerIdInvalid, RPCError, UserIsBlocked
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from info import CHNL_LNK, OWNER_LNK
from EbookGuy.shared.global_settings import get_global_settings


@dataclass(frozen=True)
class SendAllRequest:
    bot: object
    user_id: int
    files: list
    identifier: str
    query: object


def _normalize_request(request, legacy_args):
    if isinstance(request, SendAllRequest):
        return request
    user_id, files, identifier, _chat_id, _user_name, query = legacy_args
    return SendAllRequest(request, user_id, files, identifier, query)


async def send_all(request, *legacy_args):
    """Send all files directly while preserving the original positional API."""
    request = _normalize_request(request, legacy_args)
    settings = await get_global_settings()
    try:
        for file in request.files:
            await request.bot.send_cached_media(
                chat_id=request.user_id,
                file_id=file["file_id"],
                caption=file["caption"],
                protect_content=bool(settings["protect_content"]),
                reply_markup=InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton(
                            'Support Group',
                            url=str(settings["support_url"]),
                        ),
                        InlineKeyboardButton('Updates Channel', url=CHNL_LNK)
                    ],[
                        InlineKeyboardButton("Bot Owner", url=OWNER_LNK)
                    ]]
                )
            )
    except UserIsBlocked:
        await request.query.answer(
            "Unblock the bot mahn !",
            show_alert=True,
        )
    except (PeerIdInvalid, RPCError):
        await request.query.answer(
            "Hey, Start Bot First And Click Send All",
            show_alert=True,
        )
