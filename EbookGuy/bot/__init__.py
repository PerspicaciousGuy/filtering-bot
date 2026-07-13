from dataclasses import dataclass
from typing import AsyncGenerator

from pyrogram import Client
from pyrogram.types import Message
from info import API_HASH, API_ID, BOT_TOKEN, SESSION
from utils import temp


@dataclass(frozen=True)
class MessageRange:
    chat_id: int | str
    limit: int
    offset: int = 0


class EbookGuyXBot(Client):

    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=150,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def set_self(self):
        temp.BOT = self
    
    async def iter_messages(
        self,
        request: MessageRange,
    ) -> AsyncGenerator[Message, None]:
        """Yield a bounded range of messages in ascending batches."""
        current = request.offset
        while True:
            new_diff = min(200, request.limit - current)
            if new_diff <= 0:
                return
            message_ids = list(range(current, current + new_diff + 1))
            messages = await self.get_messages(request.chat_id, message_ids)
            for message in messages:
                yield message
                current += 1
      
EbookGuyBot = EbookGuyXBot()

multi_clients = {}
work_loads = {}
