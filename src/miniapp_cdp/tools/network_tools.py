from __future__ import annotations

import asyncio

from ..network_capture import NetworkCaptureService


def format_requests_markdown(data: dict) -> str:
    md = []
    if data.get("mode") == "detail":
        req = data["request"]
        md.append(f"## Request {req.get('url')}")
        status = req.get('status')
        status_text = f"[success - {status}]" if status else "[failed]" if req.get('loading_finished') else "[pending]"
        md.append(f"Status: {status_text}")
        md.append(f"Method: {req.get('method')}")
        md.append(f"Type: {req.get('resource_type')}")
        
        req_headers = req.get("request_headers")
        if req_headers:
            md.append("### Request Headers")
            for k, v in req_headers.items():
                md.append(f"- {k}: {v}")
                
        post_data = req.get("post_data")
        if post_data:
            md.append("### Request Body (Post Data)")
            md.append(post_data)
            
        res_headers = req.get("response_headers")
        if res_headers:
            md.append("### Response Headers")
            for k, v in res_headers.items():
                md.append(f"- {k}: {v}")
                
        initiator = req.get("initiator")
        if initiator:
            import json
            md.append("### Initiator")
            md.append(json.dumps(initiator, ensure_ascii=False, indent=2))
            
        # Note: Response body is extracted by get_response_body in a separate tool
        return "\n".join(md)
    
    # List mode
    reqs = data.get("requests", [])
    total = data.get("totalCount", 0)
    page_size = data.get("pageSize", 20)
    page_idx = data.get("pageIdx", 0)
    
    start_idx = page_idx * page_size
    end_idx = min(start_idx + page_size, total)
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    
    md.append(f"Showing {start_idx + 1}-{end_idx} of {total} (Page {page_idx + 1} of {total_pages}).")
    if page_idx + 1 < total_pages:
        md.append(f"Next page: {page_idx + 1}")
    if page_idx > 0:
        md.append(f"Previous page: {page_idx - 1}")
        
    md.append("\n## Network requests")
    if not reqs:
        md.append("No requests found.")
    else:
        for r in reqs:
            status_code = r.get('status')
            status = f"[success - {status_code}]" if status_code else "[failed]" if r.get('loading_finished') else "[pending]"
            req_str = f"reqid={r['request_id']} [{r.get('resource_type')}] {r.get('method')} {r.get('url')} {status}"
            md.append(req_str)
            
    return "\n".join(md)


async def list_network_requests(
    network_capture: NetworkCaptureService,
    endpoint: str | None = None,
    reqid: str | None = None,
    page_size: int = 20,
    page_idx: int = 0,
    resource_types: list[str] | None = None,
    url_filter: str | None = None,
    include_preserved_requests: bool = False,
    wait_ms: int = 0,
    clear_existing: bool = False,
) -> str:
    monitor = await network_capture.ensure_monitoring(endpoint=endpoint)
    if clear_existing:
        network_capture.clear_requests()
    if wait_ms > 0:
        await asyncio.sleep(wait_ms / 1000)
    data = network_capture.list_requests(
        reqid=reqid,
        page_size=page_size,
        page_idx=page_idx,
        resource_types=resource_types,
        url_filter=url_filter,
    )
    return format_requests_markdown(data)


import base64
from ..network_capture import NetworkCaptureService

BODY_CONTEXT_SIZE_LIMIT = 10000

async def get_response_body(
    network_capture: NetworkCaptureService,
    request_id: str,
    session_id: str | None = None,
) -> str:
    try:
        # 5 seconds timeout
        result = await asyncio.wait_for(
            network_capture.get_response_body(request_id=request_id, session_id=session_id),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        return "<timed out fetching body>"
    except Exception as e:
        return f"<not available: {e}>"

    body = result.get("body", "")
    is_base64 = result.get("base64Encoded", False)
    
    if is_base64:
        try:
            decoded = base64.b64decode(body)
            # Try to decode as utf-8
            body_str = decoded.decode('utf-8')
        except UnicodeDecodeError:
            return "<binary data>"
        except Exception:
            return "<binary data>"
    else:
        body_str = body

    if not body_str:
        return "<empty response>"

    if len(body_str) > BODY_CONTEXT_SIZE_LIMIT:
        body_str = body_str[:BODY_CONTEXT_SIZE_LIMIT] + "\n... <truncated>"
        
    return body_str


async def get_request_initiator(network_capture: NetworkCaptureService, request_id: str) -> str:
    """Gets the JavaScript call stack that initiated a network request."""
    await network_capture.ensure_monitoring()
    collector = network_capture.collector
    if not collector:
        return "Network monitoring is not active."
        
    record = collector.records.get(request_id)
    if not record:
        return f"No network request found with ID {request_id}"
        
    initiator = record.initiator
    if not initiator:
        return f"No initiator information found for request {request_id}.\nThis might be a navigation request or the initiator was not captured."
        
    md = [f"Request initiator for {record.url}:\n"]
    md.append(f"Type: {initiator.get('type')}")
    
    if initiator.get("url"):
        md.append(f"URL: {initiator.get('url')}")
    if initiator.get("lineNumber") is not None:
        md.append(f"Line: {initiator.get('lineNumber', 0) + 1}")
    if initiator.get("columnNumber") is not None:
        md.append(f"Column: {initiator.get('columnNumber')}")
        
    stack = initiator.get("stack")
    if stack and stack.get("callFrames"):
        md.append("\nCall Stack:")
        for i, frame in enumerate(stack["callFrames"]):
            func_name = frame.get("functionName") or "(anonymous)"
            loc = f"{frame.get('url')}:{frame.get('lineNumber', 0) + 1}:{frame.get('columnNumber', 0) + 1}" if frame.get("url") else f"script {frame.get('scriptId')}:{frame.get('lineNumber', 0) + 1}:{frame.get('columnNumber', 0) + 1}"
            md.append(f"  {i + 1}. {func_name} @ {loc}")
            
        parent = stack.get("parent")
        while parent:
            if parent.get("callFrames"):
                desc = parent.get("description", "Async Parent Stack")
                md.append(f"\n{desc}:")
                for i, frame in enumerate(parent["callFrames"]):
                    func_name = frame.get("functionName") or "(anonymous)"
                    loc = f"{frame.get('url')}:{frame.get('lineNumber', 0) + 1}:{frame.get('columnNumber', 0) + 1}" if frame.get("url") else f"script {frame.get('scriptId')}:{frame.get('lineNumber', 0) + 1}:{frame.get('columnNumber', 0) + 1}"
                    md.append(f"  {i + 1}. {func_name} @ {loc}")
            parent = parent.get("parent")
            
    return "\n".join(md)
