# Wiki MCP Server

MCP (Model Context Protocol) server implementation for Wiki CLI, enabling AI tools (Claude Code, CodeX, Gemini) to access wiki functionality.

## Features

### MCP Tools

1. **search_wiki** - Search wiki and get AI-generated answers
   - Input: `query` (string)
   - Returns: answer, cited_pages, page_count

2. **get_page** - Get wiki page content by slug
   - Input: `slug` (string)
   - Returns: slug, content, path

3. **get_backlinks** - Get pages linking to a target page
   - Input: `slug` (string)
   - Returns: slug, backlinks[]

4. **get_thread** - Get thread details by ID
   - Input: `thread_id` (string)
   - Returns: thread data (id, title, status, messages, etc.)

5. **get_recent_threads** - Get recent threads
   - Input: `limit` (integer, default: 10)
   - Returns: threads[]

6. **get_decisions** - Get recent decisions from decision log
   - Input: `limit` (integer, default: 20)
   - Returns: decisions[]

### Performance Features

- **Caching**: In-memory cache with TTL (default 5 minutes)
- **Cache Statistics**: Hit rate tracking
- **Incremental Updates**: Cache invalidation on updates

### Daemon Mode

- Background service for persistent MCP server
- PID file management
- Log file rotation
- Signal handling (SIGTERM, SIGINT)

## Usage

### Start MCP Server (Foreground)

```bash
wiki mcp serve
```

This starts the MCP server in stdio mode, suitable for direct integration with AI tools.

### Start MCP Server (Daemon)

```bash
wiki mcp start
```

Starts the server as a background daemon.

### Stop Daemon

```bash
wiki mcp stop
```

### Check Status

```bash
wiki mcp status
```

### Generate Configuration

```bash
# For all tools
wiki mcp setup

# For specific tool
wiki mcp setup --tool cc
wiki mcp setup --tool codex
wiki mcp setup --tool gemini
```

## Configuration

### Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "wiki": {
      "command": "/path/to/wiki",
      "args": ["mcp", "serve"],
      "env": {
        "WIKI_DOMAIN": "your-domain"
      }
    }
  }
}
```

### CodeX

Add to `~/.codex/config.json`:

```json
{
  "mcpServers": {
    "wiki": {
      "command": "/path/to/wiki",
      "args": ["mcp", "serve"]
    }
  }
}
```

### Gemini

Add to `~/.gemini/mcp.json`:

```json
{
  "servers": {
    "wiki": {
      "command": "/path/to/wiki",
      "args": ["mcp", "serve"]
    }
  }
}
```

## Thread Management

Threads provide persistent context for multi-turn conversations.

### Create Thread

```bash
wiki thread create THREAD_ID --title "Thread Title" --description "Description" --priority high --tags "tag1,tag2"
```

### List Threads

```bash
wiki thread list
```

### Show Thread

```bash
wiki thread show THREAD_ID
```

### Update Thread

```bash
wiki thread update THREAD_ID --status in_progress --priority high
```

### Add Message

```bash
wiki thread add-message THREAD_ID "Message content"
```

### Add Dependency

```bash
wiki thread add-dependency THREAD_ID DEPENDENCY_ID
```

## Thread Data Structure

Threads are stored as JSON files in `{domain}/threads/{thread_id}.json`:

```json
{
  "id": "thread-001",
  "title": "Feature Implementation",
  "description": "Implement new feature X",
  "priority": "high",
  "tags": ["feature", "backend"],
  "status": "in_progress",
  "created_at": "2024-04-23T10:00:00",
  "updated_at": "2024-04-23T15:30:00",
  "dependencies": ["thread-002"],
  "messages": [
    {
      "content": "Started implementation",
      "timestamp": "2024-04-23T10:05:00"
    }
  ]
}
```

## Architecture

```
wiki_cli/mcp/
├── __init__.py       # Package initialization
├── cache.py          # WikiCache class with TTL
├── tools.py          # WikiTools class (MCP tool implementations)
├── server.py         # WikiMCPServer class (MCP protocol)
├── daemon.py         # WikiDaemon class (background service)
└── README.md         # This file

wiki_cli/commands/
├── mcp_cmd.py        # CLI commands (serve, start, stop, status, setup)
└── thread.py         # Thread management commands
```

## Error Handling

All tools return error information in the response:

```json
{
  "error": "Error message"
}
```

Common errors:
- "Wiki directory does not exist"
- "Page not found: {slug}"
- "Thread not found: {thread_id}"
- "No active domain configured"

## Performance

- Cache hit rate typically >80% for repeated queries
- Search queries cached for 10 minutes
- Page content cached for 5 minutes
- Backlinks cached for 5 minutes
- Cache automatically invalidates on updates

## Development

### Adding New Tools

1. Add tool method to `WikiTools` class in `tools.py`
2. Register tool in `WikiMCPServer._register_handlers()` in `server.py`
3. Add tool schema to `list_tools()` handler

### Testing

```bash
# Test server startup
wiki mcp serve

# Test in another terminal
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | wiki mcp serve
```

## Troubleshooting

### Server won't start

- Check active domain: `wiki status`
- Check active provider: `wiki status`
- Check wiki directory exists: `ls ~/wiki-data/{domain}/wiki`

### Daemon issues

- Check logs: `cat ~/wiki-data/.daemon/mcp.log`
- Check PID: `cat ~/wiki-data/.daemon/mcp.pid`
- Force stop: `kill $(cat ~/wiki-data/.daemon/mcp.pid)`

### Cache issues

- Cache is in-memory only (cleared on restart)
- Adjust TTL in `WikiCache.__init__()` if needed
- Clear cache by restarting server

## License

Same as Wiki CLI project.
