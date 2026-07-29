# oracle_readiness_mcp

MCP server for Oracle Cloud Applications **readiness / "what's new"** notes
(ERP, SCM, HCM, Service), built around the same filtering model as Oracle's
own **Readiness Reports Center**:

> https://www.oracle.com/webfolder/technetwork/tutorials/tutorial/readiness/app/index.html

You pick **Pillar** → **Module** → **Update**, generate a report, and get the
full content of matching notes back — not just links. Everything is cached
locally and refreshed automatically every 6 hours.

## About that URL

The Readiness Reports Center is a client-side JS app with no public/documented
API behind its search-and-download UI, so this server can't call it as a
backend directly. It's still the canonical entry point (`list_products` and
every generated report link back to it), and this server reproduces the same
data and the same three filters (Pillar/Module/Update) by reading the
server-rendered pages the app itself is built from and links out to, on
Oracle Help Center:

| Pillar | Source (all releases) |
|---|---|
| ERP | https://docs.oracle.com/en/cloud/saas/readiness/erp-all.html |
| SCM | https://docs.oracle.com/en/cloud/saas/readiness/scm-all.html |
| HCM | https://docs.oracle.com/en/cloud/saas/readiness/hcm-all.html |
| Service | https://docs.oracle.com/en/cloud/saas/readiness/service-all.html |
| News (cross-product) | https://docs.oracle.com/en/cloud/saas/readiness/news.html |

If a `-all` page ever 404s, the scraper falls back to the plain (latest
update only) page automatically. If Oracle changes the page template, all
the parsing logic lives in one place: `_parse_entries` in `oracle_scraper.py`.

## What it does

1. **Filters like the Reports Center** — Pillar, Module (substring, e.g.
   "Procurement"), Update/release (e.g. "26C"), plus a free-text query.
2. **Generates a report** — `generate_report` matches entries against your
   filters, and can also download the full content of every matching
   document (HTML converted to markdown, PDF text-extracted) instead of
   just returning a link.
3. **Streams content to the consumer** — matched documents' full text comes
   back in the tool response (capped to the first 15 per call so one report
   can't blow up an LLM's context) *and* is always written in full,
   unlimited, to a report file on disk plus a shared content cache, so an
   ingestion pipeline can read everything directly from disk regardless of
   what got inlined into any one tool response.
4. **Holds it all locally, refreshed every 6 hours** — entry metadata
   refreshes automatically on a schedule; full document content is
   downloaded on demand (via `generate_report(include_content=true)` or
   `get_document_content`) and cached indefinitely once fetched, since
   published notes rarely change after the fact.

## Tools

| Tool | Purpose |
|---|---|
| `list_products` | Tracked pillars, their source URLs, and the Readiness Reports Center URL |
| `get_cache_status` | Last refresh time/errors per pillar + how much content is cached |
| `get_release_notes` | All cached notes for one pillar, optional release filter |
| `search_release_notes` | Substring search across titles/descriptions |
| `generate_report` | **Main tool.** Filter by pillars/modules/releases/query; optionally download full content; always saves a report file |
| `get_document_content` | Download (or serve cached) full text of one specific note by URL |
| `refresh_readiness_data` | Force an immediate metadata refresh instead of waiting for the schedule |

**Resource:** `readiness://cache/{product}` — raw JSON of a pillar's cached entries.

## On-disk layout (`READINESS_DATA_DIR`, default `./data`)

```
data/
  cache.json           # entry metadata for all pillars (refreshed every 6h)
  content_cache.json   # full downloaded document text, keyed by URL
  reports/
    report_20260720T190000Z.json   # every generate_report call writes both
    report_20260720T190000Z.md
```

`cache.json` and `content_cache.json` are plain JSON specifically so an
external ingestion job can tail them directly without going through MCP at
all.

## Install

```bash
pip install -r requirements.txt
```

## Run

### Option A — stdio (local, e.g. Claude Desktop / Claude Code)

```bash
python server.py
```

```json
{
  "mcpServers": {
    "oracle-readiness": {
      "command": "python",
      "args": ["/absolute/path/to/oracle_readiness_mcp/server.py"],
      "env": { "READINESS_DATA_DIR": "/absolute/path/to/oracle_readiness_mcp/data" }
    }
  }
}
```

**Caveat:** over stdio, the process (and its background refresh loop) only
runs while a client is connected. For continuous refreshing regardless of
connections, either run in HTTP mode (below) or point a cron job / systemd
timer at `refresh_cli.py` against the same `READINESS_DATA_DIR`.

### Option B — Streamable HTTP (recommended for always-on / deployed use)

```bash
python server.py --http
```

Listens on `0.0.0.0:8000` (`READINESS_HTTP_HOST` / `READINESS_HTTP_PORT` to
override) at `/mcp`. The background refresh loop runs for as long as the
process is up, independent of client connections.

### Option C — Podman

```bash
podman build -t oracle-readiness-mcp .
podman run -d --name oracle-readiness \
  -p 8000:8000 \
  -v $(pwd)/data:/data:Z \
  -e READINESS_REFRESH_HOURS=6 \
  oracle-readiness-mcp
```

### Standalone metadata refresh (cron / systemd timer)

```bash
python refresh_cli.py            # refresh all pillars
python refresh_cli.py erp hcm     # refresh only ERP and HCM
```

```ini
# /etc/systemd/system/oracle-readiness-refresh.service
[Unit]
Description=Refresh Oracle readiness cache

[Service]
Type=oneshot
Environment=READINESS_DATA_DIR=/opt/oracle-readiness-mcp/data
WorkingDirectory=/opt/oracle-readiness-mcp
ExecStart=/usr/bin/python3 refresh_cli.py
```

```ini
# /etc/systemd/system/oracle-readiness-refresh.timer
[Unit]
Description=Run Oracle readiness refresh every 6 hours

[Timer]
OnBootSec=5min
OnUnitActiveSec=6h

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable --now oracle-readiness-refresh.timer
```

## Example: a filtered report with full content

Ask your MCP client something like:

> Generate a report of ERP and SCM readiness notes for release 26C, and
> include the full content of each note.

which maps to:

```json
{
  "filters": {"pillars": ["erp", "scm"], "releases": ["26C"]},
  "include_content": true
}
```

The response inlines up to 15 documents' full text; `report_json_path` /
`report_markdown_path` point to the complete files on disk (every matched
entry, every document, no cap) for ingestion.

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `READINESS_DATA_DIR` | `./data` | Where cache.json / content_cache.json / reports/ live |
| `READINESS_REFRESH_HOURS` | `6` | Hours between automatic metadata refreshes |
| `READINESS_AUTOSTART_REFRESH` | `1` | Set to `0` to disable the built-in background loop |
| `READINESS_HTTP_HOST` | `0.0.0.0` | Bind host in `--http` mode |
| `READINESS_HTTP_PORT` | `8000` | Bind port in `--http` mode |

## Notes / limitations

- No stable IDs are published for entries, so new/updated detection is by
  exact title match — a retitled publication shows up as new rather than
  updated.
- Release codes are extracted heuristically from the title or URL; a few
  cross-references (e.g. Fusion Data Intelligence "what's new" that appears
  on multiple pillar pages) won't have one and show `release: null`.
- Content downloads are capped at 300,000 characters per document
  (`MAX_CONTENT_CHARS` in `oracle_scraper.py`) so one oversized PDF can't
  blow up the cache file.
- Be a reasonable citizen of Oracle's site: metadata refresh is capped to
  every 6 hours by default with a 1-second pause between pillar requests,
  and full document downloads only happen on demand, deduplicated by URL, so
  repeated reports over the same notes don't re-fetch anything.
