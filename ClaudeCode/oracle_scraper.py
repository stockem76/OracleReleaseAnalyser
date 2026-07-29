"""
Scraper + local cache for Oracle's Cloud Applications Readiness content.

Entry point / human-facing UI (as provided):
    https://www.oracle.com/webfolder/technetwork/tutorials/tutorial/readiness/app/index.html
This "Readiness Reports Center" is a client-side JS app (no public JSON/RSS
feed) that lets a person filter by Pillar (ERP/SCM/HCM/Service/...), Product,
Module, and Update, then view or download the matching "What's New"
publications. There's no documented API behind it to call directly, so this
scraper reproduces the same filterable dataset by reading the server-rendered
pages the app itself links out to and is built from, on Oracle Help Center:

    erp-all.html / erp.html         -> Enterprise Resource Planning
    scm-all.html / scm.html         -> Supply Chain & Manufacturing
    hcm-all.html / hcm.html         -> Human Capital Management
    service-all.html / service.html -> Service (CX)
    news.html                       -> Cross-product readiness news

The "-all" variant (all releases) is preferred when it exists since it's a
superset of the "latest update" page and gives filtering by Update (release)
real breadth to work with; the scraper falls back to the plain page if
"-all" 404s.

Two things are cached to disk:

1. `cache.json` — entry metadata (title, module, release, links, first/last
   seen). Cheap, refreshed on the configured schedule.
2. `content_cache.json` — the full downloaded text of each entry's linked
   document (HTML page converted to markdown, or extracted PDF text),
   keyed by URL so multiple entries that point at the same document only
   store it once. This is what lets a report or tool call return/"stream"
   full note content instead of just a link, and is deliberately kept as
   plain JSON on disk so any external ingestion job can read it directly.

If Oracle changes the page template, `_parse_entries` is the one place that
needs updating.
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import httpx
from markdownify import markdownify as html_to_md

try:
    from pypdf import PdfReader
    _HAVE_PYPDF = True
except ImportError:
    _HAVE_PYPDF = False

logger = logging.getLogger("oracle_readiness_mcp.scraper")

READINESS_APP_URL = (
    "https://www.oracle.com/webfolder/technetwork/tutorials/tutorial/readiness/app/index.html"
)
BASE = "https://docs.oracle.com/en/cloud/saas/readiness"

# (all-releases page, latest-only fallback page)
_PRODUCT_PAGES: dict[str, tuple[str, str]] = {
    "erp": (f"{BASE}/erp-all.html", f"{BASE}/erp.html"),
    "scm": (f"{BASE}/scm-all.html", f"{BASE}/scm.html"),
    "hcm": (f"{BASE}/hcm-all.html", f"{BASE}/hcm.html"),
    "service": (f"{BASE}/service-all.html", f"{BASE}/service.html"),
    "news": (f"{BASE}/news.html", f"{BASE}/news.html"),
}
PRODUCTS: dict[str, str] = {p: pages[0] for p, pages in _PRODUCT_PAGES.items()}

PRODUCT_LABELS: dict[str, str] = {
    "erp": "Enterprise Resource Planning",
    "scm": "Supply Chain & Manufacturing",
    "hcm": "Human Capital Management",
    "service": "Service (CX)",
    "news": "Cross-product Readiness News",
}

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 oracle-readiness-mcp/1.0"
)

MAX_CONTENT_CHARS = 300_000  # per-document cap so one giant PDF can't blow up the cache file

# Pass 1: reliably locate every (title, links) pair — this part of the
# template is always present. A description paragraph, when present, is
# *not* guaranteed: Oracle's template sometimes omits it for consecutive
# releases of the same module, so it can't be baked into one combined regex
# without risking swallowing the next entry's title as this entry's
# "description". Pass 2 (below, in _parse_entries) fills in description text
# as whatever's left between the end of one match and the start of the next.
_TITLE_LINKS_RE = re.compile(
    r"(?P<title>[^\n]{4,200}?)\n\s*\n"
    r"(?P<links>(?:\[(?:HTML|PDF)\]\(https?://[^\)]+\)\s*)+)",
    re.MULTILINE,
)

_LINK_RE = re.compile(r"\[(HTML|PDF)\]\((https?://[^\)]+)\)")
_RELEASE_RE = re.compile(r"\b(\d{2}[A-D])\b")
_MODULE_RE = re.compile(r"^(?P<module>.+?)\s+What'?s New\b", re.IGNORECASE)


@dataclass
class ReadinessEntry:
    product: str
    title: str
    module: str
    release: Optional[str]
    description: str
    html_url: Optional[str]
    pdf_url: Optional[str]
    source_page: str
    first_seen: float
    last_seen: float


def _extract_module(title: str) -> str:
    m = _MODULE_RE.match(title)
    return m.group("module").strip() if m else title.strip()


def _parse_entries(markdown_text: str, product: str, source_page: str, now: float) -> list[ReadinessEntry]:
    entries: list[ReadinessEntry] = []
    seen_titles: set[str] = set()

    matches = list(_TITLE_LINKS_RE.finditer(markdown_text))
    for idx, m in enumerate(matches):
        title = m.group("title").strip(" *#-\t")
        if not title or title.lower() in seen_titles:
            continue
        if len(title) < 4 or title.startswith("["):
            continue

        links = dict(_LINK_RE.findall(m.group("links")))
        html_url = links.get("HTML")
        pdf_url = links.get("PDF")
        if not html_url and not pdf_url:
            continue

        # Description is whatever text sits between this match and the next
        # one (empty if the template omitted it for this entry).
        end = m.end()
        start_next = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown_text)
        desc = markdown_text[end:start_next].strip()
        # Keep it to a single paragraph; drop anything after a blank line
        # (stray nav text, etc.) so a missed-title edge case can't leak in.
        desc = desc.split("\n\n")[0].strip() if desc else ""

        release_match = _RELEASE_RE.search(title) or (html_url and _RELEASE_RE.search(html_url))
        release = release_match.group(1) if release_match else None

        seen_titles.add(title.lower())
        entries.append(
            ReadinessEntry(
                product=product,
                title=title,
                module=_extract_module(title),
                release=release,
                description=desc,
                html_url=html_url,
                pdf_url=pdf_url,
                source_page=source_page,
                first_seen=now,
                last_seen=now,
            )
        )
    return entries


async def _get(client: httpx.AsyncClient, url: str) -> httpx.Response:
    resp = await client.get(url, headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=30.0)
    resp.raise_for_status()
    return resp


async def fetch_product_page(client: httpx.AsyncClient, product: str) -> tuple[list[ReadinessEntry], str]:
    """Fetch and parse a single product's readiness page (all-releases page,
    falling back to the latest-only page if that 404s). Returns
    (entries, url_actually_used). Raises on total failure."""
    all_url, latest_url = _PRODUCT_PAGES[product]
    try:
        resp = await _get(client, all_url)
        used_url = all_url
    except httpx.HTTPStatusError:
        resp = await _get(client, latest_url)
        used_url = latest_url

    md = html_to_md(resp.text, heading_style="ATX")
    now = time.time()
    return _parse_entries(md, product, used_url, now), used_url


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    if not _HAVE_PYPDF:
        return "[PDF text extraction unavailable: install the 'pypdf' package to enable it.]"
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        parts = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(parts).strip()
    except Exception as e:
        logger.warning("PDF text extraction failed: %s", e)
        return f"[PDF text extraction failed: {e}]"


async def fetch_document_content(client: httpx.AsyncClient, url: str) -> dict:
    """Download a single readiness document (HTML or PDF) and return its
    text content plus metadata. Does not touch the cache itself."""
    resp = await _get(client, url)
    content_type = resp.headers.get("content-type", "")

    if "pdf" in content_type or url.lower().endswith(".pdf"):
        text = _extract_pdf_text(resp.content)
        doc_type = "pdf"
    else:
        text = html_to_md(resp.text, heading_style="ATX").strip()
        doc_type = "html"

    truncated = len(text) > MAX_CONTENT_CHARS
    if truncated:
        text = text[:MAX_CONTENT_CHARS]

    return {
        "url": url,
        "doc_type": doc_type,
        "content": text,
        "content_chars": len(text),
        "truncated": truncated,
        "fetched_at": time.time(),
    }


class ReadinessCache:
    """
    Thread/async-safe on-disk cache of readiness entry metadata, refreshed
    periodically.

    Layout on disk (JSON):
        {
          "products": {
            "erp": {"entries": [...], "last_refresh": <epoch>, "last_error": null},
            ...
          }
        }

    Plain JSON (not sqlite) so any downstream ingestion job can read it
    directly without needing this codebase.
    """

    def __init__(self, path: Path):
        self.path = path
        self._lock = asyncio.Lock()
        self._data: dict = {"products": {}}
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text())
            except Exception:
                logger.exception("Failed to load existing cache at %s; starting fresh", self.path)
                self._data = {"products": {}}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2))
        tmp.replace(self.path)

    async def refresh_product(self, client: httpx.AsyncClient, product: str) -> dict:
        """Refresh a single product. Returns a summary dict (also merges into cache)."""
        async with self._lock:
            existing = self._data["products"].get(product, {"entries": []})
            existing_by_key = {e["title"]: e for e in existing.get("entries", [])}

        try:
            fresh_entries, used_url = await fetch_product_page(client, product)
        except Exception as e:
            logger.warning("Refresh failed for %s: %s", product, e)
            async with self._lock:
                self._data["products"].setdefault(product, {"entries": []})
                self._data["products"][product]["last_error"] = str(e)
                self._data["products"][product]["last_attempt"] = time.time()
                self._save()
            return {"product": product, "ok": False, "error": str(e)}

        new_count = 0
        updated_count = 0
        merged: list[dict] = []
        for entry in fresh_entries:
            d = asdict(entry)
            prior = existing_by_key.get(entry.title)
            if prior is None:
                new_count += 1
            else:
                d["first_seen"] = prior.get("first_seen", d["first_seen"])
                if (
                    prior.get("html_url") != d["html_url"]
                    or prior.get("pdf_url") != d["pdf_url"]
                    or prior.get("description") != d["description"]
                ):
                    updated_count += 1
            merged.append(d)

        async with self._lock:
            self._data["products"][product] = {
                "entries": merged,
                "last_refresh": time.time(),
                "last_error": None,
                "source_page": used_url,
            }
            self._save()

        return {
            "product": product,
            "ok": True,
            "source_page": used_url,
            "total_entries": len(merged),
            "new_entries": new_count,
            "updated_entries": updated_count,
        }

    async def refresh_all(self, products: Optional[list[str]] = None) -> list[dict]:
        products = products or list(PRODUCTS.keys())
        async with httpx.AsyncClient() as client:
            results = []
            for p in products:
                results.append(await self.refresh_product(client, p))
                await asyncio.sleep(1.0)  # be polite to Oracle's servers
            return results

    def get_entries(self, product: str) -> dict:
        return self._data["products"].get(product, {"entries": [], "last_refresh": None, "last_error": None})

    def get_all(self) -> dict:
        return self._data

    def status(self) -> dict:
        out = {}
        for p in PRODUCTS:
            rec = self._data["products"].get(p)
            out[p] = {
                "label": PRODUCT_LABELS[p],
                "last_refresh": rec.get("last_refresh") if rec else None,
                "last_error": rec.get("last_error") if rec else None,
                "entry_count": len(rec.get("entries", [])) if rec else 0,
            }
        return out

    def filter_entries(
        self,
        pillars: Optional[list[str]] = None,
        modules: Optional[list[str]] = None,
        releases: Optional[list[str]] = None,
        query: Optional[str] = None,
    ) -> list[dict]:
        """Filter cached entries the same way the Readiness Reports Center's
        Pillar / Module / Update selectors do (OR within a filter, AND across
        filters)."""
        pillars = pillars or list(PRODUCTS.keys())
        modules_l = [m.lower() for m in modules] if modules else None
        releases_u = [r.upper() for r in releases] if releases else None
        query_l = query.lower() if query else None

        matched: list[dict] = []
        for p in pillars:
            for e in self.get_entries(p).get("entries", []):
                if modules_l and not any(
                    m in e.get("module", "").lower() or m in e.get("title", "").lower() for m in modules_l
                ):
                    continue
                if releases_u and (e.get("release") or "").upper() not in releases_u:
                    continue
                if query_l and query_l not in e.get("title", "").lower() and query_l not in e.get("description", "").lower():
                    continue
                matched.append(e)
        matched.sort(key=lambda e: (e.get("product", ""), e.get("release") or "", e.get("title", "")))
        return matched


class ContentCache:
    """
    On-disk cache of full downloaded document text, keyed by URL, so the same
    document referenced by multiple entries is only stored once and only
    fetched once. Deliberately separate from ReadinessCache since it can grow
    much larger and is fetched more selectively (on demand / opt-in during
    refresh) rather than on every scheduled metadata refresh.
    """

    def __init__(self, path: Path):
        self.path = path
        self._lock = asyncio.Lock()
        self._data: dict = {"documents": {}}
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text())
            except Exception:
                logger.exception("Failed to load existing content cache at %s; starting fresh", self.path)
                self._data = {"documents": {}}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2))
        tmp.replace(self.path)

    def get(self, url: str) -> Optional[dict]:
        return self._data["documents"].get(url)

    async def fetch(self, client: httpx.AsyncClient, url: str, force: bool = False) -> dict:
        if not force:
            cached = self.get(url)
            if cached is not None:
                return cached
        doc = await fetch_document_content(client, url)
        async with self._lock:
            self._data["documents"][url] = doc
            self._save()
        return doc

    async def fetch_many(self, urls: list[str], force: bool = False, max_concurrency: int = 4) -> list[dict]:
        """Bounded-concurrency batch fetch, e.g. for populating content ahead
        of a report. Errors for individual URLs are captured, not raised."""
        sem = asyncio.Semaphore(max_concurrency)

        async with httpx.AsyncClient() as client:
            async def _one(u: str):
                async with sem:
                    try:
                        return await self.fetch(client, u, force=force)
                    except Exception as e:
                        logger.warning("Content fetch failed for %s: %s", u, e)
                        return {"url": u, "error": str(e)}

            results = await asyncio.gather(*(_one(u) for u in urls))
        return list(results)

    def status(self) -> dict:
        docs = self._data["documents"]
        return {
            "documents_cached": len(docs),
            "total_chars_cached": sum(d.get("content_chars", 0) for d in docs.values()),
        }
