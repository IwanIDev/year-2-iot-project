import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

from flask import Flask

from notify.factory import NotificationFactory
from notify.invoker import NotificationInvoker
from notify.commands import NotificationCommand
from notify.email.email_notification import EmailNotification


class NotificationSystemTests(unittest.TestCase):
    def test_factory_builds_email_notification(self):
        gateway = Mock()
        factory = NotificationFactory(gateway=gateway)

        user = SimpleNamespace(email="resident@example.com")
        bins = ["Food Waste"]
        collection_date = "Tomorrow"

        command = factory.create_email_reminder(user=user, bins=bins, collection_date=collection_date)

        self.assertIsInstance(command, EmailNotification)
        self.assertIs(command.user, user)
        self.assertEqual(command.bins, bins)
        self.assertEqual(command.collection_date, collection_date)
        self.assertIs(command.gateway, gateway)

    def test_invoker_executes_command(self):
        invoker = NotificationInvoker()

        command = Mock(spec=NotificationCommand)
        invoker.execute(command)

        command.execute.assert_called_once_with()

    def test_email_notification_execute_formats_date_and_sends_email(self):
        app = Flask(__name__)
        gateway = Mock()
        gateway.send_email.return_value = SimpleNamespace(is_success=True, text="queued")

        user = SimpleNamespace(email="resident@example.com")
        command = EmailNotification(
            user=user,
            bins=["General Waste", "Recycling"],
            collection_date=date(2026, 5, 1),
            gateway=gateway,
        )

        with app.app_context(), \
            patch("notify.email.email_notification.render_template", side_effect=["<html>ok</html>", "text ok"]) as mock_render, \
            patch.object(app.logger, "info") as mock_info, \
            patch.object(app.logger, "error") as mock_error:
            command.execute()

        self.assertEqual(command.collection_date, "01 May 2026")
        self.assertEqual(mock_render.call_count, 2)
        gateway.send_email.assert_called_once_with(
            recipient="resident@example.com",
            subject="Bin Collection Reminder",
            text_content="text ok",
            html_content="<html>ok</html>",
        )
        mock_info.assert_called_once()
        mock_error.assert_not_called()

    def test_email_notification_execute_logs_error_when_send_fails(self):
        app = Flask(__name__)
        gateway = Mock()
        gateway.send_email.return_value = SimpleNamespace(is_success=False, text="bad request")

        user = SimpleNamespace(email="resident@example.com")
        command = EmailNotification(
            user=user,
            bins=["General Waste"],
            collection_date="Tomorrow",
            gateway=gateway,
        )

        with app.app_context(), \
            patch("notify.email.email_notification.render_template", side_effect=["<html>fail</html>", "text fail"]), \
            patch.object(app.logger, "info") as mock_info, \
            patch.object(app.logger, "error") as mock_error:
            command.execute()

        mock_error.assert_called_once()
        mock_info.assert_not_called()


if __name__ == "__main__":
    unittest.main()
