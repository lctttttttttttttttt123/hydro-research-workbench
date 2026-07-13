# Codex 安装支持补丁

把本目录中的隐藏目录和文件按原路径合并到 `hydro-research-workbench` 仓库根目录：

```text
.codex-plugin/plugin.json
.agents/plugins/marketplace.json
.mcp.json
.codex/agents/auto-reviewer.toml   # 可选，仅在仓库作为 Codex 项目打开时生效
```

## 用户安装插件

更新到支持 Plugins 的 Codex 后，在终端执行：

```powershell
codex plugin marketplace add lctttttttttttttttt123/hydro-research-workbench --ref main
codex
```

进入 Codex 后输入：

```text
/plugins
```

在 `水利科研工作台` marketplace 中安装并启用 `hydro-research-workbench`，随后开启一个新会话。安装后，仓库 `skills/` 下的技能会作为插件技能加载。

## 启用可选文献检索 MCP

插件中的 `hydro-litsearch` 默认关闭，避免没有 Python 依赖或邮箱环境变量时影响插件启动。

先安装依赖：

```powershell
py -m pip install "mcp>=1.2.0" "httpx>=0.27.0"
```

设置联系邮箱；Semantic Scholar 和 WoS Key 均为可选：

```powershell
[Environment]::SetEnvironmentVariable("LIT_MCP_EMAIL", "your.name@example.com", "User")
[Environment]::SetEnvironmentVariable("S2_API_KEY", "", "User")
[Environment]::SetEnvironmentVariable("WOS_API_KEY", "", "User")
```

然后在 `~/.codex/config.toml` 中启用：

```toml
[plugins."hydro-research-workbench".mcp_servers.hydro-litsearch]
enabled = true
default_tools_approval_mode = "prompt"
```

重启 Codex 后用 `/mcp` 检查连接状态。

> 说明：`.mcp.json` 使用相对 `cwd`，Codex 会以安装后的插件根目录为基准解析 `./hydro-litsearch-mcp`。

## 关于 auto-reviewer

Codex 当前的插件清单不支持把自定义 agent 作为插件组件自动安装。因此 `.codex/agents/auto-reviewer.toml` 是项目级兼容文件：当开发者在本仓库中打开 Codex 时可用；普通用户安装插件后，仍应优先使用插件内已有的 `hydro-auto-review` skill。
