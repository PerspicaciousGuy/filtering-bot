from database.mongo import get_mongo_client
from info import (
    COLLECTION_NAME,
    DATABASE_NAME,
    FILE_DB_URI,
    MULTIPLE_DATABASE,
    SEC_FILE_DB_URI,
)


client = get_mongo_client(FILE_DB_URI)
db = client[DATABASE_NAME]
col = db[COLLECTION_NAME]

sec_client = get_mongo_client(SEC_FILE_DB_URI)
sec_db = sec_client[DATABASE_NAME]
sec_col = sec_db[COLLECTION_NAME]

checkpoint_col = db["indexing_checkpoints"]


def active_file_collections():
    """Return distinct file collections enabled by the current configuration."""
    if not MULTIPLE_DATABASE:
        return (col,)
    is_same_collection = (
        client is sec_client
        and col.full_name == sec_col.full_name
    )
    return (col,) if is_same_collection else (col, sec_col)
