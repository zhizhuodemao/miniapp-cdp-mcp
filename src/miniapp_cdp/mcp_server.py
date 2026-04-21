from __future__ import annotations

from .cdp_runtime import CDPRuntime
from .event_bus import EventBus
from .network_capture import NetworkCaptureService
from .state_store import StateStore
from .tools.network_tools import (
    get_response_body,
    list_network_requests,
    get_request_initiator,
)
from .tools.script_tools import (
    list_scripts,
    get_script_source,
    save_script_source,
    search_in_sources,
    evaluate_script,
)
from .tools.debugger_tools import (
    break_on_xhr,
    remove_breakpoints,
    resume_execution,
    get_paused_info,
    set_breakpoint_on_text,
    list_breakpoints,
    step,
)
from .tools.target_tools import list_targets, switch_target

class MiniappCDPMCP:
    def __init__(self) -> None:
        self.state_store = StateStore()
        self.event_bus = EventBus()
        self.runtime = CDPRuntime(self.state_store, self.event_bus)
        self.network_capture = NetworkCaptureService()

    async def list_network_requests(
        self,
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
        return await list_network_requests(
            self.network_capture,
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

    async def get_response_body(
        self, request_id: str, session_id: str | None = None
    ) -> str:
        return await get_response_body(
            self.network_capture,
            request_id=request_id,
            session_id=session_id,
        )

    async def get_request_initiator(self, request_id: str) -> str:
        return await get_request_initiator(self.network_capture, request_id)

    async def list_scripts(self, url_filter: str | None = None) -> str:
        return await list_scripts(self.network_capture, url_filter=url_filter)

    async def get_script_source(
        self,
        script_id: str | None = None,
        url: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
        offset: int | None = None,
        length: int = 1000,
    ) -> str:
        return await get_script_source(
            self.network_capture,
            script_id=script_id,
            url=url,
            start_line=start_line,
            end_line=end_line,
            offset=offset,
            length=length,
        )

    async def save_script_source(
        self,
        file_path: str,
        script_id: str | None = None,
        url: str | None = None,
    ) -> str:
        return await save_script_source(
            self.network_capture,
            file_path=file_path,
            script_id=script_id,
            url=url,
        )

    async def search_in_sources(
        self,
        query: str,
        case_sensitive: bool = False,
        is_regex: bool = False,
        max_results: int = 30,
        max_line_length: int = 150,
        exclude_minified: bool = True,
        url_filter: str | None = None,
    ) -> str:
        return await search_in_sources(
            self.network_capture,
            query=query,
            case_sensitive=case_sensitive,
            is_regex=is_regex,
            max_results=max_results,
            max_line_length=max_line_length,
            exclude_minified=exclude_minified,
            url_filter=url_filter,
        )

    async def evaluate_script(
        self,
        expression: str,
        return_by_value: bool = True,
        await_promise: bool = True,
        context_id: int | None = None,
        frame_index: int = 0,
    ) -> str:
        return await evaluate_script(
            self.network_capture,
            expression=expression,
            return_by_value=return_by_value,
            await_promise=await_promise,
            context_id=context_id,
            frame_index=frame_index,
        )

    async def get_websocket_messages(
        self,
        wsid: str | None = None,
        direction: str | None = None,
        show_content: bool = False,
        page_size: int = 10,
        page_idx: int = 0,
    ) -> str:
        from .tools.websocket_tools import get_websocket_messages
        return await get_websocket_messages(
            self.network_capture,
            wsid=wsid,
            direction=direction,
            show_content=show_content,
            page_size=page_size,
            page_idx=page_idx,
        )

    async def break_on_xhr(self, url: str) -> str:
        return await break_on_xhr(self.network_capture, url)

    async def resume_execution(self) -> str:
        return await resume_execution(self.network_capture)

    async def get_paused_info(
        self,
        include_scopes: bool = True,
        max_scope_depth: int = 2,
        frame_index: int = 0,
    ) -> str:
        return await get_paused_info(
            self.network_capture,
            include_scopes=include_scopes,
            max_scope_depth=max_scope_depth,
            frame_index=frame_index,
        )

    async def set_breakpoint_on_text(
        self,
        text: str,
        case_sensitive: bool = True,
        condition: str | None = None,
    ) -> str:
        return await set_breakpoint_on_text(
            self.network_capture,
            text=text,
            case_sensitive=case_sensitive,
            condition=condition,
        )

    async def remove_breakpoints(
        self,
        breakpoint_id: str | None = None,
        xhr_url: str | None = None,
        clear_all: bool = False,
    ) -> str:
        return await remove_breakpoints(
            self.network_capture,
            breakpoint_id=breakpoint_id,
            xhr_url=xhr_url,
            clear_all=clear_all,
        )

    async def list_breakpoints(self) -> str:
        return await list_breakpoints(self.network_capture)

    async def step(self, action: str) -> str:
        return await step(self.network_capture, action)

    async def list_targets(self) -> str:
        return await list_targets(self.network_capture)

    async def switch_target(self, target_id: str) -> str:
        return await switch_target(self.network_capture, target_id)
