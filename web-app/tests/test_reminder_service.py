import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

from notify.reminder_service import ReminderService


class ReminderServiceTests(unittest.TestCase):
    def test_send_email_reminder_creates_and_executes_command(self):
        factory = Mock()
        invoker = Mock()
        command = Mock()
        factory.create_email_reminder.return_value = command

        service = ReminderService(factory=factory, invoker=invoker)
        user = SimpleNamespace(email="resident@example.com")
        bins = ["General Waste", "Recycling"]
        collection_date = date(2026, 5, 1)

        service.send_email_reminder(user=user, bins=bins, collection_date=collection_date)

        factory.create_email_reminder.assert_called_once_with(user, bins, collection_date)
        invoker.execute.assert_called_once_with(command)


if __name__ == "__main__":
    unittest.main()
