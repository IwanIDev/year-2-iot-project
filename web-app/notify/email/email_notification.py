"""Email notification command implementation."""

from dataclasses import dataclass
from datetime import date
from typing import Sequence

from flask import current_app, render_template

from notify.commands import NotificationCommand
from notify.gateway import MailgunGateway
from users.Users import Users


@dataclass(slots=True)
class EmailNotification(NotificationCommand):
    """Concrete command for sending a bin collection reminder email."""

    user: Users
    bins: Sequence[str]
    collection_date: date | str
    gateway: MailgunGateway

    def execute(self) -> None:
        """Render the reminder templates and send the email."""
        if isinstance(self.collection_date, date):
            self.collection_date = self.collection_date.strftime("%d %B %Y")

        
        html_content = render_template(
            "email/reminder.html",
            user=self.user,
            bins=self.bins,
            collection_date=self.collection_date,
        )
        text_content = render_template(
            "email/reminder.txt",
            user=self.user,
            bins=self.bins,
            collection_date=self.collection_date,
        )

        response = self.gateway.send_email(
            recipient=self.user.email,
            subject="Bin Collection Reminder",
            text_content=text_content,
            html_content=html_content,
        )

        if not response.is_success:
            current_app.logger.error(
                "Failed to send email reminder to %s. Response: %s",
                self.user.email,
                response.text,
            )
            return

        current_app.logger.info(
            "Email reminder sent successfully to %s. Response: %s",
            self.user.email,
            response.text,
        )

