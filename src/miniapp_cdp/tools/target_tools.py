from __future__ import annotations
from typing import TYPE_CHECKING
from ..network_capture import NetworkCaptureService
from ..collectors.single_target_network import SingleTargetNetworkCollector

async def list_targets(network_capture: NetworkCaptureService) -> str:
    await network_capture.ensure_monitoring()
    collector = network_capture.collector
    if not collector:
        return "Not connected."
        
    targets = collector.state_store.list_targets()
    md = ["### Available Targets"]
    for i, t in enumerate(targets):
        is_selected = " ⭐ SELECTED" if collector.selected_target and t.target_id == collector.selected_target.target_id else ""
        md.append(f"{i}. ID: `{t.target_id}`{is_selected}")
        md.append(f"   Type: {t.target_type}")
        md.append(f"   Title: {t.title}")
        md.append(f"   URL: {t.url}")
        
    md.append("\n💡 Use switch_target(target_id) to switch to the AppService or another WebView thread.")
    return "\n".join(md)

async def switch_target(network_capture: NetworkCaptureService, target_id: str) -> str:
    await network_capture.ensure_monitoring()
    old_collector = network_capture.collector
    if old_collector:
        # cleanup old? 
        pass
        
    endpoint = old_collector.ws_endpoint if old_collector else None
    
    # Create a new collector for the specific target
    new_collector = SingleTargetNetworkCollector(
        endpoint=endpoint,
        target_id=target_id,
    )
    monitor = await new_collector.start()
    
    network_capture.collector = new_collector
    network_capture.monitor = monitor
    
    t = new_collector.selected_target
    title = t.title if t else "Unknown"
    return f"✅ Successfully switched to target '{title}' (ID: {target_id}).\n\nNote: Previous network records and breakpoints have been cleared. You are now attached to a different thread."
