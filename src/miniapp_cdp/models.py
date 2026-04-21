from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EndpointState:
    raw_input: str = ""
    resolved_ws_endpoint: str | None = None
    connected: bool = False


@dataclass(slots=True)
class TargetState:
    target_id: str
    target_type: str
    title: str
    url: str
    attached: bool = False
    selected: bool = False
    session_id: str | None = None


@dataclass(slots=True)
class SessionState:
    session_id: str
    target_id: str
    selected: bool = False
    network_enabled: bool = False
    debugger_enabled: bool = False


@dataclass(slots=True)
class RequestState:
    session_id: str
    request_id: str
    url: str | None = None
    method: str | None = None
    status: int | None = None
    mime_type: str | None = None
    resource_type: str | None = None
    encoded_data_length: float | None = None
    initiator: dict[str, Any] | None = None
    loading_finished: bool = False
    has_response_body: bool = False


@dataclass(slots=True)
class ToolContext:
    selected_target_id: str | None = None
    selected_session_id: str | None = None
    monitor_started: bool = False
    monitor_target_id: str | None = None
    monitor_session_id: str | None = None


@dataclass(slots=True)
class AppState:
    endpoint: EndpointState = field(default_factory=EndpointState)
    context: ToolContext = field(default_factory=ToolContext)
    targets: dict[str, TargetState] = field(default_factory=dict)
    sessions: dict[str, SessionState] = field(default_factory=dict)
    requests: dict[tuple[str, str], RequestState] = field(default_factory=dict)
