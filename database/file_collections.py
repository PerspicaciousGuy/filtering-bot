from motor.motor_asyncio import AsyncIOMotorClient

from info import (
    COLLECTION_NAME,
    DATABASE_NAME,
    FILE_DB_URI,
    SEC_FILE_DB_URI,
)


client = AsyncIOMotorClient(FILE_DB_URI)
db = client[DATABASE_NAME]
col = db[COLLECTION_NAME]

sec_client = AsyncIOMotorClient(SEC_FILE_DB_URI)
sec_db = sec_client[DATABASE_NAME]
sec_col = sec_db[COLLECTION_NAME]

checkpoint_col = db["indexing_checkpoints"]
