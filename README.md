<h1 align="center">yt_scraper</h1>

<p align="center">
  <b>Turn any YouTube video into one clean Markdown file — transcript + summary, nothing loose.</b>
</p>

<p align="center">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="MCP server" src="https://img.shields.io/badge/MCP-stdio%20server-6f42c1">
  <img alt="No API key" src="https://img.shields.io/badge/API%20key-none%20needed-brightgreen">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-lightgrey">
</p>

---

A 90-minute conference talk holds about six minutes of things you actually needed. Getting at
them usually means scrubbing the timeline, or pasting a transcript into a chat window and
watching the result scroll away forever.

This does it differently: **one video in, one file out.** The transcript and the summary live
in the same Markdown file, named by date and title, sitting in a folder you can grep. Nothing
loose, nothing lost.

```
output/2026-09-10_AI Is Making Coding Cheap. Here's What Matters Now.md
```

```markdown
# AI Is Making Coding Cheap. Here's What Matters Now

- **Kanal:** Perfology Clips
- **Video:** https://www.youtube.com/watch?v=AVvDFsMUxf0
- **Gescraped:** 2026-09-10

## Zusammenfassung
Ng rejects the "AI progress is slowing" narrative: measured by how long a human
would take on a task AI can complete, capability doubles roughly every seven months…

## Volltranskript
What I want to do today is chat to you about career advice in AI…
```

## The good part: it runs inside your LLM chat

`yt_scraper` ships as an **MCP server**, so Claude (Code or Desktop) can drive the whole loop
itself — fetch, read, summarize, save — without you copying a single line of text:

> **You:** scrape this and give me a TLDR for our team chat → *`youtube.com/watch?v=…`*
>
> **Claude:** *`scrape_video`* → reads the transcript → writes the summary → *`save_summary`*
> "Done, saved to `output/2026-09-10_…md`. Here's the TLDR: …"

The summary is written by *your* model, in your voice, at whatever depth you ask for.
There is no model call anywhere in this repo — no keys, no tokens, no vendor.

## Quickstart

```bash
git clone https://github.com/ilPicc0ne/yt_scraper.git && cd yt_scraper
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scrape.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

That writes `output/<date>_<title>.md` with the transcript and a `_(TODO)_` placeholder where
the summary goes. Fill it in yourself, or let an LLM do it — see below.

### Wire it into Claude Code

```bash
claude mcp add yt-scraper --scope user -- "$PWD/.venv/bin/python" "$PWD/mcp_server.py"
```

Check with `claude mcp list` or `/mcp` in a session. User scope means it's available in every
project, not just this one. Re-run the command after moving the folder — paths are absolute.

<details>
<summary><b>Claude Desktop instead?</b></summary>

Add to `claude_desktop_config.json`:

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

## Tools

| Tool | What it does |
| --- | --- |
| `get_transcript` | Title, channel, URL, plain-text transcript. Read-only, writes nothing. |
| `scrape_video` | Writes `output/<date>_<title>.md`. Won't overwrite unless `overwrite=true`. |
| `save_summary` | Drops your summary into the placeholder. Refuses to write outside `output/`. |
| `list_outputs` | Every output file, and whether its summary is still pending. |

Both guards matter in practice: a re-scrape can't clobber a summary you spent real thought on,
and a confused model can't write files across your disk.

## CLI reference

```bash
.venv/bin/python scrape.py <url-or-id>              # scrape
.venv/bin/python scrape.py <id> --languages en de   # caption preference order (default: de en)
.venv/bin/python scrape.py <id> --overwrite         # replace an existing file
.venv/bin/python scrape.py -- -abc123xyz9           # IDs starting with "-" need the --
```

Prints the path it wrote.

## Good to know

- **Captions, not audio.** Transcripts come from
  [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api). Videos without
  captions fail, and YouTube rate-limits datacenter IPs — this is happiest on a home connection.
- **Auto-captions have no punctuation.** Sentences get split on a best-effort basis, so
  paragraph breaks in auto-generated transcripts are approximate.
- **No API key, anywhere.** Titles come from YouTube's public oEmbed endpoint.
- **German headings** (`Zusammenfassung`, `Volltranskript`) are the author's default — one string
  in `scrape.py` changes them.
- **`output/` is gitignored.** Scraped content stays on your machine. Mind the copyright of what
  you scrape before republishing it.
- **Contributing to the MCP server?** Never `print()` to stdout — stdout *is* the transport. Use
  stderr, and raise `ToolError` for expected failures.

## License

MIT — see [LICENSE](LICENSE).
