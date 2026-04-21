from __future__ import annotations

from typing import Any

from .collectors.single_target_network import (
    DEFAULT_ENDPOINT,
    DEFAULT_RESOURCE_TYPES,
    SingleTargetNetworkCollector,
)


class NetworkCaptureService:
    def __init__(self) -> None:
        self.collector: SingleTargetNetworkCollector | None = None
        self.monitor: dict[str, Any] | None = None

    async def ensure_monitoring(self, endpoint: str | None = None) -> dict[str, Any]:
        raw_endpoint = endpoint or (self.monitor.get("resolvedEndpoint") if self.monitor else None)
        raw_endpoint = raw_endpoint or DEFAULT_ENDPOINT
        if self.collector is None:
            self.collector = SingleTargetNetworkCollector(
                endpoint=raw_endpoint,
                resource_types=set(DEFAULT_RESOURCE_TYPES),
            )
            self.monitor = await self.collector.start()
        return self.monitor or {}

    def list_requests(
        self,
        reqid: str | None = None,
        page_size: int = 20,
        page_idx: int = 0,
        resource_types: list[str] | None = None,
        url_filter: str | None = None,
        include_preserved_requests: bool = False,
    ) -> dict[str, Any]:
        if self.collector is None:
            return {
                "mode": "list",
                "totalCount": 0,
                "pageSize": page_size,
                "pageIdx": page_idx,
                "requests": [],
            }
        return self.collector.list_requests(
            reqid=reqid,
            page_size=page_size,
            page_idx=page_idx,
            resource_types=resource_types,
            url_filter=url_filter,
        )

    def clear_requests(self) -> None:
        if self.collector is not None:
            self.collector.clear()

    async def get_response_body(
        self, request_id: str, session_id: str | None = None
    ) -> dict[str, Any]:
        if self.collector is None:
            raise RuntimeError("Network collector not started")
        return await self.collector.get_response_body(request_id)
