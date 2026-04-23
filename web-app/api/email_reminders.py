from datetime import date
from typing import Sequence

from flask import current_app as app

from notify.factory import NotificationFactory
from notify.gateway import MailgunGateway
from notify.invoker import NotificationInvoker
from notify.reminder_service import ReminderService
from users.Users import Users


def _build_reminder_service() -> ReminderService:
    gateway = MailgunGateway(
        mail_url=app.config["MAIL_URL"],
        mail_sender=app.config["MAIL_SENDER"],
        api_key=app.config["MAIL_API_KEY"],
    )
    return ReminderService(
        factory=NotificationFactory(gateway),
        invoker=NotificationInvoker(),
    )


def send_email_reminder(user: Users, bins: Sequence[str], collection_date: date | str) -> None:
    """Send an email reminder to the user about their bin collection schedule."""
    reminder_service = _build_reminder_service()
    reminder_service.send_email_reminder(user, bins, collection_date)

