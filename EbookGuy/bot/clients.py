

import asyncio
import logging

from info import API_HASH, API_ID
from pyrogram import Client
from pyrogram.errors import RPCError
from EbookGuy.util.config_parser import TokenParser
from EbookGuy.bot import multi_clients, work_loads, EbookGuyBot

logger = logging.getLogger(__name__)
CLIENT_SLEEP_THRESHOLD = 5


async def initialize_clients():
    multi_clients[0] = EbookGuyBot
    work_loads[0] = 0
    all_tokens = TokenParser().parse_from_env()
    if not all_tokens:
        logger.info("No additional clients found; using the default client")
        return
    
    async def start_client(client_id, token):
        try:
            logger.info("Starting client %s", client_id)
            if client_id == len(all_tokens):
                await asyncio.sleep(2)
                logger.info("Starting the final additional client")
            client = await Client(
                name=str(client_id),
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=token,
                sleep_threshold=CLIENT_SLEEP_THRESHOLD,
                no_updates=True,
                in_memory=True
            ).start()
            work_loads[client_id] = 0
            return client_id, client
        except RPCError:
            logger.exception("Failed starting client %s", client_id)
    
    clients = await asyncio.gather(*[
        start_client(client_id, token)
        for client_id, token in all_tokens.items()
    ])
    started_clients = (
        client for client in clients if client is not None
    )
    multi_clients.update(dict(started_clients))
    if len(multi_clients) != 1:
        logger.info("Multi-client mode enabled")
    else:
        logger.info("No additional clients initialized; using the default client")
