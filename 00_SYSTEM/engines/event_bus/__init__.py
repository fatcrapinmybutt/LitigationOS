"""Event Bus — LitigationOS inter-engine communication backbone.

Asyncio + synchronous pub/sub with self-healing retry, topic routing,
event history, and thread-safe operation. Enables engines to react to
evidence discoveries, contradictions, filing updates, and system events
without tight coupling.

Usage:
    from engines.event_bus import EventBus, register_default_handlers

    bus = EventBus()
    register_default_handlers(bus)
    bus.publish_sync("evidence.new", {"quote": "...", "lane": "A"})
"""

__version__ = "1.0.0"

from .bus import EventBus
from .handlers import register_default_handlers

__all__ = ["EventBus", "register_default_handlers"]
