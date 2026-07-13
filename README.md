# 水利/水电科研工作台

面向水利工程、水电工程科研写作与数据分析的可复用工作台，支持 **Claude Desktop / Cowork** 与 **OpenAI Codex**。

覆盖以下科研流程：

> 文献检索与精读 → 文献综述 → 论文谋篇 → 学术写作 → 数据分析 → 科研制图 → 文稿润色 → 自动审查 → Word 成文

当前包含 **14 个 skill**，并附带一个可选的水利文献检索 MCP。

## 主要特点

- 面向河流动力学、泥沙运动、局部冲刷、河床演变、水文水资源、水工结构、水库调度和水电系统等方向。
- 支持中文学位论文、中文期刊论文、英文 SCI 论文和科研项目申请书。
- 支持河海大学学位论文 Word 排版与专项审稿。
- 支持 CSV、Excel 等科研数据的统计、拟合和模型评价。
- 支持出版级科研图件生成及统一图表规范。
- 强调真实数据、真实文献、结果可追溯和项目可复现。
- 全局原则：不编造数据、不编造文献，不确定内容明确标记为待补。

## 支持平台

- Claude Desktop / Cowork
- ChatGPT Desktop 中的 Codex
- Codex CLI
- Codex IDE 扩展

## Codex 插件安装

### 方式一：安装完整插件

这种方式会安装全部 skill，并可选择启用文献检索 MCP。

在 PowerShell 或终端中执行：

```powershell
codex plugin marketplace add lctttttttttttttttt123/hydro-research-workbench --ref main
```

随后启动 Codex CLI：

```powershell
codex
```

在 Codex 中输入：

```text
/plugins
```

找到并安装：

```text
hydro-research-workbench
```

使用 Codex 桌面版时，也可以重启应用后进入 **Plugins** 页面完成安装。

插件安装完成后，请新建一个聊天或 CLI 会话，使 skill 正式加载。

检查可用 skill：

```text
/skills
```

也可以输入 `$` 搜索并显式调用某个 skill。

### 方式二：只在当前项目中安装 skill

这种方式不会全局安装，只对当前项目及其子目录生效。

先进入需要使用这些 skill 的项目根目录，然后执行：

```powershell
New-Item -ItemType Directory -Force ".agents\skills" | Out-Null

$tempRepo = Join-Path $env:TEMP ("hydro-research-workbench-" + [guid]::NewGuid())

git clone --depth 1 `
  https://github.com/lctttttttttttttttt123/hydro-research-workbench.git `
  $tempRepo

Copy-Item `
  "$tempRepo\skills\*" `
  ".agents\skills" `
  -Recurse -Force

Remove-Item $tempRepo -Recurse -Force
```

完成后，项目目录结构类似：

```text
your-project/
├─ .agents/
│  └─ skills/
│     ├─ academic-writing/
│     ├─ hydro-data-analysis/
│     ├─ hydro-paper-narrative/
│     └─ ...
├─ data/
├─ scripts/
└─ ...
```

项目级方式只安装 skill，不自动安装文献检索 MCP。

## Claude Desktop / Cowork 安装

在 Claude Desktop 或 Cowork 中打开：

```text
Customize → Plugins
```

上传本仓库文件夹，或下载仓库后从本地安装。

安装完成后，各 skill 可根据任务描述自动触发，也可以从可用 skill 列表中手动选择。

## 包含的 Skill

### 总协调与项目管理

| Skill | 用途 |
|---|---|
| `$hydro-workflow` | 规划大型跨环节科研任务，并协调其他专项 skill |
| `$hydro-project-steward` | 建立可复现项目目录，登记数据、脚本、图件、文稿和决策记录 |
| `$hydro-auto-review` | 交付前扫描待补项、文件缺失、不可追溯图件、格式问题和残留 AI 痕迹 |

### 文献阅读与论文写作

| Skill | 用途 |
|---|---|
| `$hydro-pdf-explore` | 勘察和精读长篇 PDF，定位章节、图表、方法及主要结论 |
| `$hydro-literature-review` | 规划文献检索、撰写研究进展和凝练研究缺口 |
| `$hydro-paper-narrative` | 梳理论文主线、章节衔接、摘要、结论和创新点 |
| `$hydro-academic-writing` | 撰写和修改水利水电领域论文、学位论文及项目申请书 |
| `$hydro-deai-polish` | 对水利学术文本进行中性去 AI 痕迹润色，保护数据、公式和术语 |
| `$humanizer-zh` | 对普通中文文本进行自然化修改，减少模板化和机器化表达 |

### 数据分析与科研制图

| Skill | 用途 |
|---|---|
| `$hydro-data-analysis` | 数据清洗、统计分析、曲线拟合及 R²、RMSE、NSE 等模型评价 |
| `$hydro-figure-style` | 统一论文图表编号、字体、单位、配色、题注及导出规范 |
| `$hydro-figure-composer` | 使用 Python 和 matplotlib 生成出版级科研图件 |

### 河海大学学位论文

| Skill | 用途 |
|---|---|
| `$hhu-thesis-docx` | 按河海大学学位论文格式生成 Word 文档 |
| `$hhu-thesis-review` | 审阅前言、摘要、问题提出、结论和参考文献等重点部分 |

## 调用示例

### 论文框架

```text
请使用 $hydro-paper-narrative，根据当前项目材料梳理论文科学问题、
研究主线、章节结构和主要创新点。
```

### 数据分析

```text
请使用 $hydro-data-analysis，读取当前项目中的率定数据，
计算 R²、RMSE、MAE、NSE 和平均相对误差。
```

### 科研制图

```text
请使用 $hydro-figure-composer，根据 data/processed 中的真实数据
绘制符合 SCI 论文规范的冲刷深度时程图。
```

### 文献综述

```text
请使用 $hydro-literature-review，围绕桥墩局部冲刷预测方法
梳理研究进展、主要方法和当前研究缺口。
```

### 交付检查

```text
请使用 $hydro-auto-review，对当前项目执行交付前自动审查，
只列出问题、位置和严重程度，不直接修改文件。
```

## Python 依赖

部分 skill 带有 Python 脚本。建议安装：

```powershell
py -m pip install numpy pandas scipy matplotlib python-docx openpyxl
```

其中：

- 数据分析主要使用 `numpy`、`pandas` 和 `scipy`。
- 科研制图主要使用 `matplotlib`。
- Word 文档生成与审阅主要使用 `python-docx`。
- Excel 文件读取通常需要 `openpyxl`。
- PDF 勘察可能需要额外安装 Poppler。

不使用相关脚本时，不需要一次性安装全部依赖。

## 可选文献检索 MCP

仓库包含：

```text
hydro-litsearch-mcp/
```

可用于：

- OpenAlex 文献检索
- Crossref DOI 核验
- Semantic Scholar 信息补充
- Unpaywall 开放全文线索
- 知网和 Web of Science 检索式生成

安装基础依赖：

```powershell
py -m pip install "mcp>=1.2.0" "httpx>=0.27.0"
```

文献检索 MCP 默认关闭，完整启用方法请参阅：

```text
CODEX_INSTALL.md
```

## 默认学术规范

除非用户明确另有要求，默认采用以下约定：

- 中文学位论文、中文期刊论文和科研项目申请书以中文书面语为主。
- 图表使用章号加序号编号，如“图 2.3”“表 4.1”。
- 图表题注采用中英文双语。
- 中文字体使用宋体类字体，英文和数字使用 Times New Roman 类字体。
- 变量使用斜体，单位使用正体，全文单位保持一致。
- 参考文献优先遵循 GB/T 7714。
- 图表遵循“先引后现、每图必解读”。
- 所有正式结果必须基于真实数据和可核实来源。
- 缺少的信息使用 `〖待补：……〗` 标记，不以猜测替代证据。

英文 SCI 投稿时，可切换到国际期刊常用的简洁图表和英文写作风格。

## 仓库结构

```text
hydro-research-workbench/
├─ .agents/plugins/marketplace.json
├─ .claude-plugin/
├─ .codex-plugin/plugin.json
├─ .codex/agents/
├─ agents/
├─ hydro-litsearch-mcp/
├─ skills/
├─ .mcp.json
├─ CODEX_INSTALL.md
├─ CHANGELOG.md
├─ LICENSE
└─ README.md
```

## 来源与致谢

- `figure-*` 的部分配色和矢量导出原则参考了 `figures4papers` 和 `nature-figure`。
- `hhu-thesis-*` 参考了 `hhuthesis` 模板及河海大学学位论文编写格式规定。
- `humanizer-zh` 参考并翻译自相关开源文本自然化项目。
- Codex 插件结构遵循 OpenAI Codex 的 skill、plugin 和 marketplace 规范。

## 许可证

本项目采用 [MIT License](LICENSE)。

欢迎根据实际科研需求提交 Issue、改进 skill 或贡献新的水利水电科研工作流。
