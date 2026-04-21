from __future__ import annotations

from ..network_capture import NetworkCaptureService


async def list_scripts(
    network_capture: NetworkCaptureService,
    url_filter: str | None = None,
) -> str:
    await network_capture.ensure_monitoring()
    
    if network_capture.collector is None:
        return "Debugger not connected."
        
    scripts = network_capture.collector.list_scripts(url_filter=url_filter)
    
    scripts_with_urls = [s for s in scripts if s.url]
    display_scripts = scripts_with_urls if scripts_with_urls else scripts
    
    if not display_scripts:
        return "No scripts found."
        
    md = [f"Found {len(display_scripts)} script(s):\n"]
    for script in display_scripts:
        md.append(f"- ID: {script.script_id}")
        md.append(f"  URL: {script.url or '(inline/eval)'}")
        if script.source_map_url:
            md.append(f"  SourceMap: {script.source_map_url}")
        md.append("")
        
    return "\n".join(md)


import os

async def get_script_source(
    network_capture: NetworkCaptureService,
    script_id: str | None = None,
    url: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
    offset: int | None = None,
    length: int = 1000,
) -> str:
    await network_capture.ensure_monitoring()
    collector = network_capture.collector
    if collector is None:
        return "Debugger not connected."
        
    if not script_id and not url:
        return "Either script_id or url must be provided."
        
    resolved_id = script_id
    if url:
        for sid, script in collector.scripts.items():
            if url in script.url:
                resolved_id = sid
                break
                
    if not resolved_id:
        return f"Could not resolve script ID for URL: {url}"
        
    try:
        source = await collector.get_script_source(resolved_id)
    except Exception as e:
        return f"Error getting script source: {e}"
        
    if not source:
        return f"No source found for script {resolved_id}."
        
    md = []
    
    if offset is not None:
        start = max(0, offset)
        end = min(len(source), start + length)
        extract = source[start:end]
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(source) else ""
        
        md.append(f"Source for script {resolved_id} (chars {start}-{end} of {len(source)}):\n")
        md.append("```javascript")
        md.append(f"{prefix}{extract}{suffix}")
        md.append("```")
        return "\n".join(md)
        
    if start_line is not None or end_line is not None:
        lines = source.split("\n")
        start = max(0, (start_line or 1) - 1)
        end = min(len(lines), end_line) if end_line is not None else len(lines)
        selected_lines = lines[start:end]
        content = "\n".join(selected_lines)
        
        if len(content) > 1000:
            md.append(f"Selected lines {start + 1}-{end} of script {resolved_id} are too large ({len(content)} chars). This file is likely minified.")
            md.append("Use offset/length params instead.")
            md.append("First 1000 characters:\n")
            md.append("```javascript")
            md.append(content[:1000] + "...")
            md.append("```")
            return "\n".join(md)
            
        md.append(f"Source for script {resolved_id} (lines {start + 1}-{end}):\n")
        md.append("```javascript")
        for i, line in enumerate(selected_lines):
            md.append(f"{start + i + 1}: {line}")
        md.append("```")
        return "\n".join(md)
        
    if len(source) > 1000:
        md.append(f"Script {resolved_id} is large ({len(source)} chars). Use offset/length or start_line/end_line to read portions.")
        md.append("First 1000 characters:\n")
        md.append("```javascript")
        md.append(source[:1000] + "...")
        md.append("```")
    else:
        md.append(f"Source for script {resolved_id}:\n")
        md.append("```javascript")
        md.append(source)
        md.append("```")
        
    return "\n".join(md)


async def save_script_source(
    network_capture: NetworkCaptureService,
    file_path: str,
    script_id: str | None = None,
    url: str | None = None,
) -> str:
    await network_capture.ensure_monitoring()
    collector = network_capture.collector
    if collector is None:
        return "Debugger not connected."
        
    if not script_id and not url:
        return "Either script_id or url must be provided."
        
    resolved_id = script_id
    if url:
        for sid, script in collector.scripts.items():
            if url in script.url:
                resolved_id = sid
                break
                
    if not resolved_id:
        return f"Could not resolve script ID for URL: {url}"
        
    try:
        source = await collector.get_script_source(resolved_id)
    except Exception as e:
        return f"Error getting script source: {e}"
        
    if not source:
        return f"No source found for script {resolved_id}."
        
    try:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(source)
    except Exception as e:
        return f"Failed to save to {file_path}: {e}"
        
    return f"Saved script source to {file_path} ({len(source)} chars)."


async def search_in_sources(
    network_capture: NetworkCaptureService,
    query: str,
    case_sensitive: bool = False,
    is_regex: bool = False,
    max_results: int = 30,
    max_line_length: int = 150,
    exclude_minified: bool = True,
    url_filter: str | None = None,
) -> str:
    await network_capture.ensure_monitoring()
    collector = network_capture.collector
    if collector is None:
        return "Debugger not connected."
        
    try:
        matches = await collector.search_in_scripts(
            query=query, case_sensitive=case_sensitive, is_regex=is_regex
        )
    except Exception as e:
        return f"Error searching: {e}"
        
    if not matches:
        return f"No matches found for '{query}'."
        
    filtered_matches = matches
    if url_filter:
        filtered_matches = [m for m in filtered_matches if m["url"] and url_filter.lower() in m["url"].lower()]
        
    skipped_minified = 0
    if exclude_minified:
        before_count = len(filtered_matches)
        filtered_matches = [m for m in filtered_matches if len(m["lineContent"]) <= 10000]
        skipped_minified = before_count - len(filtered_matches)
        
    if not filtered_matches:
        md = [f"No matches found for '{query}'."]
        if skipped_minified > 0:
            md.append(f"({skipped_minified} matches in minified files were skipped. Set exclude_minified=False to include them.)")
        return "\n".join(md)
        
    total_matches = len(filtered_matches)
    display_matches = filtered_matches[:max_results]
    
    md = [f"Found {total_matches} match(es) for '{query}'" + (f" (showing first {max_results}):" if total_matches > max_results else ":")]
    if skipped_minified > 0:
        md.append(f"({skipped_minified} matches in minified files skipped)")
    md.append("")
    
    for match in display_matches:
        line_num = match["lineNumber"] + 1
        script_id = match["scriptId"]
        url = match["url"] or "(inline)"
        
        preview = match["lineContent"].strip()
        effective_max_len = max_line_length if max_line_length > 0 else 500
        
        if len(preview) > effective_max_len:
            lower_content = preview if case_sensitive else preview.lower()
            lower_query = query if case_sensitive else query.lower()
            match_pos = 0 if is_regex else lower_content.find(lower_query)
            
            if match_pos >= 0:
                half_len = effective_max_len // 2
                start = max(0, match_pos - half_len)
                end = start + effective_max_len
                if end > len(preview):
                    end = len(preview)
                    start = max(0, end - effective_max_len)
                prefix = "..." if start > 0 else ""
                suffix = "..." if end < len(preview) else ""
                preview = prefix + preview[start:end] + suffix
            else:
                preview = preview[:effective_max_len] + "..."
                
        md.append(f"[{script_id}] {url}:{line_num}")
        md.append(f"  {preview}")
        md.append("")
        
    md.append("---")
    md.append("Tip: Use get_script_source(url=..., start_line, end_line) to view full context around a match.")
    return "\n".join(md)


import json

async def evaluate_script(
    network_capture: NetworkCaptureService,
    expression: str,
    return_by_value: bool = True,
    await_promise: bool = True,
    context_id: int | None = None,
    frame_index: int = 0,
) -> str:
    await network_capture.ensure_monitoring()
    collector = network_capture.collector
    if collector is None:
        return "Runtime not connected."
        
    try:
        import asyncio
        result = await asyncio.wait_for(
            collector.evaluate_script(
                expression=expression,
                return_by_value=return_by_value,
                await_promise=await_promise,
                context_id=context_id,
                frame_index=frame_index,
            ),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        return "Error: Script evaluation timed out after 30 seconds."
    except Exception as e:
        return f"Error evaluating script: {e}"
        
    exception = result.get("exceptionDetails")
    if exception:
        md = ["Evaluation resulted in an exception:\n```javascript"]
        if "exception" in exception and "description" in exception["exception"]:
            md.append(exception["exception"]["description"])
        else:
            md.append(json.dumps(exception, indent=2, ensure_ascii=False))
        md.append("```")
        return "\n".join(md)
        
    remote_obj = result.get("result", {})
    
    md = ["Evaluation Result:\n```json"]
    if return_by_value and "value" in remote_obj:
        md.append(json.dumps(remote_obj["value"], indent=2, ensure_ascii=False))
    else:
        # For non-value returns (e.g. object references or undefined)
        desc = remote_obj.get("description", str(remote_obj))
        if remote_obj.get("type") == "undefined":
            desc = "undefined"
        md.append(desc)
    md.append("```")
    return "\n".join(md)
