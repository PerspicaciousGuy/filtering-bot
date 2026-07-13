import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, Union

from info import LOG_CHANNEL
from EbookGuy.bot import work_loads
from pyrogram import Client, utils, raw
from EbookGuy.util.file_properties import get_file_ids
from pyrogram.session import Session, Auth
from pyrogram.errors import AuthBytesInvalid
from EbookGuy.server.exceptions import FIleNotFound
from pyrogram.file_id import FileId, FileType, ThumbnailSource


@dataclass(frozen=True)
class FileChunkRequest:
    file_id: FileId
    client_index: int
    offset: int
    first_part_cut: int
    last_part_cut: int
    part_count: int
    chunk_size: int


async def _authorize_media_session(client, file_id, media_session):
    for _ in range(6):
        exported = await client.invoke(
            raw.functions.auth.ExportAuthorization(dc_id=file_id.dc_id)
        )
        try:
            await media_session.send(raw.functions.auth.ImportAuthorization(
                id=exported.id,
                bytes=exported.bytes,
            ))
            return
        except AuthBytesInvalid:
            logging.debug("Invalid authorization bytes for DC %s", file_id.dc_id)
    await media_session.stop()
    raise AuthBytesInvalid


async def _create_media_session(client, file_id):
    is_foreign_dc = file_id.dc_id != await client.storage.dc_id()
    auth_key = (
        await Auth(
            client,
            file_id.dc_id,
            await client.storage.test_mode(),
        ).create()
        if is_foreign_dc
        else await client.storage.auth_key()
    )
    media_session = Session(
        client,
        file_id.dc_id,
        auth_key,
        await client.storage.test_mode(),
        is_media=True,
    )
    await media_session.start()
    if is_foreign_dc:
        await _authorize_media_session(client, file_id, media_session)
    return media_session


def _normalize_chunk_request(request, legacy_args):
    if isinstance(request, FileChunkRequest):
        return request
    return FileChunkRequest(request, *legacy_args)


class ByteStreamer:
    def __init__(self, client: Client):
        """A custom class that holds the cache of a specific client and class functions.
        attributes:
            client: the client that the cache is for.
            cached_file_ids: a dict of cached file IDs.
            cached_file_properties: a dict of cached file properties.
        
        functions:
            generate_file_properties: returns the properties for a media of a specific message contained in Tuple.
            generate_media_session: returns the media session for the DC that contains the media file.
            yield_file: yield a file from telegram servers for streaming.
            
        This is a modified version of the <https://github.com/eyaadh/megadlbot_oss/blob/master/mega/telegram/utils/custom_download.py>
        Thanks to Eyaadh <https://github.com/eyaadh>
        """
        self.clean_timer = 30 * 60
        self.client: Client = client
        self.cached_file_ids: Dict[int, FileId] = {}
        asyncio.create_task(self.clean_cache())

    async def get_file_properties(self, id: int) -> FileId:
        """
        Returns the properties of a media of a specific message in a FIleId class.
        if the properties are cached, then it'll return the cached results.
        or it'll generate the properties from the Message ID and cache them.
        """
        if id not in self.cached_file_ids:
            await self.generate_file_properties(id)
            logging.debug(f"Cached file properties for message with ID {id}")
        return self.cached_file_ids[id]
    
    async def generate_file_properties(self, id: int) -> FileId:
        """
        Generates the properties of a media file on a specific message.
        returns ths properties in a FIleId class.
        """
        file_id = await get_file_ids(self.client, LOG_CHANNEL, id)
        logging.debug(f"Generated file ID and Unique ID for message with ID {id}")
        if not file_id:
            logging.debug(f"Message with ID {id} not found")
            raise FIleNotFound
        self.cached_file_ids[id] = file_id
        logging.debug(f"Cached media message with ID {id}")
        return self.cached_file_ids[id]

    async def generate_media_session(self, client: Client, file_id: FileId) -> Session:
        """Return or create the media session for the file's data center."""
        media_session = client.media_sessions.get(file_id.dc_id, None)
        if media_session is None:
            media_session = await _create_media_session(client, file_id)
            logging.debug("Created media session for DC %s", file_id.dc_id)
            client.media_sessions[file_id.dc_id] = media_session
        else:
            logging.debug("Using cached media session for DC %s", file_id.dc_id)
        return media_session


    @staticmethod
    async def get_location(file_id: FileId) -> Union[raw.types.InputPhotoFileLocation,
                                                     raw.types.InputDocumentFileLocation,
                                                     raw.types.InputPeerPhotoFileLocation,]:
        """
        Returns the file location for the media file.
        """
        file_type = file_id.file_type

        if file_type == FileType.CHAT_PHOTO:
            if file_id.chat_id > 0:
                peer = raw.types.InputPeerUser(
                    user_id=file_id.chat_id, access_hash=file_id.chat_access_hash
                )
            else:
                if file_id.chat_access_hash == 0:
                    peer = raw.types.InputPeerChat(chat_id=-file_id.chat_id)
                else:
                    peer = raw.types.InputPeerChannel(
                        channel_id=utils.get_channel_id(file_id.chat_id),
                        access_hash=file_id.chat_access_hash,
                    )

            location = raw.types.InputPeerPhotoFileLocation(
                peer=peer,
                volume_id=file_id.volume_id,
                local_id=file_id.local_id,
                big=file_id.thumbnail_source == ThumbnailSource.CHAT_PHOTO_BIG,
            )
        elif file_type == FileType.PHOTO:
            location = raw.types.InputPhotoFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size,
            )
        else:
            location = raw.types.InputDocumentFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size,
            )
        return location

    async def _stream_chunks(self, media_session, request):
        location = await self.get_location(request.file_id)
        current_part = 1
        offset = request.offset
        while current_part <= request.part_count:
            result = await media_session.send(raw.functions.upload.GetFile(
                location=location,
                offset=offset,
                limit=request.chunk_size,
            ))
            if not isinstance(result, raw.types.upload.File) or not result.bytes:
                return
            if request.part_count == 1:
                yield result.bytes[request.first_part_cut:request.last_part_cut]
            elif current_part == 1:
                yield result.bytes[request.first_part_cut:]
            elif current_part == request.part_count:
                yield result.bytes[:request.last_part_cut]
            else:
                yield result.bytes
            current_part += 1
            offset += request.chunk_size

    async def yield_file(self, request, *legacy_args) -> Union[str, None]:
        """Yield requested byte chunks, accepting the original positional API."""
        request = _normalize_chunk_request(request, legacy_args)
        client = self.client
        work_loads[request.client_index] += 1
        logging.debug("Starting file stream with client %s", request.client_index)
        try:
            session = await self.generate_media_session(client, request.file_id)
            async for chunk in self._stream_chunks(session, request):
                yield chunk
        except (TimeoutError, AttributeError):
            logging.getLogger(__name__).debug(
                "Custom download worker did not return a usable result",
                exc_info=True,
            )
        finally:
            logging.debug("Finished file stream for client %s", request.client_index)
            work_loads[request.client_index] -= 1

    
    async def clean_cache(self) -> None:
        """
        function to clean the cache to reduce memory usage
        """
        while True:
            await asyncio.sleep(self.clean_timer)
            self.cached_file_ids.clear()
            logging.debug("Cleaned the cache")
