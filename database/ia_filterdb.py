

import base64
import logging
import re
from struct import pack
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError, PyMongoError
from database.file_collections import col, sec_col
from database import indexing_checkpoints as checkpoint_store
from database.search_repository import SearchRequest, get_search_results
from info import (
    ALLOWED_EXTENSIONS,
    FILTER_BY_EXTENSION,
    MULTIPLE_DATABASE,
    USE_CAPTION_FILTER,
)

logger = logging.getLogger(__name__)

save_checkpoint = checkpoint_store.save_checkpoint
get_checkpoint = checkpoint_store.get_checkpoint
delete_checkpoint = checkpoint_store.delete_checkpoint
get_all_checkpoints = checkpoint_store.get_all_checkpoints

async def save_file(media):
    """Save file in the database."""
    
    file_id = unpack_new_file_id(media.file_id)
    file_name = clean_file_name(media.file_name)
    
    file = {
        'file_id': file_id,
        'file_name': file_name,
        'file_size': media.file_size,
        'caption': media.caption.html if media.caption else None
    }

    if await is_file_already_saved(file_id, file_name):
        return False, 0

    try:
        await col.insert_one(file)
        logger.info("%s is successfully saved", file_name)
        return True, 1
    except DuplicateKeyError:
        logger.info("%s is already saved", file_name)
        return False, 0
    except PyMongoError:
        if MULTIPLE_DATABASE:
            try:
                await sec_col.insert_one(file)
                logger.info("%s is successfully saved", file_name)
                return True, 1
            except DuplicateKeyError:
                logger.info("%s is already saved", file_name)
                return False, 0
        else:
            logger.error("The file database is full and no secondary database is configured")
            return False, 2

def clean_file_name(file_name):
    """Clean and format the file name."""
    file_name = re.sub(r"(_|\-|\.|\+)", " ", str(file_name)) 
    unwanted_chars = ['[', ']', '(', ')', '{', '}']
    
    for char in unwanted_chars:
        file_name = file_name.replace(char, '')
        
    return ' '.join(filter(lambda x: not x.startswith('@') and not x.startswith('http') and not x.startswith('www.') and not x.startswith('t.me'), file_name.split()))


async def _delete_from_file_collections(method_name, query):
    for collection in (col, sec_col):
        result = await getattr(collection, method_name)(query)
        if result.deleted_count:
            return result.deleted_count
    return 0


async def delete_file_by_id(file_id):
    """Delete one indexed file by ID from the active file collections."""
    return await _delete_from_file_collections(
        "delete_one",
        {"file_id": file_id},
    )


async def delete_file_record(file_id, file_name, file_size):
    """Delete an indexed media record using its ID and filename fallbacks."""
    deleted_count = await delete_file_by_id(file_id)
    if deleted_count:
        return deleted_count

    cleaned_name = clean_file_name(file_name)
    deleted_count = await _delete_from_file_collections(
        "delete_many",
        {"file_name": cleaned_name, "file_size": file_size},
    )
    if deleted_count or cleaned_name == file_name:
        return deleted_count

    return await _delete_from_file_collections(
        "delete_many",
        {"file_name": file_name, "file_size": file_size},
    )


async def is_file_already_saved(file_id, file_name):
    """Check if the file is already saved in either collection."""
    found1 = {'file_name': file_name}
    found = {'file_id': file_id}

    for collection in [col, sec_col]:
        if await collection.find_one(found1) or await collection.find_one(found):
            logger.info("%s is already saved", file_name)
            return True
            
    return False

async def get_bad_files(query, file_type=None, use_filter=False):
    """For given query return (results, next_offset)"""
    query = query.strip()
    
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = rf'(\b|[.+-_]){query}(\b|[.+-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[s.+-_]')
    
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except re.error:
        return [], 0

    filter_criteria = {'file_name': regex}
    if USE_CAPTION_FILTER:
        filter_criteria = {'$or': [filter_criteria, {'caption': regex}]}

    total_results = await col.count_documents(filter_criteria)
    files = await col.find(filter_criteria).to_list(length=None)
    if MULTIPLE_DATABASE:
        total_results += await sec_col.count_documents(filter_criteria)
        files.extend(await sec_col.find(filter_criteria).to_list(length=None))

    return files, total_results

async def get_file_details(query):
    file = await col.find_one({'file_id': query})
    return file or await sec_col.find_one({'file_id': query})

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0
    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")
    
def unpack_new_file_id(new_file_id):
    """Return file_id"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    return file_id


def is_allowed_file(file_name):
    """Check if file extension is in allowed list (ebooks/audiobooks)."""
    if not FILTER_BY_EXTENSION:
        return True
    if not file_name:
        return False
    ext = file_name.rsplit('.', 1)[-1].lower() if '.' in file_name else ''
    return ext in ALLOWED_EXTENSIONS
