# MiniApp CDP MCP

English | [中文](README.md)

A WeChat Mini Program reverse engineering MCP server that enables AI coding assistants (Claude, Cursor, Antigravity) to debug and analyze JavaScript code in WeChat Mini Programs directly via the Chrome DevTools Protocol (CDP).

## Features

- **Multi-Target Debugging**: Seamlessly switch between `AppService` (Logic thread) and `WebView` (Render thread) targets
- **Network Interception**: Capture, monitor, and filter XHR/Fetch requests initiated by the Mini Program
- **Breakpoint Debugging**: Set/remove code breakpoints and XHR breakpoints, precise positioning in minified/obfuscated code
- **Execution Control**: Pause/resume execution, step debugging (over/into/out) with source context
- **Script Analysis**: List all loaded JS scripts, search code, get/save source code
- **Runtime Inspection**: Evaluate expressions at breakpoints, inspect call stacks and scope variables
- **WebSocket Analysis**: Monitor WebSocket connections and message patterns

## Requirements

- [Python](https://www.python.org/) 3.11 or later
- [uv](https://docs.astral.sh/uv/) (Required, an extremely fast Python package installer)
- Running WeChat DevTools (with debugging port enabled) or WeChat PC Mini Program (with remote debugging enabled)

## Prerequisite 1: Expose Debug Port

Before using this MCP, you must expose the CDP debugging port of the WeChat Mini Program via an injection tool. Depending on your OS and WeChat version, you can use one of the following open-source tools to hook the process and expose the port (typically on `62000`):

- [WMPFDebugger-arm](https://github.com/chain00x/WMPFDebugger-arm) (For macOS ARM)
- [WMPFDebugger](https://github.com/evi0s/WMPFDebugger)
- [WeChatOpenDevTools-Python](https://github.com/JaveleyQAQ/WeChatOpenDevTools-Python)

## Prerequisite 2: Install uv

This project leverages `uvx` for zero-install execution. If you haven't installed `uv` yet, please install it first:

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Quick Start (Zero Install with uvx)

No need to clone the repository. Take advantage of `uvx` and directly add this to your AI assistant's MCP configuration:

```json
{
  "mcpServers": {
    "miniapp-cdp": {
      "command": "uvx",
      "args": ["--from", "miniapp-cdp", "miniapp-cdp-mcp"]
    }
  }
}
```

### Claude Desktop

Modify `~/Library/Application Support/Claude/claude_desktop_config.json` and add the above configuration.

### Cursor

Go to `Cursor Settings` -> `Features` -> `MCP` -> `Add new MCP server`:
- **Type**: `command`
- **Name**: `miniapp-cdp`
- **Command**: `uvx --from miniapp-cdp miniapp-cdp-mcp`

## Local Installation (Alternative)

If you want to modify or develop locally:

```bash
git clone https://github.com/yourusername/miniapp-cdp-py.git
cd miniapp-cdp-py
uv sync
```

Then use the local path in your MCP configuration:

```json
{
  "mcpServers": {
    "miniapp-cdp": {
      "command": "uv",
      "args": ["run", "run_mcp_server.py"],
      "cwd": "/path/to/miniapp-cdp-py"
    }
  }
}
```

## Tools List

### Target & Context Management

| Tool              | Description                                     |
| ----------------- | ----------------------------------------------- |
| `list_targets`    | List all available targets in the debugger (AppService, WebView, etc.) |
| `switch_target`   | Switch CDP connection to a different target thread |

### Network & WebSocket

| Tool                     | Description                                           |
| ------------------------ | ----------------------------------------------------- |
| `list_network_requests`  | List network requests (paginated) or get one by reqid |
| `get_request_initiator`  | Get JavaScript call stack for a network request       |
| `get_response_body`      | Get the full response body for a network request      |
| `get_websocket_messages` | List WebSocket connections or get specific message details |

### Script Analysis

| Tool                 | Description                                                 |
| -------------------- | ----------------------------------------------------------- |
| `list_scripts`       | List all JavaScript scripts loaded in the current page      |
| `get_script_source`  | Get script source snippet by line range or character offset |
| `save_script_source` | Save full script source to a local file (for large/minified files) |
| `search_in_sources`  | Search for strings or regex patterns across all scripts     |

### Breakpoint & Execution Control

| Tool                     | Description                                                |
| ------------------------ | ---------------------------------------------------------- |
| `set_breakpoint_on_text` | Set breakpoint by searching code text (works with minified code) |
| `break_on_xhr`           | Set XHR/Fetch breakpoint by URL pattern                    |
| `remove_breakpoint`      | Remove normal code breakpoint                              |
| `remove_xhr_breakpoint`  | Remove XHR/Fetch breakpoint                                |
| `list_breakpoints`       | List all active breakpoints                                |
| `get_paused_info`        | Get paused state, call stack and scope variables           |
| `pause_or_resume`        | Toggle pause/resume execution                              |
| `step`                   | Step over, into, or out with source context in response    |

### Inspection

| Tool                    | Description                                           |
| ----------------------- | ----------------------------------------------------- |
| `evaluate_script`       | Execute JavaScript expressions (supports paused call frame context) |

## Usage Examples

### Basic Mini Program Reverse Engineering Workflow

1. **Connect and Switch Target**

```
List all mini program targets, and switch to the AppService (Logic layer) thread
```

2. **Find Target Functions**

```
Search all scripts for code containing "encrypt" and get the source snippet
```

3. **Set Breakpoints**

```
Set a breakpoint at the specific execution statement (e.g., return statement) of the encryption function
```

4. **Trigger and Analyze**

```
Trigger a network request in the mini program. Once paused, inspect arguments, call stacks, and encryption keys.
```

### Intercept and Analyze Network Requests

```
Fetch the latest network requests, identify a specific encrypted request (e.g., with mina_edata),
and then get its Request Initiator call stack to locate the encryption entry point.
```

## Real-World Examples

Check out the `examples/` directory for real-world scripts derived using this tool (such as `vipshop_decrypt_demo.py`), which demonstrate how complex multi-layer encryption algorithms inside mini programs can be analyzed via MCP and perfectly reproduced in Python.

## Security Notice

This tool exposes the underlying runtime context of mini programs to MCP clients, allowing inspection, debugging, and modification of any data in the app's memory. Do not use this tool for illegal purposes; it is strictly intended for personal learning, security research, and legally authorized reverse engineering.

## License

MIT License
