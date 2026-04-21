from __future__ import annotations

from urllib.parse import urlparse, parse_qs


def resolve_endpoint(input_value: str) -> str:
    value = input_value.strip()

    if not value:
        raise ValueError("Endpoint is required")

    if value.startswith("ws://") or value.startswith("wss://"):
        return value

    if not value.startswith("devtools://"):
        raise ValueError(f"Unsupported endpoint format: {value}")

    parsed = urlparse(value)
    ws_values = parse_qs(parsed.query).get("ws")
    ws_value = ws_values[0] if ws_values else None

    if not ws_value:
        raise ValueError(f"Missing ws query parameter in devtools URL: {value}")

    return f"ws://{ws_value}"
