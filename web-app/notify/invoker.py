"""Command invoker for executing notification actions."""

from notify.commands import NotificationCommand
from flask import current_app as app


class NotificationInvoker:
    """Execute notification commands."""

    def execute(self, command: NotificationCommand) -> None:
        """Run the provided notification command."""
        app.logger.info(f"Executing notification command: {command}")
        command.execute()
