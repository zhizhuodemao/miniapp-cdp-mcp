# 🚀 自动化发布指南 (CI/CD Pipeline Guide)

本文档旨在记录 `miniapp-cdp-mcp` 项目是如何实现从代码提交全自动打包并发布到全球 PyPI 仓库的。这套工作流可以极大降低开发者的心智负担，实现“只关注代码，无脑发版”的终极体验。

## 一、流水线核心机制

项目通过 `.github/workflows/publish.yml` 配置了基于 GitHub Actions 的智能化 CI/CD 流水线。

这套流水线的**核心智能点**在于：
**只要检测到 `pyproject.toml` 中的 `version` 字段发生了改变，流水线就会自动执行打包和发布。**

流水线的具体执行流：
1. **监听动作**：时刻监听 `main` 分支的所有 `git push` 请求。
2. **智能比对 (Check version change)**：使用 shell 脚本读取上一版本 (`HEAD~1`) 与当前版本的 `pyproject.toml`。
3. **分发路由**：
   - 如果代码变了，但 `version` 没变：流水线会输出 `💤 Version unchanged. Skipping publish step.`，然后安全结束，不执行任何构建（因为 PyPI 严禁重复推送相同的版本号）。
   - 如果 `version` 变了：流水线会输出 `✨ Version changed! Proceeding to publish.`，接着安装高速打包工具 `uv`，执行构建，并推送到 PyPI！

## 二、发版操作手册（傻瓜式日常发版）

无论你改了多么惊天动地的代码，想要发布到公网，永远只需要下面两步：

### 第 1 步：改版本号
打开根目录下的 `pyproject.toml` 文件，找到 `version` 字段，给它升个级（例如从 `"0.1.2"` 改成 `"0.1.3"`）：
```toml
[project]
name = "miniapp-cdp"
version = "0.1.3"  <-- 就是改这里！
```

### 第 2 步：常规提交
像往常一样在你的终端里敲代码提交：
```bash
git add .
git commit -m "feat: 发布了一项很牛的新功能"
git push
```

**结束！** 剩下的全交给云端机器人。你甚至不用在本地装任何 Python 依赖。
前往 [GitHub Actions 页面](https://github.com/zhizhuodemao/miniapp-cdp-mcp/actions) 就能看着流水线自动打包上传，几秒钟后，使用 `uvx miniapp-cdp` 的用户就能体验到最新版本了。

## 三、环境密钥维护 (Troubleshooting)

为了让 GitHub 机器拥有替你向 PyPI 推送代码的权限，该仓库已配置了名为 `PYPI_TOKEN` 的底层安全密钥。

如果未来发现 GitHub Action 在 `Build and publish` 这一步报错 `HTTPError: 403 Forbidden`，说明 Token 过期或失效了，请按以下步骤修复：

1. 登录 [PyPI Token 申请页](https://pypi.org/manage/account/token/)，创建一个新的 Token。
2. 打开当前仓库的 [GitHub Secrets 设置页](https://github.com/zhizhuodemao/miniapp-cdp-mcp/settings/secrets/actions)。
3. 找到 `PYPI_TOKEN`，点击后面的笔图标进行 Edit（或者重新新建一个同名的 Secret），将全新的 `pypi-xxxxxx` 填进去保存即可满血复活。
