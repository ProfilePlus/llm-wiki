# Wiki CLI

> Local knowledge management system based on Karpathy's LLM Wiki pattern

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![中文文档](https://img.shields.io/badge/docs-中文-red)](README.md)

A lightweight, zero-overhead local LLM Wiki tool. Let AI maintain a persistent, cross-referenced knowledge base instead of re-deriving answers from raw documents every time.

## Features

- 📥 **AI-Powered Ingestion** — Automatically compile source documents into structured wiki pages
- 🔍 **Smart Querying** — Answer questions from compiled wiki with automatic page citations
- 🩺 **Health Checks** — Detect broken links, orphan pages, missing concepts with suggestions
- 🔗 **Auto Cross-Referencing** — Automatic `[[wikilink]]` connections between pages
- 🌐 **Multi-Provider** — Anthropic, OpenAI, custom base_url (Volcengine, etc.)
- 🈳 **Bilingual** — Configurable language (Chinese/English) for all AI operations
- 📊 **Zero Overhead** — Pure Markdown files, no database, no vector store, no Docker
- 🎨 **Dual Output** — Rich terminal UI + JSON for Claude Code integration

## Quick Start

### Install

```bash
git clone https://github.com/ProfilePlus/llm-wiki.git
cd llm-wiki
pip install -e .
```

### Configure

```bash
# Initialize
wiki init

# Add a knowledge domain
wiki domain add ai

# Add an LLM provider
wiki provider add claude
# Follow prompts:
#   type: anthropic
#   api_key: your-key
#   model: claude-sonnet-4-20250514

# Set language (default: Chinese)
wiki language en   # English
wiki language zh   # Chinese
```

### Use

```bash
# Ingest a source document
wiki ingest ~/Downloads/paper.md --topic transformers

# Query the wiki
wiki query "What is Transformer"

# Health check
wiki lint

# View stats
wiki stats
```

## Commands

### Configuration
| Command | Description |
|---------|-------------|
| `wiki init` | Initialize data directory |
| `wiki domain add/list/use` | Manage knowledge domains |
| `wiki provider add/list/use` | Manage LLM providers |
| `wiki language [zh\|en]` | View or set language |
| `wiki config` | View/modify configuration |
| `wiki status` | Show status dashboard |

### AI Operations
| Command | Description |
|---------|-------------|
| `wiki ingest <file> --topic <topic>` | Ingest source document |
| `wiki query "<question>"` | Query the wiki |
| `wiki lint` | Health check |

### File Management
| Command | Description |
|---------|-------------|
| `wiki scan` | Scan raw/ for files |
| `wiki list [--type]` | List wiki pages |
| `wiki links <page>` | Show outgoing links |
| `wiki backlinks <page>` | Show incoming links |
| `wiki orphans` | Find orphan pages |
| `wiki broken` | Find broken links |
| `wiki index` | Rebuild index.md |
| `wiki graph` | Export link graph |
| `wiki stats` | Statistics |
| `wiki log` | View operation log |

## Data Structure

```
D:/AI/llm-wiki/
  ai/                              # Domain
    raw/                           # Immutable source documents
      transformers/
        2026-04-23-paper.md
    wiki/                          # LLM-compiled wiki
      index.md                     # Index
      log.md                       # Operation log
      transformers/
        summary-paper.md           # Summary page
        entity-vaswani.md          # Entity page
        concept-transformer.md     # Concept page
        comparison-bert-vs-gpt.md  # Comparison page
```

## Page Types

| Prefix | Description |
|--------|-------------|
| `summary-*` | Source document summary |
| `entity-*` | Named entities (people, tools, models, orgs) |
| `concept-*` | Thematic concepts |
| `comparison-*-vs-*` | Side-by-side comparisons |
| `synthesis-*` | Higher-order insights |
| `archive-*` | Archived high-value query results |

## Language Configuration

```bash
# View current language
wiki language

# Set to English (all AI operations will use English)
wiki language en

# Set to Chinese (default)
wiki language zh
```

Language setting affects all AI operations:
- **ingest**: Generated wiki pages use the configured language
- **query**: Answers are in the configured language
- **lint**: Health check reports use the configured language

## Claude Code Integration

After installation, just say in Claude Code:
- "Add this article to my wiki"
- "What does my wiki say about Transformer"
- "Check my wiki health"

## How It Works

Based on [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f):

1. **Ingest**: LLM reads source documents and compiles them into structured wiki pages
2. **Query**: Answers questions from compiled wiki, not re-derived from raw documents each time
3. **Lint**: Checks wiki health — broken links, orphan pages, missing concepts

The key advantage: knowledge is **compiled, persistent, and cross-referenced**, not re-derived on every query.

## Tech Stack

- Python 3.12+
- Click 8.3.3
- Rich 15.0.0
- Anthropic SDK + OpenAI SDK

## License

MIT License

## Credits

Inspired by [Andrej Karpathy's LLM Wiki Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
