import unittest
from datetime import datetime, timedelta, timezone

from api.api_view import _get_shared_attribute_value, _parse_collection_day, should_notify_user


class ApiViewReminderTests(unittest.TestCase):
    def test_get_shared_attribute_value_returns_matching_value(self):
        payload = [
            {"key": "bins", "value": "Food, Recycling"},
            {"key": "next_collection_iso", "value": "2026-04-30T00:00:00Z"},
        ]

        self.assertEqual(_get_shared_attribute_value(payload, "bins"), "Food, Recycling")
        self.assertEqual(_get_shared_attribute_value(payload, "missing"), None)

    def test_parse_collection_day_handles_utc_iso(self):
        self.assertEqual(_parse_collection_day("2026-04-30T00:00:00Z"), datetime(2026, 4, 30, tzinfo=timezone.utc).date())

    def test_should_notify_user_allows_first_notification_within_window(self):
        now = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
        collection_date = now - timedelta(hours=1)

        self.assertTrue(should_notify_user(collection_date, last_reminder_iso=None, now=now))

    def test_should_notify_user_skips_when_same_collection_day_was_already_notified(self):
        now = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
        collection_date = now - timedelta(hours=1)

        self.assertFalse(
            should_notify_user(
                collection_date,
                last_reminder_iso="2026-04-30T00:00:00Z",
                now=now,
            )
        )

    def test_should_notify_user_skips_future_dates(self):
        now = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
        collection_date = now + timedelta(hours=1)

        self.assertFalse(should_notify_user(collection_date, last_reminder_iso=None, now=now))


if __name__ == "__main__":
    unittest.main()