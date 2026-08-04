import os
import shutil
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

REQUIRED_TEST_ENVIRONMENT = {
    "API_ID": "123456",
    "API_HASH": "test-api-hash",
    "BOT_TOKEN": "123456:test-bot-token",
    "DATABASE_URI": "mongodb://localhost:27017",
    "ADMINS": "123456789",
}
for name, value in REQUIRED_TEST_ENVIRONMENT.items():
    os.environ.setdefault(name, value)


from EbookGuy.features.downloads import conversion


class ConversionRequestTests(unittest.IsolatedAsyncioTestCase):
    async def test_rejects_unrecognized_target_format(self):
        query = SimpleNamespace(
            data="do_convert#prefix#file-id#../pdf",
            from_user=SimpleNamespace(id=123456789),
            answer=AsyncMock(),
        )

        with (
            patch.object(
                conversion,
                "get_file_details",
                AsyncMock(return_value={"file_name": "book epub"}),
            ),
            patch.object(
                conversion,
                "get_global_settings",
                AsyncMock(return_value={}),
            ),
            patch.object(
                conversion,
                "_check_conversion_policy",
                AsyncMock(return_value=True),
            ),
            patch.object(conversion.tempfile, "mkdtemp") as make_directory,
        ):
            result = await conversion._load_conversion(query)

        self.assertIsNone(result)
        make_directory.assert_not_called()
        query.answer.assert_awaited_once_with(
            "Invalid conversion format.",
            show_alert=True,
        )

    async def test_uses_isolated_temporary_directory(self):
        query = SimpleNamespace(
            data="do_convert#prefix#file-id#pdf",
            from_user=SimpleNamespace(id=123456789),
            answer=AsyncMock(),
        )

        with (
            patch.object(
                conversion,
                "get_file_details",
                AsyncMock(return_value={"file_name": "book epub"}),
            ),
            patch.object(
                conversion,
                "get_global_settings",
                AsyncMock(return_value={}),
            ),
            patch.object(
                conversion,
                "_check_conversion_policy",
                AsyncMock(return_value=True),
            ),
        ):
            result = await conversion._load_conversion(query)

        try:
            self.assertEqual(
                Path(result.input_path).parent,
                Path(result.work_dir),
            )
            self.assertEqual(
                Path(result.output_path).parent,
                Path(result.work_dir),
            )
            self.assertEqual(Path(result.input_path).name, "input.epub")
            self.assertEqual(Path(result.output_path).name, "output.pdf")
        finally:
            shutil.rmtree(result.work_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
