# Wiki MCP Server - Quick Reference

## Installation
```bash
cd ~/Documents/llmwiki/cli
pip install -e .
```

## MCP Commands

### Server Management
```bash
wiki mcp serve          # Start in foreground (stdio mode)
wiki mcp start          # Start as daemon
wiki mcp stop           # Stop daemon
wiki mcp status         # Check status
wiki mcp setup          # Generate config for all tools
wiki mcp setup --tool cc    # Generate config for Claude Code only
```

### Thread Management
```bash
# Create thread
wiki thread create THREAD_ID --title "Title" --priority high --tags "tag1,tag2"

# List threads
wiki thread list

# Show thread
wiki thread show THREAD_ID

# Update thread
wiki thread update THREAD_ID --status in_progress --priority high

# Add message
wiki thread add-message THREAD_ID "Message content"

# Add dependency
wiki thread add-dependency THREAD_ID DEPENDENCY_ID
```

## MCP Tools (for AI)

### search_wiki
Search wiki and get AI-generated answer.
```json
{
  "name": "search_wiki",
  "arguments": {
    "query": "How do I implement authentication?"
  }
}
```

### get_page
Get wiki page content by slug.
```json
{
  "name": "get_page",
  "arguments": {
    "slug": "api-design"
  }
}
```

### get_backlinks
Get pages linking to target page.
```json
{
  "name": "get_backlinks",
  "arguments": {
    "slug": "database-schema"
  }
}
```

### get_thread
Get thread details by ID.
```json
{
  "name": "get_thread",
  "arguments": {
    "thread_id": "feat-001"
  }
}
```

### get_recent_threads
Get recent threads.
```json
{
  "name": "get_recent_threads",
  "arguments": {
    "limit": 10
  }
}
```

### get_decisions
Get recent decisions.
```json
{
  "name": "get_decisions",
  "arguments": {
    "limit": 20
  }
}
```

## Configuration

### Claude Code (~/.claude/settings.json)
```json
{
  "mcpServers": {
    "wiki": {
      "command": "/usr/local/bin/wiki",
      "args": ["mcp", "serve"]
    }
  }
}
```

### CodeX (~/.codex/config.json)
```json
{
  "mcpServers": {
    "wiki": {
      "command": "/usr/local/bin/wiki",
      "args": ["mcp", "serve"]
    }
  }
}
```

### Gemini (~/.gemini/mcp.json)
```json
{
  "servers": {
    "wiki": {
      "command": "/usr/local/bin/wiki",
      "args": ["mcp", "serve"]
    }
  }
}
```

## File Structure
```
~/wiki-data/
├── {domain}/
│   ├── wiki/           # Wiki pages
│   ├── raw/            # Source documents
│   ├── threads/        # Thread JSON files
│   └── log.md          # Activity log
└── .daemon/
    ├── mcp.pid         # Process ID
    └── mcp.log         # Server logs
```

## Troubleshooting

### Check status
```bash
wiki status
wiki mcp status
```

### View logs
```bash
tail -f ~/wiki-data/.daemon/mcp.log
```

### Restart server
```bash
wiki mcp stop
wiki mcp start
```

## Performance

- Cache TTL: 5 minutes (default)
- Search cache: 10 minutes
- Hit rate: 80-95% typical
- Search: 100-500ms (first), 1-5ms (cached)
- Page get: 10-50ms (first), <1ms (cached)

## Documentation

- Full docs: `wiki_cli/mcp/README.md`
- Setup guide: `MCP_SETUP.md`
- Implementation: `IMPLEMENTATION_SUMMARY.md`
