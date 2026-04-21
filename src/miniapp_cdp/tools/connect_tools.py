from __future__ import annotations

from ..endpoint import resolve_endpoint
from ..cdp_runtime import CDPRuntime
from ..state_store import StateStore


async def connect_endpoint(
    runtime: CDPRuntime,
    state_store: StateStore,
    endpoint: str,
) -> dict:
    resolved = resolve_endpoint(endpoint)
    await runtime.connect(endpoint, resolved)
    targets = await runtime.bootstrap_targets_and_sessions()
    return {
        "ok": True,
        "resolvedEndpoint": resolved,
        "connected": state_store.state.endpoint.connected,
        "targetCount": len(targets),
        "sessionCount": len(state_store.state.sessions),
    }
