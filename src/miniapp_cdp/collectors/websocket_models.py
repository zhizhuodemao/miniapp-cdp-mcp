from dataclasses import dataclass, field
from typing import Any

@dataclass
class WebSocketFrame:
    direction: str  # "sent" or "received"
    time: float
    opcode: int
    mask: bool
    payloadData: str

@dataclass
class WebSocketConnection:
    wsid: str
    url: str
    initiator: dict[str, Any] | None = None
    frames: list[WebSocketFrame] = field(default_factory=list)
    closed: bool = False
