#!/usr/bin/env python3
"""Test script for MCP implementation."""

import sys
from pathlib import Path

# Add wiki_cli to path
sys.path.insert(0, str(Path(__file__).parent))

from wiki_cli.mcp.cache import WikiCache
from wiki_cli.context import WikiContext


def test_cache():
    """Test WikiCache functionality."""
    print("Testing WikiCache...")
    
    cache = WikiCache(default_ttl=1)
    
    # Test set/get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1", "Cache get failed"
    print("✓ Cache set/get works")
    
    # Test miss
    assert cache.get("nonexistent") is None, "Cache miss failed"
    print("✓ Cache miss works")
    
    # Test stats
    stats = cache.stats()
    assert stats["hits"] == 1, "Hit count wrong"
    assert stats["misses"] == 1, "Miss count wrong"
    print(f"✓ Cache stats: {stats}")
    
    # Test expiration
    import time
    time.sleep(1.1)
    assert cache.get("key1") is None, "Cache expiration failed"
    print("✓ Cache expiration works")
    
    # Test clear
    cache.set("key2", "value2")
    cache.clear()
    assert cache.get("key2") is None, "Cache clear failed"
    print("✓ Cache clear works")
    
    print("✓ All cache tests passed!\n")


def test_context():
    """Test WikiContext."""
    print("Testing WikiContext...")
    
    ctx = WikiContext()
    print(f"  Data dir: {ctx.data_dir}")
    print(f"  Active domain: {ctx.active_domain}")
    print(f"  Active provider: {ctx.active_provider}")
    print(f"  Language: {ctx.language}")
    
    if ctx.domain_path:
        print(f"  Domain path: {ctx.domain_path}")
        print(f"  Wiki path: {ctx.wiki_path}")
        print(f"  Raw path: {ctx.raw_path}")
    
    print("✓ WikiContext works\n")


def test_imports():
    """Test all imports."""
    print("Testing imports...")
    
    try:
        from wiki_cli.mcp.cache import WikiCache, CacheEntry
        print("✓ cache.py imports")
        
        from wiki_cli.mcp.tools import WikiTools
        print("✓ tools.py imports")
        
        from wiki_cli.mcp.server import WikiMCPServer, run_server
        print("✓ server.py imports")
        
        from wiki_cli.mcp.daemon import WikiDaemon
        print("✓ daemon.py imports")
        
        from wiki_cli.commands.mcp_cmd import mcp
        print("✓ mcp_cmd.py imports")
        
        from wiki_cli.commands.thread import thread
        print("✓ thread.py imports")
        
        print("✓ All imports successful!\n")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Wiki MCP Implementation Tests")
    print("=" * 60 + "\n")
    
    if not test_imports():
        print("\n✗ Tests failed - import errors")
        sys.exit(1)
    
    test_cache()
    test_context()
    
    print("=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Install dependencies: pip install -e .")
    print("2. Check status: wiki status")
    print("3. Start MCP server: wiki mcp serve")
    print("4. Generate config: wiki mcp setup")


if __name__ == "__main__":
    main()
