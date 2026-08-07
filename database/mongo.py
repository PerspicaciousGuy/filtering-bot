"""Shared MongoDB client registry."""

from motor.motor_asyncio import AsyncIOMotorClient


_CLIENTS = {}


def get_mongo_client(uri):
    """Return one Motor client per connection URI."""
    client = _CLIENTS.get(uri)
    if client is None:
        client = AsyncIOMotorClient(uri, appname="EbookGuyBot")
        _CLIENTS[uri] = client
    return client
