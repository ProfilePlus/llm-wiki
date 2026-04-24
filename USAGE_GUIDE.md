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
- 已安装 wiki CLI：`pip install -e .`
- 至少一个 AI 工具（Claude Code / CodeX CLI / Gemini CLI）

### 5 分钟快速体验

```bash
# 1. 初始化 wiki
wiki init

# 2. 创建第一个领域
wiki domain add ai

# 3. 配置 provider（以火山方舟为例）
wiki provider add volcengine

# 4. 配置 MCP（自动配置三个工具）
wiki mcp setup

# 5. 启动 MCP 服务（可选，推荐）
wiki mcp start

# 6. 在 Claude Code 中测试
# 打开 Claude Code，输入："搜索我的 wiki 中关于 transformer 的内容"
```

---

## 初始化配置

### 1. 运行初始化向导

```bash
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

### 2. 创建知识领域

```bash
# 创建多个领域
wiki domain add ai        # AI 相关知识
wiki domain add work      # 工作项目
wiki domain add life      # 生活记录

# 切换活跃领域
wiki domain use ai

# 查看所有领域
wiki domain list
```

### 3. 添加原始文档

```bash
# 手动添加 markdown 文件到 raw/ 目录
cp my-notes.md D:/AI/llm-wiki/ai/raw/

# 或者直接在 raw/ 目录下创建文件
# 文件命名建议：YYYY-MM-DD-topic-name.md
```

### 4. 生成 wiki 页面

```bash
# 处理 raw/ 目录下的所有文档
wiki ingest

# 处理特定文件
wiki ingest D:/AI/llm-wiki/ai/raw/2026-04-24-transformer.md
```

---

## 配置 AI 工具

### 方式一：自动配置（推荐）

```bash
# 自动配置所有三个工具
wiki mcp setup

# 或者只配置特定工具
wiki mcp setup --tool cc        # Claude Code
wiki mcp setup --tool codex     # CodeX CLI
wiki mcp setup --tool gemini    # Gemini CLI
```

### 方式二：手动配置

#### Claude Code

编辑 `~/.claude/settings.json`：

```json
{
  "mcpServers": {
    "wiki": {
      "command": "wiki",
      "args": ["mcp", "serve"]
    }
  }
}
```

#### CodeX CLI

编辑 `~/.codex/config.toml`：

```toml
[mcp_servers.wiki]
command = "wiki"
args = ["mcp", "serve"]
```

#### Gemini CLI

编辑 `~/.gemini/settings.json`：

```json
{
  "mcpServers": {
    "wiki": {
      "command": "wiki",
      "args": ["mcp", "serve"],
      "env": {}
    }
  }
}
```

### 验证配置

```bash
# 检查 MCP 服务是否正常
wiki mcp serve

# 应该看到：
# MCP server running on stdio...
# (按 Ctrl+C 退出)
```

在 AI 工具中测试：

```
你: "搜索我的 wiki"
AI: [自动调用 search_wiki 工具]
AI: "找到以下页面：..."
```

---

## 日常使用流程

### 典型工作流

```
1. 记录原始信息
   ↓
2. AI 提炼知识
   ↓
3. 跨工具协作
   ↓
4. 持续积累
```

### 场景 1：学习新技术

```bash
# 1. 保存学习笔记到 raw/
echo "# Transformer 架构学习" > D:/AI/llm-wiki/ai/raw/2026-04-24-transformer.md
# ... 编辑笔记 ...

# 2. 让 AI 提炼知识
wiki ingest D:/AI/llm-wiki/ai/raw/2026-04-24-transformer.md

# 3. 在 Claude Code 中使用
# 你: "根据我的 wiki，解释 self-attention 机制"
# CC: [自动查询 wiki] "根据你的笔记，self-attention..."
```

### 场景 2：跨工具协作

```bash
# 1. CodeX 诊断问题
# 在 CodeX 中: "分析这个内存泄漏"
# CodeX: 发现 EventEmitter 监听器未清理

# 2. 创建 thread 记录
wiki thread create memory-leak \
  --title "API 服务器内存泄漏" \
  --priority high \
  --tags "bug,performance"

# 3. Claude Code 修复
# 在 CC 中: "继续修复内存泄漏问题"
# CC: [查询 thread] "我看到 CodeX 已经定位了问题..."

# 4. 更新 thread
wiki thread add-message memory-leak "已使用 WeakMap 修复" \
  --tool cc --action fix

# 5. Gemini 优化
# 在 Gemini 中: "优化内存泄漏修复方案"
# Gemini: [查询 thread] "基于 CC 的修复..."
```

### 场景 3：查询历史决策

```bash
# 在任何 AI 工具中
你: "我们之前为什么选择 WeakMap 而不是手动清理？"
AI: [查询 thread decisions] "根据 thread memory-leak 的决策记录..."
```

---

## 高级功能

### 1. Thread 管理

```bash
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

### 2. 常驻 Daemon 模式

```bash
# 启动 daemon（推荐，避免每次启动开销）
wiki mcp start

# 查看状态
wiki mcp status

# 停止 daemon
wiki mcp stop

# 查看日志
tail -f ~/.wiki/.daemon/mcp.log  # Unix
type %USERPROFILE%\.wiki\.daemon\mcp.log  # Windows
```

### 3. 链接图分析

```bash
# 查看页面的反向链接
wiki links <page-slug> --backlinks

# 查看孤立页面
wiki links --orphans

# 导出链接图
wiki graph --format dot > wiki-graph.dot
```

### 4. 质量检查

```bash
# 检查 wiki 质量
wiki lint

# 常见问题：
# - 孤立页面（无入链）
# - 断链（指向不存在的页面）
# - 过短页面（< 100 字）
```

### 5. 统计信息

```bash
# 查看 wiki 统计
wiki stats

# 输出示例：
# Total pages: 42
# Total links: 156
# Orphan pages: 3
# Average page length: 523 words
```

---

## MCP 工具说明

AI 工具可以自动调用以下 MCP 工具：

### search_wiki
搜索 wiki 知识库

```python
# AI 内部调用
search_wiki(query="transformer", limit=10)
```

### get_page
获取指定页面内容

```python
get_page(page_slug="concept-self-attention")
```

### get_backlinks
获取反向链接

```python
get_backlinks(page_slug="concept-transformer")
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

---

## 故障排查

### 问题 1：AI 工具无法调用 wiki

**症状**：AI 说"我无法访问你的 wiki"

**解决**：

```bash
# 1. 检查 MCP 配置
wiki mcp setup --tool cc

# 2. 验证 wiki 命令可用
which wiki  # Unix
where wiki  # Windows

# 3. 手动测试 MCP 服务
wiki mcp serve
# 应该看到 "MCP server running on stdio..."

# 4. 重启 AI 工具
```

### 问题 2：搜索结果为空

**症状**：AI 调用 search_wiki 返回空结果

**解决**：

```bash
# 1. 检查是否有 wiki 页面
wiki list

# 2. 如果没有，运行 ingest
wiki ingest

# 3. 检查活跃领域
wiki domain list

# 4. 切换到正确的领域
wiki domain use ai
```

### 问题 3：Daemon 启动失败

**症状**：`wiki mcp start` 报错

**解决**：

```bash
# 1. 检查是否已经在运行
wiki mcp status

# 2. 如果卡住，强制停止
wiki mcp stop

# 3. 查看日志
cat ~/.wiki/.daemon/mcp.log  # Unix
type %USERPROFILE%\.wiki\.daemon\mcp.log  # Windows

# 4. 清理 PID 文件
rm ~/.wiki/.daemon/mcp.pid  # Unix
del %USERPROFILE%\.wiki\.daemon\mcp.pid  # Windows
```

### 问题 4：Windows 下 prompt_toolkit 报错

**症状**：`NoConsoleScreenBufferError`

**解决**：

在 PowerShell 或 cmd 中运行，不要用 Git Bash：

```powershell
# PowerShell
wiki config set

# 或者 cmd
cmd /c wiki config set
```

### 问题 5：Provider API 调用失败

**症状**：`wiki ingest` 报错 "API call failed"

**解决**：

```bash
# 1. 检查 provider 配置
wiki provider list

# 2. 测试 API 连接
wiki query "test"

# 3. 检查 API key 是否正确
wiki config

# 4. 如果是火山方舟等第三方，检查 base_url
wiki provider update volcengine --base-url "https://ark.cn-beijing.volces.com/api/coding"
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

```bash
# 每周运行一次
wiki lint              # 检查质量问题
wiki stats             # 查看统计
wiki links --orphans   # 清理孤立页面
```

---

## 示例：完整工作流

```bash
# === 第一天：学习 Transformer ===

# 1. 记录学习笔记
vim D:/AI/llm-wiki/ai/raw/2026-04-24-transformer.md

# 2. 生成 wiki
wiki ingest D:/AI/llm-wiki/ai/raw/2026-04-24-transformer.md

# 3. 在 Claude Code 中使用
# 你: "根据我的 wiki，用简单的语言解释 transformer"
# CC: [查询 wiki] "根据你的笔记，transformer 是..."

# === 第二天：实现项目 ===

# 4. 在 CodeX 中诊断
# 你: "这个 attention 实现有什么问题？"
# CodeX: "发现性能瓶颈..."

# 5. 创建 thread
wiki thread create attention-perf \
  --title "Attention 性能优化" \
  --priority high \
  --tags "performance,transformer"

# 6. 在 CC 中修复
# 你: "继续优化 attention 性能"
# CC: [查询 thread] "CodeX 已经定位了问题..."

# 7. 更新 thread
wiki thread add-message attention-perf "使用 flash attention 优化" \
  --tool cc --action optimization

# === 第三天：总结 ===

# 8. 在 Gemini 中总结
# 你: "总结这次 attention 优化的经验"
# Gemini: [查询 thread + wiki] "这次优化的关键点是..."

# 9. 保存总结到 wiki
wiki ingest D:/AI/llm-wiki/ai/raw/2026-04-26-attention-optimization.md

# 10. 关闭 thread
wiki thread update attention-perf --status closed
```

---

## 更多资源

- **GitHub**: https://github.com/ProfilePlus/llm-wiki
- **MCP 文档**: https://modelcontextprotocol.io/
- **问题反馈**: https://github.com/ProfilePlus/llm-wiki/issues

---

## 附录：配置文件位置

| 文件 | 路径 |
|------|------|
| Wiki 配置 | `~/.wiki/config.json` |
| Wiki 数据 | `D:/AI/llm-wiki/` (可自定义) |
| Claude Code | `~/.claude/settings.json` |
| CodeX CLI | `~/.codex/config.toml` |
| Gemini CLI | `~/.gemini/settings.json` |
| Daemon PID | `~/.wiki/.daemon/mcp.pid` |
| Daemon 日志 | `~/.wiki/.daemon/mcp.log` |
