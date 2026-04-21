from __future__ import annotations

from collections import defaultdict
from typing import Any, Awaitable, Callable

EventHandler = Callable[[dict[str, Any], str | None], Awaitable[None] | None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, method: str, handler: EventHandler) -> None:
        self._handlers[method].append(handler)

    async def emit(self, method: str, params: dict[str, Any], session_id: str | None) -> None:
        for handler in self._handlers.get(method, []):
            result = handler(params, session_id)
            if result is not None:
                await result
