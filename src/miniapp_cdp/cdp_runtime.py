from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cdp_use.client import CDPClient

from .endpoint import resolve_endpoint
from .event_bus import EventBus
from .models import SessionState, TargetState
from .state_store import StateStore


class CDPRuntime:
    def __init__(self, state_store: StateStore, event_bus: EventBus) -> None:
        self.state_store = state_store
        self.event_bus = event_bus
        self.client: "CDPClient | None" = None
        self._bridged_methods: set[str] = set()

    def resolve_endpoint(self, raw_input: str) -> str:
        return resolve_endpoint(raw_input)

    async def connect(self, raw_input: str, resolved_endpoint: str) -> None:
        if self.client is not None:
            return

        from cdp_use.client import CDPClient

        self.state_store.set_endpoint(raw_input, resolved_endpoint)
        self.client = CDPClient(resolved_endpoint)
        await self.client.start()
        self.state_store.set_connected(True)

    async def close(self) -> None:
        if self.client is None:
            return

        await self.client.stop()
        self.client = None
        self.state_store.reset_runtime()

    def require_client(self) -> CDPClient:
        if self.client is None:
            raise RuntimeError("CDP client is not connected")
        return self.client

    async def bootstrap_targets_and_sessions(self) -> list[TargetState]:
        client = self.require_client()
        response = await client.send.Target.getTargets()
        targets: list[TargetState] = []

        for target_info in response["targetInfos"]:
            target = TargetState(
                target_id=target_info["targetId"],
                target_type=target_info["type"],
                title=target_info.get("title", ""),
                url=target_info.get("url", ""),
            )
            self.state_store.upsert_target(target)
            targets.append(target)

        return targets

    def select_default_app_target(self, targets: list[TargetState]) -> TargetState:
        preferred_exact = [
            t
            for t in targets
            if t.target_type == "page"
            and "servicewechat.com" in t.url
            and "page-frame.html" in t.url
            and "preload-" not in t.url
            and t.title == "AppIndex"
        ]
        if preferred_exact:
            return preferred_exact[0]

        preferred_non_preload = [
            t
            for t in targets
            if t.target_type == "page"
            and "servicewechat.com" in t.url
            and "page-frame.html" in t.url
            and "preload-" not in t.url
        ]
        if preferred_non_preload:
            return preferred_non_preload[0]

        preferred = [
            t
            for t in targets
            if t.target_type == "page"
            and "servicewechat.com" in t.url
            and "page-frame.html" in t.url
            and t.title == "AppIndex"
        ]
        if preferred:
            return preferred[0]

        servicewechat_pages = [
            t
            for t in targets
            if t.target_type == "page"
            and "servicewechat.com" in t.url
            and "page-frame.html" in t.url
        ]
        if servicewechat_pages:
            return servicewechat_pages[0]

        raise RuntimeError("Could not infer the corresponding target from current targets")

    async def attach_target(self, target_id: str) -> str:
        target = self.state_store.state.targets.get(target_id)
        if target and target.session_id:
            return target.session_id

        client = self.require_client()
        attached = await client.send.Target.attachToTarget(
            params={"targetId": target_id, "flatten": True}
        )
        session_id = attached.get("sessionId")
        if not session_id:
            raise RuntimeError("attachToTarget returned no sessionId")

        self.state_store.mark_target_attached(target_id, session_id)
        self.state_store.upsert_session(
            SessionState(session_id=session_id, target_id=target_id)
        )
        return session_id

    async def enable_network_for_session(self, session_id: str) -> None:
        session = self.state_store.state.sessions.get(session_id)
        if session and session.network_enabled:
            return
        client = self.require_client()
        await client.send.Network.enable(session_id=session_id)
        self.state_store.mark_session_network_enabled(session_id)

    async def register_forwarding(self, method: str) -> None:
        if method in self._bridged_methods:
            return

        domain_name, event_name = method.split(".", 1)
        register_domain = getattr(self.require_client().register, domain_name)

        async def forwarder(params: dict[str, Any], session_id: str | None) -> None:
            await self.event_bus.emit(method, params, session_id)

        getattr(register_domain, event_name)(forwarder)
        self._bridged_methods.add(method)
