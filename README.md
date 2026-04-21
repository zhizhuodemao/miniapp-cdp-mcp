# MiniApp CDP MCP

[English](README_en.md) | 中文

微信小程序逆向工程 MCP 服务器，让你的 AI 编码助手（如 Claude、Cursor、Antigravity）能够直接通过 Chrome DevTools Protocol (CDP) 调试和分析微信小程序（包括微信开发者工具或 PC 端微信小程序）中的 JavaScript 代码。

## 功能特点

- **多目标调试**: 支持在 `AppService`（逻辑层）和 `WebView`（渲染层）目标之间无缝切换
- **网络拦截**: 捕获、监控和过滤由小程序发起的 XHR/Fetch 请求
- **断点调试**: 设置/移除代码断点和 XHR 断点，支持在压缩混淆代码中精确定位
- **执行控制**: 暂停/恢复执行，单步调试（over/into/out）并返回源码上下文
- **脚本分析**: 列出所有加载的 JS 脚本，搜索代码，获取/保存源码
- **运行时检查**: 在断点处求值表达式，检查调用栈和作用域变量
- **WebSocket 分析**: 监控 WebSocket 连接和消息模式

## 系统要求

- [Python](https://www.python.org/) 3.11 或更新版本
- [uv](https://docs.astral.sh/uv/) (必需，超快的 Python 包和环境管理器)
- 运行中的微信开发者工具（需开启调试端口）或 PC 版微信小程序（开启远程调试机制）

## 安装前置条件：安装 uv

本项目通过 `uvx` 实现零配置的“开箱即用”。如果你还没安装 `uv`，请先根据你的系统执行以下命令安装：

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 快速开始（uvx 零安装）

无需把代码克隆到本地，你可以直接利用 `uv` 的能力，在 AI 助手的 MCP 配置文件中添加：

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

修改 `~/Library/Application Support/Claude/claude_desktop_config.json`，加入上述配置。

### Cursor

进入 `Cursor Settings` -> `Features` -> `MCP` -> `Add new MCP server`：
- **Type**: `command`
- **Name**: `miniapp-cdp`
- **Command**: `uvx --from miniapp-cdp miniapp-cdp-mcp`

## 本地安装（可选）

如果你想在本地修改或开发：

```bash
git clone https://github.com/yourusername/miniapp-cdp-py.git
cd miniapp-cdp-py
uv sync
```

然后在 MCP 配置中使用本地运行方式：

```json
{
  "mcpServers": {
    "miniapp-cdp": {
      "command": "uv",
      "args": ["run", "run_mcp_server.py"],
      "cwd": "/你的路径/miniapp-cdp-py"
    }
  }
}
```

## 工具列表

### 目标与上下文管理

| 工具              | 描述                                     |
| ----------------- | ---------------------------------------- |
| `list_targets`    | 列出调试器中所有可用的目标（AppService 线程、WebView 线程等）   |
| `switch_target`   | 切换 CDP 连接到不同的目标线程进行调试上下文切换 |

### 网络与 WebSocket

| 工具                     | 描述                                           |
| ------------------------ | ---------------------------------------------- |
| `list_network_requests`  | 列出小程序网络请求（支持分页），或获取单条详情          |
| `get_request_initiator`  | 获取发起网络请求的 JavaScript 调用栈               |
| `get_response_body`      | 获取网络请求的完整响应体 |
| `get_websocket_messages` | 列出 WebSocket 连接或获取特定连接的消息详情 |

### 脚本分析

| 工具                 | 描述                                                 |
| -------------------- | ---------------------------------------------------- |
| `list_scripts`       | 列出当前页面加载的所有 JavaScript 脚本                 |
| `get_script_source`  | 获取脚本源码片段，支持行范围或字符偏移               |
| `save_script_source` | 保存完整脚本源码到本地文件（适用于提取整包或核心风控代码）    |
| `search_in_sources`  | 在所有脚本中搜索字符串或正则表达式                   |

### 断点与执行控制

| 工具                     | 描述                                           |
| ------------------------ | ---------------------------------------------- |
| `set_breakpoint_on_text` | 通过搜索代码文本自动设置断点（切勿直接对匿名函数声明下断点） |
| `break_on_xhr`           | 按 URL 模式设置 XHR/Fetch 断点                 |
| `remove_breakpoint`      | 移除普通代码断点        |
| `remove_xhr_breakpoint`  | 移除 XHR/Fetch 断点        |
| `list_breakpoints`       | 列出所有活动断点                               |
| `get_paused_info`        | 获取暂停状态、调用栈和作用域变量               |
| `pause_or_resume`        | 切换暂停/恢复执行                              |
| `step`                   | 单步调试（over/into/out），返回位置和源码上下文 |

### 检查工具

| 工具                    | 描述                                           |
| ----------------------- | ---------------------------------------------- |
| `evaluate_script`       | 在当前上下文中执行 JavaScript 表达式（支持在断点暂停时执行） |

## 使用示例

### 小程序逆向工程基本流程

1. **连接与目标切换**

```
列出所有小程序目标，并切换到 AppService (逻辑层) 线程
```

2. **查找目标函数与代码**

```
在所有脚本中搜索包含 "encrypt" 的代码，并获取相关脚本的上下文源码
```

3. **设置断点**

```
在加密函数的具体执行语句（如 return 处）设置断点
```

4. **触发并分析**

```
在小程序上点击触发网络请求，断点命中后，检查参数、调用栈以及密钥的生成逻辑
```

### 拦截并分析网络请求

```
抓取最新发出的网络请求列表，并找出特定的加密请求（如带有 mina_edata 参数的请求），
随后获取该请求的发起者调用栈 (Initiator) 定位加密入口。
```

## 实战案例

在项目的 `examples/` 目录下，包含了一些利用本工具逆向得出的实战脚本（例如 `vipshop_decrypt_demo.py`），展示了如何通过 MCP 分析出小程序的复杂多层加密算法并在 Python 中完美还原。

## 安全提示

此工具会将小程序的底层运行上下文暴露给 MCP 客户端，允许检查、调试和修改应用内存中的任何数据。请勿将此工具用于非法用途，仅限于个人学习、安全研究与合法授权的逆向分析。

## 许可证

MIT License
