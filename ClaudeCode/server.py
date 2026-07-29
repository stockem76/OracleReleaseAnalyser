"""
oracle_readiness_mcp: MCP server for Oracle Cloud Applications Readiness notes
(HCM, ERP, SCM, Service).

Mirrors the filtering model of Oracle's own "Readiness Reports Center"
(https://www.oracle.com/webfolder/technetwork/tutorials/tutorial/readiness/app/index.html)
— Pillar, Module, Update — and adds report generation plus full-document
content download (so a consumer gets the actual note text, not just a link),
backed by a local cache that refreshes automatically every
READINESS_REFRESH_HOURS hours (default 6).

Run modes:
  stdio (default)   -> python server.py
  streamable HTTP    -> python server.py --http   (recommended: keeps the
                        background refresh loop running independent of any
                        connected client — see README)

Environment variables:
  READINESS_DATA_DIR            Directory for cache.json / content_cache.json / reports/ (default: ./data)
  READINESS_REFRESH_HOURS        Hours between automatic refreshes (default: 6)
  READINESS_AUTOSTART_REFRESH    "0" to disable the background refresh loop (default: "1")
  READINESS_HTTP_HOST / _PORT    Bind address for --http mode
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, ConfigDict, Field

from oracle_scraper import (
    PRODUCT_LABELS,
    PRODUCTS,
    READINESS_APP_URL,
    ContentCache,
    ReadinessCache,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("oracle_readiness_mcp")

DATA_DIR = Path(os.environ.get("READINESS_DATA_DIR", "./data")).resolve()
CACHE_PATH = DATA_DIR / "cache.json"
CONTENT_CACHE_PATH = DATA_DIR / "content_cache.json"
REPORTS_DIR = DATA_DIR / "reports"
REFRESH_HOURS = float(os.environ.get("READINESS_REFRESH_HOURS", "6"))
AUTOSTART_REFRESH = os.environ.get("READINESS_AUTOSTART_REFRESH", "1") != "0"

PRODUCT_NAMES = tuple(PRODUCTS.keys())  # ('erp', 'scm', 'hcm', 'service', 'news')
DEFAULT_PILLARS = ("erp", "scm", "hcm", "service")  # the four the user asked to track day-to-day

# Cap on how many full documents a single tool call will inline into its
# response (context safety) — the full, unlimited set is still written to
# the report file on disk either way.
MAX_INLINE_CONTENT_DOCS = 15


class AppState:
    def __init__(self) -> None:
        self.cache = ReadinessCache(CACHE_PATH)
        self.content_cache = ContentCache(CONTENT_CACHE_PATH)
        self._refresh_task: Optional[asyncio.Task] = None
        self._refresh_lock = asyncio.Lock()

    async def start_background_refresh(self) -> None:
        if self._refresh_task is not None:
            return

        async def _loop():
            while True:
                try:
                    async with self._refresh_lock:
                        results = await self.cache.refresh_all()
                    logger.info("Background refresh complete: %s", results)
                except Exception:
                    logger.exception("Background refresh loop encountered an error")
                await asyncio.sleep(REFRESH_HOURS * 3600)

        self._refresh_task = asyncio.create_task(_loop())

    async def refresh_now(self, products: Optional[list[str]]) -> list[dict]:
        async with self._refresh_lock:
            return await self.cache.refresh_all(products)


state = AppState()


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    if AUTOSTART_REFRESH:
        await state.start_background_refresh()
    else:
        logger.info("Background refresh disabled via READINESS_AUTOSTART_REFRESH=0")
    yield {}


mcp = FastMCP(
    "oracle_readiness_mcp",
    lifespan=app_lifespan,
    host=os.environ.get("READINESS_HTTP_HOST", "0.0.0.0"),
    port=int(os.environ.get("READINESS_HTTP_PORT", "8000")),
)


def _validate_products(products: list[str]) -> None:
    bad = [p for p in products if p not in PRODUCT_NAMES]
    if bad:
        raise ValueError(f"Unknown product(s) {bad}. Valid values are: {', '.join(PRODUCT_NAMES)}")


class ReportFilters(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    pillars: list[str] = Field(
        default_factory=lambda: list(DEFAULT_PILLARS),
        description=f"Pillars to include, matching the Readiness Reports Center's Pillar selector. Any of: {', '.join(PRODUCT_NAMES)}. Defaults to erp, scm, hcm, service.",
    )
    modules: Optional[list[str]] = Field(
        default=None,
        description="Optional module/product name substrings (OR'd), e.g. ['Procurement', 'Benefits'], matching the Module selector.",
    )
    releases: Optional[list[str]] = Field(
        default=None,
        description="Optional release/update codes (OR'd), e.g. ['26C', '26B'], matching the Updates selector.",
    )
    query: Optional[str] = Field(
        default=None, description="Optional free-text substring to additionally require in the title or description."
    )


class GenerateReportInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    filters: ReportFilters = Field(default_factory=ReportFilters, description="Pillar/Module/Update/query filters, mirroring the Readiness Reports Center.")
    include_content: bool = Field(
        default=False,
        description="If true, download (or reuse cached) full text of each matched entry's linked document and include it. The full set is always written to the report file on disk; only the first "
        f"{MAX_INLINE_CONTENT_DOCS} are inlined into the tool response to avoid flooding context — use the file path or get_document_content for the rest.",
    )
    force_redownload: bool = Field(default=False, description="If true and include_content is set, re-download documents even if already cached.")
    save_report: bool = Field(default=True, description="Write the full report (metadata + content if requested) to a timestamped file under the local reports directory.")


class GetDocumentContentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    url: str = Field(..., description="The html_url or pdf_url of a readiness entry, as returned by get_release_notes/search_release_notes/generate_report.")
    force_redownload: bool = Field(default=False, description="Re-download even if already cached.")


class ListNotesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    product: str = Field(..., description=f"Product line to fetch notes for. One of: {', '.join(PRODUCT_NAMES)}.")
    release: Optional[str] = Field(default=None, description="Optional release code filter, e.g. '26C'. Case-insensitive.")
    limit: int = Field(default=50, ge=1, le=500, description="Maximum number of entries to return.")


class SearchNotesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(..., min_length=2, max_length=200, description="Case-insensitive substring to search for in titles and descriptions.")
    product: Optional[str] = Field(default=None, description=f"Restrict search to one product ({', '.join(PRODUCT_NAMES)}). Omit to search all.")
    limit: int = Field(default=50, ge=1, le=500, description="Maximum number of matching entries to return.")


class RefreshInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    products: Optional[list[str]] = Field(
        default=None,
        description=f"Which product pages to refresh now. Omit to refresh all ({', '.join(PRODUCT_NAMES)}).",
    )


@mcp.tool(
    name="list_products",
    annotations={"title": "List Oracle readiness product lines", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def list_products() -> dict:
    """List the Oracle Cloud readiness pillars this server tracks and where
    their data comes from.

    Returns:
        dict: {"readiness_reports_center_url": str,
               "products": {product_code: {"label": str, "source_url": str}}}
    """
    return {
        "readiness_reports_center_url": READINESS_APP_URL,
        "products": {p: {"label": PRODUCT_LABELS[p], "source_url": PRODUCTS[p]} for p in PRODUCT_NAMES},
    }


@mcp.tool(
    name="get_cache_status",
    annotations={"title": "Get readiness cache status", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def get_cache_status() -> dict:
    """Report when each product's readiness metadata was last refreshed,
    whether the last attempt errored, how many entries are cached, and how
    much full document content is cached locally.

    Returns:
        dict: {"metadata": {product_code: {...}}, "content": {"documents_cached": int, "total_chars_cached": int}}
    """
    return {"metadata": state.cache.status(), "content": state.content_cache.status()}


@mcp.tool(
    name="get_release_notes",
    annotations={"title": "Get cached Oracle readiness notes for a product", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def get_release_notes(params: ListNotesInput) -> dict:
    """Return cached "what's new" / readiness publications for one Oracle
    Cloud pillar (HCM, ERP, SCM, Service, or cross-product News), across all
    releases available. For multi-pillar/module/release filtering, prefer
    generate_report.

    Args:
        params (ListNotesInput): product (required), optional release filter, result limit.

    Returns:
        dict: {"product": str, "last_refresh": epoch|null, "total_matched": int,
               "entries": [{"title": str, "module": str, "release": str|null,
               "description": str, "html_url": str|null, "pdf_url": str|null,
               "first_seen": epoch, "last_seen": epoch}]}
    """
    _validate_products([params.product])
    record = state.cache.get_entries(params.product)
    entries = record.get("entries", [])

    if params.release:
        target = params.release.upper()
        entries = [e for e in entries if (e.get("release") or "").upper() == target]

    entries = sorted(entries, key=lambda e: e.get("last_seen", 0), reverse=True)
    total_matched = len(entries)
    entries = entries[: params.limit]

    return {
        "product": params.product,
        "last_refresh": record.get("last_refresh"),
        "last_error": record.get("last_error"),
        "total_matched": total_matched,
        "entries": entries,
    }


@mcp.tool(
    name="search_release_notes",
    annotations={"title": "Search cached Oracle readiness notes", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def search_release_notes(params: SearchNotesInput) -> dict:
    """Case-insensitive substring search across cached readiness note titles
    and descriptions, optionally restricted to one pillar.

    Args:
        params (SearchNotesInput): query string, optional product filter, result limit.

    Returns:
        dict: {"query": str, "total_matched": int,
               "entries": [{"product": str, "title": str, "module": str,
               "release": str|null, "description": str, "html_url": str|null, "pdf_url": str|null}]}
    """
    products = [params.product] if params.product else list(PRODUCT_NAMES)
    _validate_products(products)

    q = params.query.lower()
    matches: list[dict] = []
    for p in products:
        for e in state.cache.get_entries(p).get("entries", []):
            if q in e.get("title", "").lower() or q in e.get("description", "").lower():
                matches.append(e)

    matches.sort(key=lambda e: e.get("last_seen", 0), reverse=True)
    return {"query": params.query, "total_matched": len(matches), "entries": matches[: params.limit]}


@mcp.tool(
    name="generate_report",
    annotations={"title": "Generate a filtered Oracle readiness report", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True},
)
async def generate_report(params: GenerateReportInput, ctx: Context) -> dict:
    """Generate a report of Oracle readiness notes filtered by Pillar,
    Module, and Update — the same three facets as the Readiness Reports
    Center — optionally with the full text of each matched document
    downloaded and included (not just a link).

    The complete, unlimited result (and full content, if requested) is
    always written to a JSON + Markdown file pair under the local reports
    directory for downstream ingestion; the tool response itself inlines at
    most the first entries/documents to stay context-safe.

    Args:
        params (GenerateReportInput): filters (pillars/modules/releases/query),
            include_content flag, force_redownload flag, save_report flag.

    Returns:
        dict: {
          "filters": {...}, "total_matched": int,
          "entries": [ {..., "content": str (only if include_content and inlined)} ],
          "content_inlined": int, "content_truncated_for_response": bool,
          "report_json_path": str|null, "report_markdown_path": str|null
        }
    """
    _validate_products(params.filters.pillars)
    entries = state.cache.filter_entries(
        pillars=params.filters.pillars,
        modules=params.filters.modules,
        releases=params.filters.releases,
        query=params.filters.query,
    )

    content_by_url: dict[str, dict] = {}
    if params.include_content and entries:
        urls = sorted({e["html_url"] or e["pdf_url"] for e in entries if (e.get("html_url") or e.get("pdf_url"))})
        await ctx.log_info(f"Downloading content for {len(urls)} document(s)...")
        fetched = await state.content_cache.fetch_many(urls, force=params.force_redownload)
        for doc in fetched:
            if "url" in doc:
                content_by_url[doc["url"]] = doc

    full_entries = []
    for e in entries:
        e2 = dict(e)
        if params.include_content:
            u = e.get("html_url") or e.get("pdf_url")
            doc = content_by_url.get(u) if u else None
            if doc and "content" in doc:
                e2["content"] = doc["content"]
                e2["content_truncated"] = doc.get("truncated", False)
            elif doc and "error" in doc:
                e2["content_error"] = doc["error"]
        full_entries.append(e2)

    report = {
        "generated_at": time.time(),
        "readiness_reports_center_url": READINESS_APP_URL,
        "filters": params.filters.model_dump(),
        "total_matched": len(full_entries),
        "entries": full_entries,
    }

    report_json_path = None
    report_md_path = None
    if params.save_report:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        json_path = REPORTS_DIR / f"report_{stamp}.json"
        md_path = REPORTS_DIR / f"report_{stamp}.md"
        json_path.write_text(json.dumps(report, indent=2))
        md_path.write_text(_render_markdown_report(report))
        report_json_path = str(json_path)
        report_md_path = str(md_path)

    # Trim what goes back in the tool response so a large report can't
    # blow up the conversation context; the files on disk have everything.
    response_entries = []
    inlined_content = 0
    for e in full_entries:
        e_resp = dict(e)
        if "content" in e_resp:
            if inlined_content >= MAX_INLINE_CONTENT_DOCS:
                del e_resp["content"]
            else:
                inlined_content += 1
        response_entries.append(e_resp)

    return {
        "filters": params.filters.model_dump(),
        "total_matched": len(full_entries),
        "entries": response_entries,
        "content_inlined": inlined_content,
        "content_truncated_for_response": params.include_content and inlined_content < len(full_entries),
        "report_json_path": report_json_path,
        "report_markdown_path": report_md_path,
    }


def _render_markdown_report(report: dict) -> str:
    lines = [
        "# Oracle Cloud Readiness Report",
        "",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(report['generated_at']))}",
        f"Source: [Readiness Reports Center]({report['readiness_reports_center_url']})",
        f"Filters: `{json.dumps(report['filters'])}`",
        f"Total matched: {report['total_matched']}",
        "",
    ]
    for e in report["entries"]:
        lines.append(f"## {e['title']}")
        lines.append(f"- Pillar: {e['product']}  |  Module: {e.get('module', '')}  |  Release: {e.get('release') or 'n/a'}")
        if e.get("html_url"):
            lines.append(f"- HTML: {e['html_url']}")
        if e.get("pdf_url"):
            lines.append(f"- PDF: {e['pdf_url']}")
        if e.get("description"):
            lines.append("")
            lines.append(e["description"])
        if e.get("content"):
            lines.append("")
            lines.append("<details><summary>Full content</summary>")
            lines.append("")
            lines.append(e["content"])
            lines.append("")
            lines.append("</details>")
        lines.append("")
    return "\n".join(lines)


@mcp.tool(
    name="get_document_content",
    annotations={"title": "Download and return full text of a readiness document", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def get_document_content(params: GetDocumentContentInput) -> dict:
    """Download (or serve from local cache) the full text of a single
    readiness document — the actual note content, not just a link — for a
    URL returned by get_release_notes / search_release_notes / generate_report.
    HTML pages are converted to markdown; PDFs have their text extracted.

    Args:
        params (GetDocumentContentInput): url, force_redownload flag.

    Returns:
        dict: {"url": str, "doc_type": "html"|"pdf", "content": str,
               "content_chars": int, "truncated": bool, "fetched_at": epoch}
    """
    import httpx

    async with httpx.AsyncClient() as client:
        return await state.content_cache.fetch(client, params.url, force=params.force_redownload)


@mcp.tool(
    name="refresh_readiness_data",
    annotations={"title": "Refresh Oracle readiness data now", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def refresh_readiness_data(params: RefreshInput, ctx: Context) -> dict:
    """Fetch the latest readiness metadata from docs.oracle.com right now
    for the requested pillar(s), instead of waiting for the scheduled
    background refresh (every READINESS_REFRESH_HOURS hours, default 6).
    This refreshes entry metadata only; use generate_report or
    get_document_content to (re)download full document text.

    Args:
        params (RefreshInput): products (optional list; omit for all).

    Returns:
        dict: {"results": [{"product": str, "ok": bool, "total_entries": int,
               "new_entries": int, "updated_entries": int}]}
    """
    if params.products:
        _validate_products(params.products)
    await ctx.log_info(f"Refreshing Oracle readiness data for: {params.products or 'all products'}")
    results = await state.refresh_now(params.products)
    return {"results": results}


@mcp.resource("readiness://cache/{product}")
async def readiness_cache_resource(product: str) -> str:
    """Expose a product's cached readiness entries as a raw JSON MCP resource."""
    _validate_products([product])
    return json.dumps(state.cache.get_entries(product), indent=2)


def main() -> None:
    if "--http" in sys.argv:
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
