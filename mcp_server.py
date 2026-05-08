#!/usr/bin/env python3
"""MCP server wrapping telegram-digest for claude-telegram-bot."""
import subprocess
import os
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from fastmcp import FastMCP

mcp = FastMCP("telegram-digest")
REPO_DIR = Path(__file__).parent
VENV_PYTHON = REPO_DIR / ".venv" / "bin" / "python"


@mcp.tool()
def list_digest_groups() -> list[str]:
    """List available digest channel groups from channels.yaml."""
    config_path = REPO_DIR / "channels.yaml"
    if not config_path.exists():
        return []
    config = yaml.safe_load(config_path.read_text())
    return list(config.get("groups", {}).keys())


@mcp.tool()
def run_digest(group: str, hours: int = 24) -> str:
    """Fetch and summarize Telegram channel messages for a group.

    Returns the digest text content on success.

    Args:
        group: Channel group name from channels.yaml (use list_digest_groups to see options)
        hours: How many hours back to look (default 24)
    """
    start = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d")
    before = set(REPO_DIR.glob("digest_*.txt"))
    result = subprocess.run(
        [str(VENV_PYTHON), "-m", "src.main",
         "--group", group, "--start-date", start, "--no-console"],
        cwd=REPO_DIR,
        capture_output=True,
        text=True,
        timeout=900,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Digest failed:\n{result.stderr[:1000]}")

    # Return the newly created digest file content
    after = set(REPO_DIR.glob("digest_*.txt"))
    new_files = sorted(after - before)
    if new_files:
        return new_files[-1].read_text()

    # Fallback: most recent digest file
    all_files = sorted(REPO_DIR.glob("digest_*.txt"))
    if all_files:
        return all_files[-1].read_text()

    return result.stdout or "No messages found for this period."


if __name__ == "__main__":
    mcp.run()
