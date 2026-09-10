<h1 align="center">yt_scraper</h1>

<p align="center">
  <b>YouTube scraper with automatic summaries.</b><br>
  One video in, one Markdown file out — full transcript and summary in the same place.
</p>

<p align="center">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="MCP server" src="https://img.shields.io/badge/MCP-stdio%20server-6f42c1">
  <img alt="No API key" src="https://img.shields.io/badge/API%20key-none%20needed-brightgreen">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-lightgrey">
</p>

---

Point it at a video. It fetches the transcript, writes
`output/<date>_<title>.md`, and your LLM fills in the summary — in the same file, in whatever
language and depth you ask for. The summarizing happens in **your** model (via MCP); this repo
contains no model calls, no API keys, no vendor.

## What you get

```markdown
# AI Is Making Coding Cheap. Here's What Matters Now

- **Channel:** Perfology Clips
- **Video:** https://www.youtube.com/watch?v=AVvDFsMUxf0
- **Scraped:** 2026-09-10
- **Transcript:** English (auto-generated)

---

## Summary

Ng rejects the "AI progress is slowing" narrative: measured by how long a human would take
on a task AI can complete, capability doubles roughly every seven months…

---

## Full transcript

What I want to do today is chat to you about career advice in AI…
```

One file per video. Greppable, portable, nothing loose. Heading strings are constants at the
top of `scrape.py` if you want them in another language.

## Install

```bash
git clone https://github.com/ilPicc0ne/yt_scraper.git && cd yt_scraper
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

## Use it from the command line

```bash
.venv/bin/python scrape.py https://www.youtube.com/watch?v=VIDEO_ID
.venv/bin/python scrape.py VIDEO_ID                   # bare ID works too
.venv/bin/python scrape.py VIDEO_ID --languages en de # force a caption preference order
.venv/bin/python scrape.py VIDEO_ID --overwrite       # replace an existing file
.venv/bin/python scrape.py -- -abc123xyz9             # IDs starting with "-" need the --
```

Prints the path it wrote. The summary section holds a `_(TODO)_` placeholder until something
fills it in.

**Captions are picked automatically:** whatever the video actually has, preferring a
human-written track over the auto-generated one. A German talk gives you a German transcript, an
English one gives you English — no language configuration to get wrong. `--languages` overrides
that when you want a specific track, e.g. a translated one.

## Use it from your LLM (the good part)

As an MCP server, Claude runs the whole loop itself — fetch, read, summarize, save — with no
copy-pasting:

> **You:** scrape this and give me a TLDR for our team chat → *`youtube.com/watch?v=…`*
>
> **Claude:** *`scrape_video`* → reads the transcript → writes the summary → *`save_summary`*
> → "Saved to `output/2026-09-10_….md`. Here's the TLDR: …"

**Claude Code:**

```bash
claude mcp add yt-scraper --scope user -- "$PWD/.venv/bin/python" "$PWD/mcp_server.py"
```

Verify with `claude mcp list`. User scope makes it available in every project. Re-run after
moving the folder — the registered paths are absolute.

<details>
<summary><b>Claude Desktop</b></summary>

In `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "yt-scraper": {
      "command": "/absolute/path/to/yt_scraper/.venv/bin/python",
      "args": ["/absolute/path/to/yt_scraper/mcp_server.py"]
    }
  }
}
```
</details>

| Tool | What it does |
| --- | --- |
| `get_transcript` | Title, channel, URL, transcript and which caption track it came from. Read-only. |
| `scrape_video` | Writes the output file. Won't overwrite unless `overwrite=true`. |
| `save_summary` | Fills the placeholder. Refuses to write outside `output/`. |
| `list_outputs` | Every output file, and whether its summary is still pending. |

Those two guards matter: a re-scrape can't destroy a summary you thought about, and a confused
model can't write files across your disk.

## Limits worth knowing

- **Captions, not audio.** Uses
  [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) — videos without
  captions fail, and YouTube rate-limits datacenter IPs, so this is happiest on a home connection.
  The header of each file records which track was used.
- **Auto-captions arrive unpunctuated,** so paragraph splitting is best-effort on those.
- **Titles** come from YouTube's public oEmbed endpoint — still no key required.
- **`output/` is gitignored.** Scraped content stays local. Mind the copyright of anything you
  republish.
- **Hacking on the MCP server?** Never `print()` to stdout — stdout *is* the transport. Use
  stderr, and raise `ToolError` for expected failures.

## License

MIT — see [LICENSE](LICENSE).
