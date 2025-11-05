"""
Notification utility module for cross-platform desktop notifications.

This module provides a simple API for sending desktop notifications
across macOS, Linux, and Windows/WSL platforms.
"""

from .core import NotificationSender
from .core import send_notification
from .models import NotificationRequest
from .models import NotificationResponse
from .models import Platform

__all__ = [
    "send_notification",
    "NotificationSender",
    "NotificationRequest",
    "NotificationResponse",
    "Platform",
]
