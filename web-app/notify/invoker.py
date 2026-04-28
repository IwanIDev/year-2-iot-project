"""Command invoker for executing notification actions."""

from notify.commands import NotificationCommand


class NotificationInvoker:
    """Execute notification commands."""

    def execute(self, command: NotificationCommand) -> None:
        """Run the provided notification command."""
        command.execute()
