from __future__ import annotations
import json
from ..network_capture import NetworkCaptureService

async def break_on_xhr(network_capture: NetworkCaptureService, url: str) -> str:
    await network_capture.ensure_monitoring()
    collector = network_capture.collector
    if not collector:
        return "Debugger not connected."
    
    try:
        await collector.set_xhr_breakpoint(url)
        return f"✅ XHR breakpoint set for URLs containing: '{url}'\nDebugger will pause when a matching XHR/Fetch request is made."
    except Exception as e:
        return f"Error: {e}"

async def remove_xhr_breakpoint(network_capture: NetworkCaptureService, url: str) -> str:
    await network_capture.ensure_monitoring()
    collector = network_capture.collector
    if not collector:
        return "Debugger not connected."
    
    try:
        await collector.remove_xhr_breakpoint(url)
        return f"✅ XHR breakpoint removed for URLs containing: '{url}'"
    except Exception as e:
        return f"Error: {e}"

async def pause_or_resume(network_capture: NetworkCaptureService) -> str:
    await network_capture.ensure_monitoring()
    collector = network_capture.collector
    if not collector:
        return "Debugger not connected."
    
    try:
        if collector.paused_state.is_paused:
            await collector.resume()
            return "▶️ Execution resumed."
        else:
            await collector.pause()
            return "⏸️ Pause requested. Waiting for execution to pause..."
    except Exception as e:
        return f"Error: {e}"

async def get_paused_info(
    network_capture: NetworkCaptureService,
    include_scopes: bool = True,
    max_scope_depth: int = 2,
    frame_index: int = 0
) -> str:
    await network_capture.ensure_monitoring()
    collector = network_capture.collector
    if not collector:
        return "Debugger not connected."
    
    state = collector.paused_state
    if not state.is_paused:
        return "Execution is not paused.\nSet a breakpoint and trigger it to pause execution."
        
    md = ["🔴 Execution Paused\n"]
    if state.reason:
        md.append(f"Reason: {state.reason}")
    if state.hit_breakpoints:
        md.append(f"Hit breakpoints: {', '.join(state.hit_breakpoints)}")
        
    md.append("\n📍 Call Stack:")
    
    for i, frame in enumerate(state.call_frames):
        location = frame.get("location", {})
        script_id = location.get("scriptId")
        script = collector.scripts.get(script_id) if script_id else None
        
        url = (script.url if script else frame.get("url")) or f"script:{script_id}"
        line_num = location.get("lineNumber", 0) + 1
        col_num = location.get("columnNumber", 0) + 1
        
        md.append(f"  {i}. {frame.get('functionName')} @ {url}:{line_num}:{col_num}")
        
    if include_scopes and state.call_frames:
        if frame_index < 0 or frame_index >= len(state.call_frames):
            md.append(f"\n⚠️ frame_index {frame_index} is out of range (0-{len(state.call_frames) - 1}).")
        else:
            selected_frame = state.call_frames[frame_index]
            md.append(f"\n🔍 Scope Variables (frame {frame_index}: {selected_frame.get('functionName') or '<anonymous>'}):")
            
            scope_priority = {"local": 1, "closure": 2}
            scope_count = 0
            
            for scope in selected_frame.get("scopeChain", []):
                scope_type = scope.get("type")
                if scope_type == "global":
                    continue
                    
                priority = scope_priority.get(scope_type, 3)
                if priority > max_scope_depth:
                    continue
                    
                scope_count += 1
                scope_name = scope.get("name") or scope_type
                md.append(f"\n  [{scope_name}]:")
                
                obj = scope.get("object", {})
                object_id = obj.get("objectId")
                
                if object_id:
                    try:
                        variables = await collector.get_scope_variables(object_id)
                        if not variables:
                            md.append("    (empty)")
                        else:
                            for var in variables[:20]:
                                val = var.get("value")
                                val_str = f'"{val}"' if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
                                if val_str and len(val_str) > 200:
                                    val_str = val_str[:200] + "...(truncated)"
                                md.append(f"    {var.get('name')}: {val_str}")
                                
                            if len(variables) > 20:
                                md.append(f"    ... and {len(variables) - 20} more")
                    except Exception:
                        md.append("    (unable to retrieve variables)")
                        
            if scope_count == 0:
                md.append("    (no matching scopes — try increasing max_scope_depth)")
                
    md.append("\n💡 Use pause_or_resume to continue execution.")
    return "\n".join(md)


async def set_breakpoint_on_text(
    network_capture: NetworkCaptureService,
    text: str,
    case_sensitive: bool = True,
    condition: str | None = None
) -> str:
    await network_capture.ensure_monitoring()
    collector = network_capture.collector
    if not collector:
        return "Debugger not connected."
        
    try:
        matches = await collector.search_in_scripts(
            query=text, case_sensitive=case_sensitive, is_regex=False
        )
    except Exception as e:
        return f"Error searching for text: {e}"
        
    if not matches:
        return f"Could not find text '{text}' in any loaded scripts."
        
    if len(matches) > 10:
        return f"Found too many matches ({len(matches)}) for '{text}'. Please provide a more specific string."
        
    results = []
    for match in matches:
        try:
            # Match original implementation: fetch full source to calculate exact column
            source = await collector.get_script_source(match["scriptId"])
            lines = source.split("\n")
            
            col = 0
            if match["lineNumber"] < len(lines):
                line_content = lines[match["lineNumber"]]
                col_pos = line_content.find(text)
                if col_pos >= 0:
                    col = col_pos
                
            bp = await collector.set_breakpoint(
                url=match["url"],
                line_number=match["lineNumber"],
                column_number=col,
                condition=condition
            )
            results.append(f"✅ Breakpoint set at {match['url']}:{match['lineNumber']+1}:{col} (ID: {bp.breakpoint_id})")
        except Exception as e:
            results.append(f"❌ Failed to set breakpoint at {match['url']}:{match['lineNumber']+1} - {e}")
            
    return "\n".join(results)


async def remove_breakpoint(network_capture: NetworkCaptureService, breakpoint_id: str) -> str:
    await network_capture.ensure_monitoring()
    collector = network_capture.collector
    if not collector:
        return "Debugger not connected."
        
    try:
        await collector.remove_breakpoint(breakpoint_id)
        return f"✅ Breakpoint {breakpoint_id} removed."
    except Exception as e:
        return f"Error removing breakpoint: {e}"


async def list_breakpoints(network_capture: NetworkCaptureService) -> str:
    await network_capture.ensure_monitoring()
    collector = network_capture.collector
    if not collector:
        return "Debugger not connected."
        
    md = ["### XHR Breakpoints"]
    if not collector.xhr_breakpoints:
        md.append("No XHR breakpoints set.")
    else:
        for url in collector.xhr_breakpoints:
            md.append(f"- URL contains: '{url}'")
            
    md.append("\n### Code Breakpoints")
    if not collector.breakpoints:
        md.append("No code breakpoints set.")
    else:
        for bp_id, bp in collector.breakpoints.items():
            cond_str = f" (Condition: {bp.condition})" if bp.condition else ""
            md.append(f"- {bp.url}:{bp.line_number + 1} [ID: {bp_id}]{cond_str}")
            
    return "\n".join(md)


async def step(network_capture: NetworkCaptureService, action: str) -> str:
    await network_capture.ensure_monitoring()
    collector = network_capture.collector
    if not collector:
        return "Debugger not connected."
        
    if not collector.paused_state.is_paused:
        return "Execution is not paused."
        
    try:
        if action == "over":
            await collector.step_over()
        elif action == "into":
            await collector.step_into()
        elif action == "out":
            await collector.step_out()
        else:
            return f"Invalid step action: {action}. Use 'over', 'into', or 'out'."
            
        return f"⏭️ Step {action} requested. Waiting for execution to pause again... (Use get_paused_info to check state)"
    except Exception as e:
        return f"Error stepping: {e}"
