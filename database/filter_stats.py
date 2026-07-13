async def count_filter_records(database, excluded_collection="CONNECTION"):
    """Return collection and document counts for a filter database."""
    collections = await database.list_collection_names()
    collections = [
        name for name in collections
        if name != excluded_collection
    ]
    total_count = 0
    for collection_name in collections:
        total_count += await database[collection_name].count_documents({})
    return len(collections), total_count


def build_filter_stats(database):
    """Bind the shared counter to one filter database."""
    async def get_stats():
        return await count_filter_records(database)

    return get_stats
