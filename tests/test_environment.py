import os
import unittest
from unittest.mock import patch

from EbookGuy.shared.environment import (
    ConfigurationError,
    load_and_validate_environment,
    parse_identifiers,
    parse_optional_identifier,
    required_int_environment,
)


class EnvironmentTests(unittest.TestCase):
    def test_reports_all_missing_required_values(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("EbookGuy.shared.environment.load_dotenv"),
            self.assertRaisesRegex(
                ConfigurationError,
                "API_ID, BOT_TOKEN",
            ),
        ):
            load_and_validate_environment(("BOT_TOKEN", "API_ID"))

    def test_rejects_invalid_required_integer(self):
        with (
            patch.dict(os.environ, {"API_ID": "not-a-number"}, clear=True),
            self.assertRaisesRegex(ConfigurationError, "must be an integer"),
        ):
            required_int_environment("API_ID")

    def test_parses_ids_and_usernames(self):
        self.assertEqual(
            parse_identifiers("-1001234567890 admin_name 123456"),
            [-1001234567890, "admin_name", 123456],
        )

    def test_parses_empty_optional_identifier(self):
        self.assertIsNone(parse_optional_identifier(""))


if __name__ == "__main__":
    unittest.main()
