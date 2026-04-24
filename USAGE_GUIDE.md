# Wiki CLI 在 AI 工具中的使用指南

本指南详细说明如何在 Claude Code、CodeX CLI、Gemini CLI 三个 AI 工具中使用 Wiki CLI，实现"更懂我"的智能对话体验。

---

## 目录

1. [快速开始](#快速开始)
2. [初始化配置](#初始化配置)
3. [配置 AI 工具](#配置-ai-工具)
4. [日常使用流程](#日常使用流程)
5. [高级功能](#高级功能)
6. [故障排查](#故障排查)

---

## 快速开始

### 前置条件

- Python 3.8+
- 已安装 wiki CLI：`pip install -e .`（在项目根目录运行）
- 至少一个 AI 工具（Claude Code / CodeX CLI / Gemini CLI）

### 验证安装

```powershell
# Windows PowerShell
Get-Command wiki

# 或者
python -m wiki_cli.main --help

# 应该看到 wiki 命令的帮助信息
```

### 5 分钟快速体验

```powershell
# 1. 初始化 wiki（交互式向导）
wiki init

# 2. 查看配置
wiki config

# 3. 查看已有的 wiki 页面
wiki list

# 4. 配置 MCP（自动配置 Claude Code）
wiki mcp setup

# 5. 在 Claude Code 中测试
# 打开 Claude Code，输入："搜索我的 wiki 中关于 transformer 的内容"
```

---

## 初始化配置

### 1. 运行初始化向导

```powershell
wiki init
```

交互式配置以下内容：
- **数据目录**：默认 `D:/AI/llm-wiki`（Windows）或 `~/llm-wiki`（Unix）
- **语言**：中文 (zh) 或 English (en)
- **Provider**：
  - 类型：Anthropic / OpenAI 兼容
  - API Key
  - 模型名称
  - Base URL（可选，用于火山方舟等第三方服务）

**注意**：如果已经初始化过，可以用 `wiki config set` 修改配置。

### 2. 创建知识领域

```powershell
# 创建领域（交互式）
wiki domain add

# 或者直接指定名称
wiki domain add ai        # AI 相关知识
wiki domain add work      # 工作项目
wiki domain add life      # 生活记录

# 切换活跃领域
wiki domain use ai

# 查看所有领域
wiki domain list
```

### 3. 添加原始文档

```powershell
# 手动添加 markdown 文件到 raw/ 目录
# 例如：D:/AI/llm-wiki/ai/raw/2026-04-24-transformer.md

# 文件命名建议：YYYY-MM-DD-topic-name.md
```

### 4. 生成 wiki 页面

```powershell
# 处理 raw/ 目录下的所有文档
wiki ingest

# 处理特定文件
wiki ingest D:/AI/llm-wiki/ai/raw/2026-04-24-transformer.md

# 查看生成的页面
wiki list
```

---

## 配置 AI 工具

### 方式一：自动配置（推荐）

```powershell
# 自动配置 Claude Code
wiki mcp setup

# 配置会写入：C:\Users\<你的用户名>\.claude\settings.json
```

**自动配置做了什么：**
1. 找到 wiki.exe 的完整路径
2. 在 `~/.claude/settings.json` 中添加 MCP 服务器配置
3. 设置环境变量 `WIKI_DOMAIN` 为当前活跃领域

### 方式二：手动配置

#### Claude Code

编辑 `C:\Users\<你的用户名>\.claude\settings.json`，添加：

```json
{
  "mcpServers": {
    "wiki": {
      "command": "C:\\Users\\<你的用户名>\\AppData\\Local\\Programs\\Python\\Python312\\Scripts\\wiki.exe",
      "args": ["mcp", "serve"],
      "env": {
        "WIKI_DOMAIN": "ai"
      }
    }
  }
}
```

**如何找到 wiki.exe 路径：**

```powershell
Get-Command wiki | Select-Object -ExpandProperty Source
```

#### CodeX CLI 和 Gemini CLI

目前 `wiki mcp setup` 只支持 Claude Code。如需配置其他工具，请参考各工具的 MCP 配置文档。

### 验证配置

```powershell
# 测试 MCP 配置
wiki mcp serve --test

# 应该看到：
# ✓ MCP server configuration OK
#   Domain: ai
#   Provider: volcengine
#   Wiki path: D:\AI\llm-wiki\ai\wiki
```

---

## 日常使用流程

### 重要提示

**MCP 服务器不需要手动启动！**

- AI 工具（如 Claude Code）会在需要时自动启动 `wiki mcp serve` 作为子进程
- 你只需要确保配置正确即可
- **不要**在终端直接运行 `wiki mcp serve`（会报错）

### 典型工作流

```
1. 记录原始信息到 raw/
   ↓
2. 运行 wiki ingest 生成 wiki 页面
   ↓
3. 在 AI 工具中自然对话，AI 自动查询 wiki
   ↓
4. 持续积累知识
```

### 场景 1：学习新技术

```powershell
# 1. 创建学习笔记
# 在 D:/AI/llm-wiki/ai/raw/ 下创建文件
# 例如：2026-04-24-transformer.md

# 2. 生成 wiki 页面
wiki ingest D:/AI/llm-wiki/ai/raw/2026-04-24-transformer.md

# 3. 查看生成的页面
wiki list

# 4. 在 Claude Code 中使用
# 你: "根据我的 wiki，解释 self-attention 机制"
# CC: [自动调用 search_wiki] "根据你的笔记，self-attention..."
```

### 场景 2：查询 wiki

```powershell
# 命令行查询
wiki query "transformer 的核心思想是什么"

# 在 Claude Code 中查询
# 你: "搜索我的 wiki 中关于 transformer 的内容"
# CC: [自动调用 search_wiki 工具]
```

### 场景 3：跨工具协作（使用 Thread）

```powershell
# 1. 创建 thread
wiki thread create memory-leak \
  --title "API 服务器内存泄漏" \
  --priority high \
  --tags "bug,performance"

# 2. 添加消息
wiki thread add-message memory-leak "CodeX 发现 EventEmitter 监听器未清理" \
  --tool codex --action diagnosis

# 3. 在 Claude Code 中继续
# 你: "继续修复 memory-leak 问题"
# CC: [查询 thread] "我看到 CodeX 已经定位了问题..."

# 4. 更新 thread
wiki thread add-message memory-leak "已使用 WeakMap 修复" \
  --tool cc --action fix

# 5. 查看 thread
wiki thread show memory-leak

# 6. 关闭 thread
wiki thread update memory-leak --status closed
```

---

## 高级功能

### 1. Thread 管理

```powershell
# 创建 thread
wiki thread create <id> \
  --title "标题" \
  --description "描述" \
  --priority high \
  --tags "tag1,tag2"

# 添加依赖关系
wiki thread add-dependency api-refactor memory-leak

# 查看依赖树
wiki thread show api-refactor --show-deps

# 过滤列表
wiki thread list --priority high --status open --tag bug

# 更新状态和标签
wiki thread update memory-leak \
  --status closed \
  --add-tags "resolved" \
  --remove-tags "bug"
```

### 2. 链接图分析

```powershell
# 查看页面的反向链接
wiki backlinks <page-slug>

# 查看孤立页面
wiki orphans

# 查看断链
wiki broken

# 导出链接图
wiki graph > wiki-graph.json
```

### 3. 质量检查

```powershell
# 检查 wiki 质量
wiki lint

# 常见问题：
# - 孤立页面（无入链）
# - 断链（指向不存在的页面）
# - 过短页面（< 100 字）
```

### 4. 统计信息

```powershell
# 查看 wiki 统计
wiki stats

# 输出示例：
# Total pages: 42
# Total links: 156
# Orphan pages: 3
# Average page length: 523 words
```

### 5. 配置管理

```powershell
# 查看当前配置
wiki config

# 交互式修改配置（带 TUI 界面）
wiki config set

# 直接修改配置
wiki config set language en

# 查看/修改语言
wiki language
```

---

## MCP 工具说明

AI 工具可以自动调用以下 MCP 工具：

### search_wiki
搜索 wiki 知识库并返回 AI 生成的答案

```python
# AI 内部调用
search_wiki(query="transformer 的核心思想")
```

### get_page
获取指定页面内容

```python
get_page(slug="concept-self-attention")
```

### get_backlinks
获取反向链接

```python
get_backlinks(slug="concept-transformer")
```

### get_thread
获取 thread 详情

```python
get_thread(thread_id="memory-leak")
```

### get_recent_threads
获取最近的 threads

```python
get_recent_threads(limit=10)
```

### get_decisions
获取决策记录

```python
get_decisions(limit=20)
```

---

## 故障排查

### 问题 1：找不到 wiki 命令

**症状**：`wiki: command not found` 或 `Get-Command wiki` 无输出

**解决**：

```powershell
# 1. 检查是否安装
pip list | Select-String wiki

# 2. 重新安装
cd C:\Users\<你的用户名>\Documents\llmwiki\cli
pip install -e .

# 3. 验证安装
Get-Command wiki
```

### 问题 2：AI 工具无法调用 wiki

**症状**：Claude Code 说"我无法访问你的 wiki"

**解决**：

```powershell
# 1. 检查 MCP 配置
wiki mcp serve --test

# 2. 查看 Claude Code 配置文件
Get-Content C:\Users\<你的用户名>\.claude\settings.json | ConvertFrom-Json | Select-Object -ExpandProperty mcpServers

# 3. 重新配置
wiki mcp setup

# 4. 重启 Claude Code
```

### 问题 3：搜索结果为空

**症状**：AI 调用 search_wiki 返回空结果

**解决**：

```powershell
# 1. 检查是否有 wiki 页面
wiki list

# 2. 如果没有，运行 ingest
wiki ingest

# 3. 检查活跃领域
wiki domain list

# 4. 切换到正确的领域
wiki domain use ai
```

### 问题 4：运行 `wiki mcp serve` 报错

**症状**：`Received exception from stream: JSON parsing error`

**原因**：`wiki mcp serve` 不应该直接在终端运行，它是给 AI 工具调用的。

**解决**：

- **不要**直接运行 `wiki mcp serve`
- AI 工具会自动启动它作为子进程
- 如果想测试配置，用 `wiki mcp serve --test`

### 问题 5：Provider API 调用失败

**症状**：`wiki ingest` 报错 "API call failed"

**解决**：

```powershell
# 1. 检查 provider 配置
wiki config

# 2. 测试 API 连接
wiki query "test"

# 3. 如果是火山方舟等第三方，检查 base_url
wiki config set

# 选择 providers 相关配置项修改
```

### 问题 6：中文乱码

**症状**：命令输出显示乱码

**解决**：

```powershell
# 设置 PowerShell 编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 或者在配置文件中设置
# C:\Users\<你的用户名>\Documents\PowerShell\Microsoft.PowerShell_profile.ps1
```

---

## 最佳实践

### 1. 文件命名规范

```
raw/
  YYYY-MM-DD-topic-name.md        # 日期 + 主题
  transformers/
    2026-04-24-attention-paper.md # 分类 + 日期 + 主题
```

### 2. Wiki 页面类型

- **concept-xxx.md** - 概念解释
- **solution-xxx.md** - 解决方案
- **entity-xxx.md** - 人物/组织/工具
- **comparison-xxx.md** - 对比分析
- **summary-xxx.md** - 总结归纳

### 3. Thread 使用建议

- **优先级**：
  - `high` - 阻塞性问题、紧急需求
  - `medium` - 常规任务
  - `low` - 优化、重构

- **标签**：
  - 类型：`bug`, `feature`, `refactor`, `docs`
  - 领域：`frontend`, `backend`, `infra`
  - 状态：`blocked`, `review`, `testing`

- **依赖关系**：
  - 用于表示"必须先完成 A 才能做 B"
  - 避免循环依赖

### 4. 定期维护

```powershell
# 每周运行一次
wiki lint              # 检查质量问题
wiki stats             # 查看统计
wiki orphans           # 清理孤立页面
```

---

## 常用命令速查

```powershell
# 配置
wiki config                    # 查看配置
wiki config set                # 交互式修改配置
wiki domain list               # 查看所有领域
wiki domain use ai             # 切换领域

# 内容管理
wiki list                      # 列出所有页面
wiki ingest                    # 生成 wiki 页面
wiki query "问题"              # 查询 wiki

# MCP
wiki mcp setup                 # 配置 Claude Code
wiki mcp serve --test          # 测试配置

# Thread
wiki thread list               # 列出所有 threads
wiki thread create <id>        # 创建 thread
wiki thread show <id>          # 查看 thread
wiki thread update <id>        # 更新 thread

# 质量检查
wiki lint                      # 检查质量
wiki stats                     # 查看统计
wiki orphans                   # 孤立页面
wiki broken                    # 断链
```

---

## 更多资源

- **GitHub**: https://github.com/ProfilePlus/llm-wiki
- **MCP 文档**: https://modelcontextprotocol.io/
- **问题反馈**: https://github.com/ProfilePlus/llm-wiki/issues

---

## 附录：配置文件位置

| 文件 | 路径 (Windows) |
|------|----------------|
| Wiki 配置 | `C:\Users\<用户名>\.wiki\config.json` |
| Wiki 数据 | `D:\AI\llm-wiki\` (可自定义) |
| Claude Code | `C:\Users\<用户名>\.claude\settings.json` |
| Python Scripts | `C:\Users\<用户名>\AppData\Local\Programs\Python\Python312\Scripts\` |
