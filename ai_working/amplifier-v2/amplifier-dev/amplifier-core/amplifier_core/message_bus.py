"""Simple async pub/sub message bus.

Direct implementation without complex routing or patterns.
Handlers run concurrently for each event.
"""

import asyncio
import logging
from collections.abc import Callable
from collections.abc import Coroutine
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Simple event structure."""

    type: str
    data: dict[str, Any]
    source: str


# Type alias for async event handlers
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class MessageBus:
    """Simple async pub/sub message bus."""

    def __init__(self) -> None:
        """Initialize with empty subscription registry."""
        self.subscriptions: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to an event type.

        Args:
            event_type: The event type to subscribe to
            handler: Async function that receives an Event
        """
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []

        self.subscriptions[event_type].append(handler)
        logger.debug(f"Subscribed handler to {event_type}")

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Remove a handler from an event type.

        Args:
            event_type: The event type to unsubscribe from
            handler: The handler to remove
        """
        if event_type in self.subscriptions:
            try:
                self.subscriptions[event_type].remove(handler)
                logger.debug(f"Unsubscribed handler from {event_type}")
            except ValueError:
                logger.warning(f"Handler not found for {event_type}")

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribed handlers.

        Handlers are executed concurrently using asyncio.gather.
        Errors in individual handlers don't stop other handlers.

        Args:
            event: The event to publish
        """
        handlers = self.subscriptions.get(event.type, [])

        if not handlers:
            logger.debug(f"No handlers for event type: {event.type}")
            return

        # Execute all handlers concurrently
        tasks = []
        for handler in handlers:
            tasks.append(self._run_handler(handler, event))

        # Wait for all handlers to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any exceptions
        for _i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Handler error for {event.type}: {result}")

    async def _run_handler(self, handler: EventHandler, event: Event) -> None:
        """Run a single handler with error handling.

        Args:
            handler: The handler to run
            event: The event to pass to the handler
        """
        try:
            await handler(event)
        except Exception as e:
            # Re-raise to be caught by gather
            raise Exception(f"Handler {handler.__name__} failed: {e}") from e
