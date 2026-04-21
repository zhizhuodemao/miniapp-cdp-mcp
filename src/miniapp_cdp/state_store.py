from __future__ import annotations

from .models import AppState, RequestState, SessionState, TargetState


class StateStore:
    def __init__(self) -> None:
        self.state = AppState()

    def reset_runtime(self) -> None:
        self.state.endpoint.connected = False
        self.state.context.selected_target_id = None
        self.state.context.selected_session_id = None
        self.state.targets.clear()
        self.state.sessions.clear()
        self.state.requests.clear()

    def set_endpoint(self, raw_input: str, resolved_ws_endpoint: str) -> None:
        self.state.endpoint.raw_input = raw_input
        self.state.endpoint.resolved_ws_endpoint = resolved_ws_endpoint

    def set_connected(self, connected: bool) -> None:
        self.state.endpoint.connected = connected

    def upsert_target(self, target: TargetState) -> None:
        current = self.state.targets.get(target.target_id)
        if current:
            current.target_type = target.target_type
            current.title = target.title
            current.url = target.url
            if target.attached:
                current.attached = True
            if target.session_id is not None:
                current.session_id = target.session_id
            return
        self.state.targets[target.target_id] = target

    def mark_target_attached(self, target_id: str, session_id: str) -> None:
        target = self.state.targets.get(target_id)
        if target:
            target.attached = True
            target.session_id = session_id

    def upsert_session(self, session: SessionState) -> None:
        self.state.sessions[session.session_id] = session

    def mark_session_network_enabled(self, session_id: str) -> None:
        session = self.state.sessions.get(session_id)
        if session:
            session.network_enabled = True

    def select_target(self, target_id: str) -> None:
        for target in self.state.targets.values():
            target.selected = target.target_id == target_id
        for session in self.state.sessions.values():
            session.selected = False
        self.state.context.selected_target_id = target_id
        target = self.state.targets.get(target_id)
        self.state.context.selected_session_id = target.session_id if target else None
        if target and target.session_id:
            session = self.state.sessions.get(target.session_id)
            if session:
                session.selected = True

    def set_monitor(self, target_id: str, session_id: str) -> None:
        self.state.context.monitor_started = True
        self.state.context.monitor_target_id = target_id
        self.state.context.monitor_session_id = session_id

    def clear_requests(self) -> None:
        self.state.requests.clear()

    def upsert_request(self, request: RequestState) -> None:
        key = (request.session_id, request.request_id)
        current = self.state.requests.get(key)
        if current:
            current.url = request.url or current.url
            current.method = request.method or current.method
            current.status = request.status if request.status is not None else current.status
            current.mime_type = request.mime_type or current.mime_type
            current.resource_type = request.resource_type or current.resource_type
            current.encoded_data_length = (
                request.encoded_data_length
                if request.encoded_data_length is not None
                else current.encoded_data_length
            )
            current.initiator = request.initiator or current.initiator
            current.loading_finished = request.loading_finished or current.loading_finished
            current.has_response_body = request.has_response_body or current.has_response_body
            return
        self.state.requests[key] = request

    def get_request(self, session_id: str, request_id: str) -> RequestState | None:
        return self.state.requests.get((session_id, request_id))

    def list_targets(self) -> list[TargetState]:
        return list(self.state.targets.values())

    def list_requests(self) -> list[RequestState]:
        return list(self.state.requests.values())
