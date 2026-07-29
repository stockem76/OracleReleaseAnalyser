"""
Standalone refresh script — updates the same cache.json the MCP server reads,
without needing the MCP server process itself to be running.

Use this if you run the MCP server over stdio (e.g. wired into Claude
Desktop/Code), where the process only exists while a client is connected, so
the server's own background refresh loop can't run continuously. Point a
cron job or systemd timer at this script instead, on the same
READINESS_DATA_DIR the MCP server uses, and both stay in sync.

This refreshes entry *metadata* only (titles, links, releases) — it's cheap
and safe to run every few hours. Full document content (the actual note
text) is downloaded separately, on demand, via the generate_report or
get_document_content tools, since pre-downloading every document on every
refresh would mean re-fetching hundreds of pages from Oracle on a schedule
for content that rarely changes once published.

Usage:
    python refresh_cli.py                 # refresh all products
    python refresh_cli.py erp hcm         # refresh only erp and hcm
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from oracle_scraper import PRODUCTS, ReadinessCache

DATA_DIR = Path(os.environ.get("READINESS_DATA_DIR", "./data")).resolve()
CACHE_PATH = DATA_DIR / "cache.json"


async def main() -> None:
    products = sys.argv[1:] or None
    if products:
        bad = [p for p in products if p not in PRODUCTS]
        if bad:
            print(f"Unknown product(s): {bad}. Valid: {list(PRODUCTS.keys())}", file=sys.stderr)
            sys.exit(1)

    cache = ReadinessCache(CACHE_PATH)
    results = await cache.refresh_all(products)
    print(json.dumps(results, indent=2))

    if any(not r["ok"] for r in results):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
