"""Reminder decision logic that selects and schedules notifications."""

from datetime import date
from typing import Sequence

from notify.factory import NotificationFactory
from notify.invoker import NotificationInvoker
from users.Users import Users


class ReminderService:
	"""Coordinate reminder command creation and execution."""

	def __init__(self, factory: NotificationFactory, invoker: NotificationInvoker):
		self.factory = factory
		self.invoker = invoker

	def send_email_reminder(
		self,
		user: Users,
		bins: Sequence[str],
		collection_date: date | str,
	) -> None:
		"""Create and execute an email reminder notification."""
		command = self.factory.create_email_reminder(user, bins, collection_date)
		self.invoker.execute(command)
