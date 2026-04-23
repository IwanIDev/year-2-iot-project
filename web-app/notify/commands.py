"""Notification command abstractions and concrete command types."""

from abc import ABC, abstractmethod


class NotificationCommand(ABC):
    """Command interface for notification actions."""

    @abstractmethod
    def execute(self) -> None:
        """Perform the notification action."""


