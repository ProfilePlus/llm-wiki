"""wiki ingest - Ingest source file or URL into wiki."""

import click
import subprocess
import tempfile
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ..context import WikiContext
from ..core.ingest_engine import ingest_file_sync
from ..output import is_machine_mode, output_json

console = Console()

# 强制 UTF-8 输出，避免 Windows GBK 编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

FETCH_SCRIPT = Path.home() / ".claude" / "skills" / "web-content-fetcher" / "scripts" / "fetch.py"

# 需要 --stealth 的域名
STEALTH_DOMAINS = ["mp.weixin.qq.com", "zhuanlan.zhihu.com", "juejin.cn"]


def _clean_topic(raw: str) -> str:
    """清洗 LLM 返回的 topic 名称"""
    # 只取第一行
    topic = raw.strip().split("\n")[0].strip()
    # 去掉引号、反引号、句号等
    topic = topic.strip("\"'`.,;:!?()[]{}。，；：！？")
    topic = topic.lower().replace(" ", "-").replace("_", "-")
    # 只保留字母数字和连字符
    topic = "".join(c for c in topic if c.isalnum() or c == "-")
    # 去掉首尾和连续的连字符
    topic = "-".join(part for part in topic.split("-") if part)
    return topic[:30] if topic else "general"


@click.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("--topic", default=None, help="topic 目录名（不指定则由 AI 自动判断）")
@click.pass_context
def ingest(ctx, source, topic):
    """摄入源文档到 wiki。"""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.active_domain:
        console.print("[red]错误：未设置活跃领域。运行 wiki domain use <name>[/red]")
        return

    if not wiki_ctx.active_provider:
        console.print("[red]错误：未设置活跃 provider。运行 wiki provider use <name>[/red]")
        return

    try:
        provider = wiki_ctx.create_provider()
    except Exception as e:
        console.print(f"[red]Provider 初始化失败: {e}[/red]")
        return

    source_path = Path(source)
    domain_path = wiki_ctx.domain_path

    if not topic:
        with console.status("[cyan]AI 正在识别文档主题...[/cyan]", spinner="dots"):
            try:
                import asyncio
                file_content = source_path.read_text(encoding="utf-8")[:2000]
                topic = asyncio.run(provider.complete(
                    system="你是一个分类助手。根据文档内容，返回一个简短的英文 topic 名称。要求：1-3 个单词，小写，用连字符分隔。例如：ai-tools、web-dev、cloud-infra、machine-learning。只输出 topic 名称这一个词，不要任何解释、标点或换行。",
                    messages=[{"role": "user", "content": file_content}],
                    max_tokens=20,
                ))
                topic = _clean_topic(topic)
            except Exception:
                topic = "general"
        console.print(f"[green]✓[/green] 主题识别: [cyan]{topic}[/cyan]")

    if not is_machine_mode():
        console.print(f"[cyan]正在摄入[/cyan] {source_path.name} → topic: {topic}...")

    try:
        result = ingest_file_sync(source_path, topic, domain_path, provider, wiki_ctx.language)
    except Exception as e:
        if is_machine_mode():
            output_json({"error": str(e)})
        else:
            console.print(f"[red]摄入失败: {e}[/red]")
        return

    if "error" in result:
        if is_machine_mode():
            output_json(result)
        else:
            console.print(f"[red]错误: {result['error']}[/red]")
        return

    if is_machine_mode():
        output_json(result)
        return

    # Rich display
    console.print(f"[green]✓[/green] 摄入完成")
    console.print(f"  Raw: {result['raw_path']}")
    console.print()

    if result["created"]:
        table = Table(title=f"创建的页面 ({len(result['created'])})")
        table.add_column("路径", style="cyan")
        for p in result["created"]:
            table.add_row(p)
        console.print(table)

    if result["updated"]:
        table = Table(title=f"更新的页面 ({len(result['updated'])})")
        table.add_column("路径", style="yellow")
        for p in result["updated"]:
            table.add_row(p)
        console.print(table)

    console.print(f"\n[dim]{result['log_entry']}[/dim]")


@click.command("ingest-url")
@click.argument("url")
@click.option("--topic", default=None, help="topic 目录名（不指定则由 AI 自动判断）")
@click.pass_context
def ingest_url(ctx, url, topic):
    """抓取网页内容并摄入到 wiki。"""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.active_domain:
        console.print("[red]错误：未设置活跃领域[/red]")
        return

    if not wiki_ctx.active_provider:
        console.print("[red]错误：未设置活跃 provider[/red]")
        return

    # 1. 抓取网页
    if not FETCH_SCRIPT.exists():
        console.print("[red]错误: web-content-fetcher skill 未安装[/red]")
        console.print("[dim]请先安装: https://github.com/shirenchuang/web-content-fetcher[/dim]")
        return

    stealth = any(d in url for d in STEALTH_DOMAINS)

    # 图片保存目录
    image_dir = wiki_ctx.domain_path / "wiki" / "assets" / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    cmd = ["python", str(FETCH_SCRIPT), url, "15000", "--download-images", str(image_dir)]
    if stealth:
        cmd.append("--stealth")

    import os
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    with console.status("[cyan]正在抓取网页...[/cyan]", spinner="dots"):
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=180, env=env)
            content = result.stdout.decode("utf-8", errors="ignore").strip()
        except subprocess.TimeoutExpired:
            console.print("[red]抓取超时（60s）[/red]")
            return
        except Exception as e:
            console.print(f"[red]抓取失败: {e}[/red]")
            return

    if not content or len(content) < 100:
        console.print("[red]抓取内容为空或太短[/red]")
        stderr = result.stderr.decode("utf-8", errors="ignore") if result.stderr else ""
        if stderr:
            console.print(f"[dim]{stderr[:200]}[/dim]")
        return

    console.print(f"[green]✓[/green] 抓取成功 ({len(content)} 字符)")

    # 2. 如果没指定 topic，让 AI 自动判断
    if not topic:
        with console.status("[cyan]AI 正在识别文章主题...[/cyan]", spinner="dots"):
            try:
                provider = wiki_ctx.create_provider()
                import asyncio
                topic = asyncio.run(provider.complete(
                    system="你是一个分类助手。根据文章内容，返回一个简短的英文 topic 名称。要求：1-3 个单词，小写，用连字符分隔。例如：ai-tools、web-dev、cloud-infra、machine-learning。只输出 topic 名称这一个词，不要任何解释、标点或换行。",
                    messages=[{"role": "user", "content": content[:2000]}],
                    max_tokens=20,
                ))
                topic = _clean_topic(topic)
            except Exception:
                topic = "general"
        console.print(f"[green]✓[/green] 主题识别: [cyan]{topic}[/cyan]")

    # 3. 保存为临时文件
    from urllib.parse import urlparse
    slug = urlparse(url).path.strip("/").replace("/", "-")[:50] or "web-article"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", encoding="utf-8", delete=False, prefix=f"{slug}-") as f:
        f.write(f"# {slug}\n\n> 来源: {url}\n\n{content}")
        tmp_path = Path(f.name)

    # 4. 调用 ingest
    with console.status("[cyan]AI 正在提炼知识点...[/cyan]", spinner="dots"):
        try:
            provider = wiki_ctx.create_provider()
            result = ingest_file_sync(tmp_path, topic, wiki_ctx.domain_path, provider, wiki_ctx.language)
        except Exception as e:
            console.print(f"[red]摄入失败: {e}[/red]")
            return
        finally:
            os.unlink(tmp_path)

    if "error" in result:
        console.print(f"[red]错误: {result['error']}[/red]")
        return

    console.print(f"[green]✓[/green] 摄入完成")
    console.print(f"  Raw: {result['raw_path']}")

    if result["created"]:
        table = Table(title=f"创建的页面 ({len(result['created'])})")
        table.add_column("路径", style="cyan")
        for p in result["created"]:
            table.add_row(p)
        console.print(table)

    if result["updated"]:
        table = Table(title=f"更新的页面 ({len(result['updated'])})")
        table.add_column("路径", style="yellow")
        for p in result["updated"]:
            table.add_row(p)
        console.print(table)

    console.print(f"\n[dim]{result['log_entry']}[/dim]")
