from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .mcp_server import MiniappCDPMCP

FILTERABLE_RESOURCE_TYPES = [
    "XHR",
    "Fetch",
]

import contextlib

app = MiniappCDPMCP()

@contextlib.asynccontextmanager
async def server_lifespan(server: FastMCP):
    try:
        await app.network_capture.ensure_monitoring()
    except Exception as e:
        print(f"Failed to start background network monitoring: {e}")
    yield

mcp = FastMCP(
    name="miniapp-cdp",
    instructions=(
        "Use list_network_requests as the primary tool. It auto-connects to the "
        "provided devtools/ws endpoint, infers the current miniapp page target, "
        "attaches only that target, starts single-target XHR/Fetch monitoring, "
        "and returns the current cached request snapshot since MCP started monitoring that target."
    ),
    lifespan=server_lifespan,
)


@mcp.tool(
    name="list_network_requests",
    description=(
        "List network requests for the currently selected miniapp target/session since MCP started monitoring it. "
        "Results are sorted newest-first. By default returns the 20 most recent requests; use page_size/page_idx to paginate. "
        "Pass reqid to get a single request's full details. On first call it automatically connects to the endpoint, infers the target, "
        "attaches only that target, enables Network on that target session, and starts collecting XHR/Fetch requests."
    ),
)
async def list_network_requests(
    endpoint: str = "devtools://devtools/bundled/inspector.html?ws=127.0.0.1:62000",
    reqid: str | None = None,
    page_size: int = 20,
    page_idx: int = 0,
    resource_types: list[str] | None = None,
    url_filter: str | None = None,
    include_preserved_requests: bool = False,
    wait_ms: int = 0,
    clear_existing: bool = False,
) -> str:
    return await app.list_network_requests(
        endpoint=endpoint,
        reqid=reqid,
        page_size=page_size,
        page_idx=page_idx,
        resource_types=resource_types,
        url_filter=url_filter,
        include_preserved_requests=include_preserved_requests,
        wait_ms=wait_ms,
        clear_existing=clear_existing,
    )


@mcp.tool(
    name="get_response_body",
    description=(
        "Get the response body for a request returned by list_network_requests. "
        "If session_id is omitted, it is inferred from the monitored request cache."
    ),
)
async def get_response_body(request_id: str, session_id: str | None = None) -> str:
    return await app.get_response_body(request_id=request_id, session_id=session_id)


@mcp.tool(
    name="get_request_initiator",
    description="Gets the JavaScript call stack that initiated a network request. This helps trace which code triggered an API call.",
)
async def get_request_initiator(request_id: str) -> str:
    return await app.get_request_initiator(request_id=request_id)


@mcp.tool(
    name="list_scripts",
    description=(
        "Lists all JavaScript scripts loaded in the current page. Returns script ID, URL, and source map information. "
        "Use this to find scripts before setting breakpoints or searching."
    ),
)
async def list_scripts(url_filter: str | None = None) -> str:
    return await app.list_scripts(url_filter=url_filter)


@mcp.tool(
    name="get_script_source",
    description=(
        "Gets a snippet of a JavaScript script source by URL (recommended) or script ID. "
        "Supports line range (for normal files) or character offset (for minified single-line files)."
    ),
)
async def get_script_source(
    script_id: str | None = None,
    url: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
    offset: int | None = None,
    length: int = 1000,
) -> str:
    return await app.get_script_source(
        script_id=script_id,
        url=url,
        start_line=start_line,
        end_line=end_line,
        offset=offset,
        length=length,
    )


@mcp.tool(
    name="save_script_source",
    description="Saves the full source code of a JavaScript script to a local file.",
)
async def save_script_source(
    file_path: str,
    script_id: str | None = None,
    url: str | None = None,
) -> str:
    return await app.save_script_source(
        file_path=file_path,
        script_id=script_id,
        url=url,
    )


@mcp.tool(
    name="search_in_sources",
    description=(
        "Searches for a string or regex pattern in all loaded JavaScript sources. "
        "Returns matching lines with script ID, URL, and line number."
    ),
)
async def search_in_sources(
    query: str,
    case_sensitive: bool = False,
    is_regex: bool = False,
    max_results: int = 30,
    max_line_length: int = 150,
    exclude_minified: bool = True,
    url_filter: str | None = None,
) -> str:
    return await app.search_in_sources(
        query=query,
        case_sensitive=case_sensitive,
        is_regex=is_regex,
        max_results=max_results,
        max_line_length=max_line_length,
        exclude_minified=exclude_minified,
        url_filter=url_filter,
    )


@mcp.tool(
    name="evaluate_script",
    description="Evaluates a JavaScript expression in the current context. If execution is paused, it automatically evaluates in the paused call frame context.",
)
async def evaluate_script(
    expression: str,
    return_by_value: bool = True,
    await_promise: bool = True,
    context_id: int | None = None,
    frame_index: int = 0,
) -> str:
    return await app.evaluate_script(
        expression=expression,
        return_by_value=return_by_value,
        await_promise=await_promise,
        context_id=context_id,
        frame_index=frame_index,
    )


@mcp.tool(
    name="get_websocket_messages",
    description="Lists WebSocket connections or gets messages for a specific connection. Without wsid, lists all connections. With wsid, gets messages.",
)
async def get_websocket_messages(
    wsid: str | None = None,
    direction: str | None = None,
    show_content: bool = False,
    page_size: int = 10,
    page_idx: int = 0,
) -> str:
    return await app.get_websocket_messages(
        wsid=wsid,
        direction=direction,
        show_content=show_content,
        page_size=page_size,
        page_idx=page_idx,
    )

@mcp.tool(
    name="break_on_xhr",
    description="Sets a breakpoint that triggers when an XHR/Fetch request URL contains the specified string.",
)
async def break_on_xhr(url: str) -> str:
    return await app.break_on_xhr(url=url)


@mcp.tool(
    name="resume_execution",
    description=(
        "Resumes JavaScript execution if it is currently paused at a breakpoint. "
        "Use this tool to continue running the application after you have finished inspecting the paused state."
    ),
)
async def resume_execution() -> str:
    return await app.resume_execution()


@mcp.tool(
    name="get_paused_info",
    description="Gets information about the current paused state including call stack, current location, and scope variables. Use this after a breakpoint is hit to understand the execution context.",
)
async def get_paused_info(
    include_scopes: bool = True,
    max_scope_depth: int = 2,
    frame_index: int = 0,
) -> str:
    return await app.get_paused_info(
        include_scopes=include_scopes,
        max_scope_depth=max_scope_depth,
        frame_index=frame_index,
    )


@mcp.tool(
    name="set_breakpoint_on_text",
    description="Finds a text string in all loaded scripts and sets a breakpoint at that location. "
                "CRITICAL AI WORKFLOW WARNING: Do NOT set breakpoints on function names or assignment statements "
                "(e.g., 'funcName = function'). In minified code, this will break on the one-time assignment rather "
                "than the execution. Instead, ALWAYS use get_script_source to read the function body first, then "
                "set the breakpoint on a specific statement INSIDE the function body (e.g., 'var x=', 'return').",
)
async def set_breakpoint_on_text(
    text: str,
    case_sensitive: bool = True,
    condition: str | None = None,
) -> str:
    return await app.set_breakpoint_on_text(
        text=text,
        case_sensitive=case_sensitive,
        condition=condition,
    )


@mcp.tool(
    name="remove_breakpoints",
    description=(
        "Removes breakpoints. You can specify a code breakpoint ID, an XHR URL, "
        "or set clear_all=True to delete ALL breakpoints (highly recommended before starting a new task). "
        "WARNING: This deletes the breakpoint so it won't hit again. "
        "If you are currently paused and just want to continue running the code, DO NOT use this tool; "
        "use `resume_execution` instead."
    ),
)
async def remove_breakpoints(
    breakpoint_id: str | None = None,
    xhr_url: str | None = None,
    clear_all: bool = False,
) -> str:
    return await app.remove_breakpoints(
        breakpoint_id=breakpoint_id,
        xhr_url=xhr_url,
        clear_all=clear_all,
    )


@mcp.tool(
    name="list_breakpoints",
    description="Lists all active XHR and code breakpoints.",
)
async def list_breakpoints() -> str:
    return await app.list_breakpoints()


@mcp.tool(
    name="step",
    description="Controls execution when paused. action must be one of: 'over', 'into', 'out'.",
)
async def step(action: str) -> str:
    return await app.step(action=action)


@mcp.tool(
    name="list_targets",
    description="Lists all available targets (WebView threads, AppService threads, etc.) in the connected debugger.",
)
async def list_targets() -> str:
    return await app.list_targets()


@mcp.tool(
    name="switch_target",
    description="Switches the CDP connection to a different target thread (e.g. from WebView to AppService) to debug different parts of the miniapp.",
)
async def switch_target(target_id: str) -> str:
    return await app.switch_target(target_id=target_id)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
