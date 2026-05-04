from datetime import date
from typing import Sequence

from flask import current_app as app

from users.Users import Users


def send_email_reminder(user: Users, bins: Sequence[str], collection_date: date | str) -> None:
    """Send an email reminder to the user about their bin collection schedule."""
    reminder_service = app.extensions.get("reminder_service")
    if reminder_service is None:
        raise RuntimeError("Reminder service not initialized. Call startup_app() to initialize it.")
    reminder_service.send_email_reminder(user, bins, collection_date)

