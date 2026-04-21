from __future__ import annotations

import asyncio
import json
import os
import sys

from .mcp_server import MiniappCDPMCP
from .endpoint import resolve_endpoint


def resolve_cli_endpoint() -> str:
    endpoint = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CDP_ENDPOINT")
    if not endpoint:
        raise RuntimeError("Usage: uv run python -m miniapp_cdp.cli_sample <ws://... | devtools://...>")
    return endpoint


async def main() -> None:
    raw_endpoint = resolve_cli_endpoint()
    resolved_endpoint = resolve_endpoint(raw_endpoint)
    server = MiniappCDPMCP()

    try:
        print(f"Resolved endpoint: {resolved_endpoint}")
        result = await server.connect_endpoint(raw_endpoint)
        print(f"Discovered {result['targetCount']} targets.")
        print("Capturing Network events for 10 seconds. Trigger some app activity now.")
        await asyncio.sleep(10)
        requests = server.list_network_requests()["requests"]
        if not requests:
            print("No completed network requests captured in the sample window.")
            return
        for request in requests:
            print(json.dumps(request, ensure_ascii=False))
    finally:
        await server.runtime.close()


if __name__ == "__main__":
    asyncio.run(main())
