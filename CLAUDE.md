# yt_scraper

Scrape YouTube transcripts and summarize them.

## Rules
- Every scraped video produces **one** file in `output/`, named `<YYYY-MM-DD>_<video title>.md`.
- File layout: header + metadata, `## Summary` (detailed, in the video's language), `## Full transcript`. Heading strings are constants at the top of `scrape.py` (older files in `output/` still use the German headings).
- No loose transcript or summary files in the project root.

## How
```bash
.venv/bin/python scrape.py <video_id_or_url>   # writes skeleton with _(TODO)_ summary placeholder
```
Then replace `_(TODO)_` with the summary. Video IDs beginning with `-` must be passed as `-- -abc123`.

## MCP server
`mcp_server.py` exposes the scraper over stdio (official `mcp` SDK v2, `MCPServer`). Tools: `get_transcript`, `scrape_video` (refuses to overwrite unless `overwrite=true`), `save_summary` (writes only inside `output/`), `list_outputs`.
- Registered in Claude Code at user scope as `yt-scraper`; check with `/mcp` or `claude mcp list`.
- Re-register after moving the project: `claude mcp add yt-scraper --scope user -- <abs>/.venv/bin/python <abs>/mcp_server.py`
- Claude Desktop: add the same command/args under `mcpServers` in `claude_desktop_config.json`.
- Never print to stdout in the server; stdout is the transport. Raise `ToolError` for expected failures.
- Workflow via MCP: `scrape_video` → write summary → `save_summary(path, markdown)`.
