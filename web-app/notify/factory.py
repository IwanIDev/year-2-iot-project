"""Factories for building notification commands from reminder data."""

from datetime import date
from typing import Sequence

from notify.email.email_notification import EmailNotification
from notify.gateway import MailgunGateway
from users.Users import Users


class NotificationFactory:
	"""Build concrete notification commands."""

	def __init__(self, gateway: MailgunGateway):
		self.gateway = gateway

	def create_email_reminder(
		self,
		user: Users,
		bins: Sequence[str],
		collection_date: date | str,
	) -> EmailNotification:
		"""Create an email reminder command."""
		return EmailNotification(
			user=user,
			bins=bins,
			collection_date=collection_date,
			gateway=self.gateway,
		)
