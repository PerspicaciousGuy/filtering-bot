import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

REQUIRED_TEST_ENVIRONMENT = {
    "API_ID": "123456",
    "API_HASH": "test-api-hash",
    "BOT_TOKEN": "123456:test-bot-token",
    "DATABASE_URI": "mongodb://localhost:27017",
    "ADMINS": "123456789",
}
for name, value in REQUIRED_TEST_ENVIRONMENT.items():
    os.environ.setdefault(name, value)


from EbookGuy.shared import background_tasks, permissions
from EbookGuy.shared.markup import single_button_markup


class BotAdminTests(unittest.TestCase):
    def test_matches_numeric_id_and_username_case_insensitively(self):
        with patch.object(permissions, "ADMINS", [123456789, "Owner_Name"]):
            self.assertTrue(
                permissions.is_bot_admin(SimpleNamespace(id=123456789))
            )
            self.assertTrue(
                permissions.is_bot_admin(
                    SimpleNamespace(id=1, username="owner_name")
                )
            )

    def test_rejects_other_users_and_objects_without_identity(self):
        with patch.object(permissions, "ADMINS", [123456789]):
            self.assertFalse(
                permissions.is_bot_admin(SimpleNamespace(id=42, username="x"))
            )
            self.assertFalse(permissions.is_bot_admin(SimpleNamespace()))


class SingleButtonMarkupTests(unittest.TestCase):
    def test_builds_one_row_with_one_callback_button(self):
        markup = single_button_markup("Close", "close_data")

        self.assertEqual(len(markup.inline_keyboard), 1)
        self.assertEqual(len(markup.inline_keyboard[0]), 1)
        button = markup.inline_keyboard[0][0]
        self.assertEqual(button.text, "Close")
        self.assertEqual(button.callback_data, "close_data")


class RetainTaskTests(unittest.IsolatedAsyncioTestCase):
    async def test_runs_coroutine_and_releases_task_when_done(self):
        finished = asyncio.Event()

        async def work():
            finished.set()

        background_tasks.retain_task(work())
        self.assertEqual(len(background_tasks._retained_tasks), 1)

        await asyncio.wait_for(finished.wait(), timeout=1)
        await asyncio.sleep(0)
        self.assertEqual(len(background_tasks._retained_tasks), 0)


if __name__ == "__main__":
    unittest.main()
