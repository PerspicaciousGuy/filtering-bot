FRESH = {}
PENDING_SEARCH = {}


class MockMessage:
    """Mock message object for format selection callbacks"""
    def __init__(self, original_query, pending_data):
        self.chat = original_query.message.chat
        self.from_user = original_query.from_user
        self.id = pending_data['message_id']
        self.text = pending_data['query']
    
    async def delete(self):
        pass  # Mock delete - original message already handled
