# Wiki CLI

> 基于 Karpathy LLM Wiki 模式的本地知识管理系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

一个轻量级、零资源占用的本地 LLM Wiki 工具。让 AI 帮你维护一个持久化、交叉引用的知识库，而非每次查询都重新检索原始文档。

## 核心特性

- 📥 **AI 驱动的知识摄入** — 自动将源文档编译为结构化 wiki 页面
- 🔍 **智能查询** — 基于编译后的 wiki 回答问题，自动引用相关页面
- 🩺 **健康检查** — 发现断链、孤儿页、缺失概念，给出改进建议
- 🔗 **自动交叉引用** — 使用 `[[wikilink]]` 格式自动建立页面间链接
- 🌐 **多 Provider 支持** — Anthropic、OpenAI、火山方舟等自定义 base_url
- 📊 **零资源占用** — 纯 Markdown 文件，无数据库、无向量库、无 Docker
- 🎨 **双输出模式** — 终端 Rich 格式 + Claude Code JSON 格式

## 快速开始

### 安装

```bash
git clone https://github.com/ProfilePlus/wiki-cli.git
cd wiki-cli
pip install -e .
```

### 配置

```bash
# 初始化
wiki init

# 添加领域
wiki domain add ai

# 添加 LLM provider
wiki provider add claude
# 按提示输入 API key、model 等信息
```

### 使用

```bash
# 摄入源文档
wiki ingest ~/Downloads/paper.md --topic transformers

# 查询知识
wiki query "什么是 Transformer"

# 健康检查
wiki lint

# 查看统计
wiki stats
```

## 命令列表

### 配置与管理
- `wiki init` — 初始化数据目录
- `wiki domain add/list/use` — 管理知识领域
- `wiki provider add/list/use` — 管理 LLM provider
- `wiki config` — 查看/修改配置
- `wiki status` — 显示状态面板

### AI 核心操作
- `wiki ingest <file> --topic <topic>` — 摄入源文档
- `wiki query "<question>"` — 查询 wiki
- `wiki lint` — 健康检查

### 文件管理
- `wiki scan` — 扫描 raw/ 文件
- `wiki list [--type]` — 列出 wiki 页面
- `wiki links <page>` — 查看出链
- `wiki backlinks <page>` — 查看反向链接
- `wiki orphans` — 找孤儿页
- `wiki broken` — 找断链
- `wiki index` — 重建 index.md
- `wiki graph` — 导出链接图
- `wiki stats` — 统计信息
- `wiki log` — 查看操作日志

## 数据结构

```
D:/AI/llm-wiki/
  ai/                          # 领域
    raw/                       # 原始文档（不可变）
      transformers/
        2026-04-23-paper.md
    wiki/                      # LLM 编译的 wiki
      index.md                 # 索引
      log.md                   # 操作日志
      transformers/
        summary-paper.md       # 摘要页
        entity-vaswani.md      # 实体页
        concept-transformer.md # 概念页
        comparison-bert-vs-gpt.md  # 对比页
```

## 页面类型

- `summary-*` — 源文档摘要
- `entity-*` — 命名实体（人物、工具、模型、组织）
- `concept-*` — 主题概念
- `comparison-*-vs-*` — 对比分析
- `synthesis-*` — 综合洞见
- `archive-*` — 高价值查询结果归档

## Claude Code 集成

安装后，在 Claude Code 中直接说：
- "把这篇文章加到我的 wiki"
- "查一下我的 wiki 里怎么说 Transformer"
- "检查我的 wiki 健康度"

Skill 文件位于 `~/.claude/skills/wiki/`。

## 工作原理

基于 [Karpathy 的 LLM Wiki 思路](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)：

1. **Ingest**：LLM 读取源文档，编译为结构化 wiki 页面（summary/entity/concept/comparison/synthesis）
2. **Query**：基于编译后的 wiki 回答问题，而非每次重新检索原始文档
3. **Lint**：检查 wiki 健康度，发现断链、孤儿页、缺失概念

核心优势：知识是**编译后的、持久化的、交叉引用的**，而非每次查询都重新推导。

## 技术栈

- Python 3.12+
- Click 8.3.3 (CLI 框架)
- Rich 15.0.0 (终端 UI)
- Anthropic SDK (Claude API)
- OpenAI SDK (OpenAI 兼容接口)

## 配置文件

配置存储在 `~/.wiki/config.json`：

```json
{
  "data_dir": "D:/AI/llm-wiki",
  "active_domain": "ai",
  "active_provider": "claude",
  "providers": {
    "claude": {
      "type": "anthropic",
      "api_key": "sk-ant-xxx",
      "model": "claude-sonnet-4-20250514"
    }
  }
}
```

## 示例

### 摄入一篇论文

```bash
$ wiki ingest ~/Downloads/attention-paper.pdf --topic transformers

✓ 摄入完成
  Raw: ai/raw/transformers/2026-04-23-attention-paper.md

创建的页面 (5)
  wiki/transformers/summary-attention-paper.md
  wiki/transformers/entity-vaswani.md
  wiki/transformers/concept-transformer.md
  wiki/transformers/concept-self-attention.md
  wiki/transformers/entity-bert.md

摄入论文 Attention Is All You Need，创建 5 个页面
```

### 查询知识

```bash
$ wiki query "什么是 Transformer"

Transformer 是由 Vaswani 等人在 2017 年提出的深度学习架构...

参考页面:
- [[concept-transformer]]
- [[entity-vaswani]]
- [[summary-attention-paper]]
```

### 健康检查

```bash
$ wiki lint

Wiki 统计
  总页面: 13
  孤儿页: 1
  断链: 2

发现 3 个问题
  medium  broken_link  concept-transformer 链接到不存在的 concept-rnn
  low     orphan       summary-test 没有入链

建议新建页面 (2)
  • [concept] concept-rnn: 作为对比概念缺失
  • [comparison] comparison-bert-vs-gpt: 填补对比类型空白
```

## 许可证

MIT License

## 致谢

灵感来自 [Andrej Karpathy 的 LLM Wiki Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)。
