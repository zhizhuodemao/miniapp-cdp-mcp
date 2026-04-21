from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from miniapp_cdp.collectors.single_target_network import (
    ALL_RESOURCE_TYPES,
    DEFAULT_ENDPOINT,
    DEFAULT_RESOURCE_TYPES,
    SingleTargetNetworkCollector,
)

DEFAULT_CAPTURE_SECONDS = 100.0


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--target-id", default=None)
    parser.add_argument("--seconds", type=float, default=DEFAULT_CAPTURE_SECONDS)
    parser.add_argument("--all-resource-types", action="store_true")
    args = parser.parse_args()

    resource_types = set(ALL_RESOURCE_TYPES) if args.all_resource_types else set(DEFAULT_RESOURCE_TYPES)
    collector = SingleTargetNetworkCollector(
        endpoint=args.endpoint,
        target_id=args.target_id,
        resource_types=resource_types,
    )
    monitor = await collector.start()
    print(json.dumps({"event": "selected_target", **monitor}, ensure_ascii=False, indent=2))
    print(
        json.dumps(
            {
                "event": "monitor_started",
                "sessionId": monitor["sessionId"],
                "captureSeconds": args.seconds,
                "resourceTypes": sorted(resource_types),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    try:
        last_seen: set[str] = set()
        end_time = asyncio.get_running_loop().time() + args.seconds
        while asyncio.get_running_loop().time() < end_time:
            result = collector.list_requests(page_size=10000, page_idx=0)
            for request in result["requests"]:
                request_id = request["request_id"]
                signature = f"{request_id}:{request.get('status')}:{request.get('loading_finished')}"
                if signature not in last_seen:
                    last_seen.add(signature)
                    if request.get("status") is None:
                        event = "requestWillBeSent"
                    elif request.get("loading_finished"):
                        event = "loadingFinished"
                    else:
                        event = "responseReceived"
                    print(json.dumps({"event": event, "request": request}, ensure_ascii=False))
            await asyncio.sleep(0.2)

        final_result = collector.list_requests(page_size=10000, page_idx=0)
        print(
            json.dumps(
                {
                    "event": "monitor_finished",
                    "sessionId": monitor["sessionId"],
                    "completedCount": len([r for r in final_result["requests"] if r.get("loading_finished")]),
                    "requests": final_result["requests"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        await collector.stop()


if __name__ == "__main__":
    asyncio.run(main())
