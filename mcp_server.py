#!/usr/bin/env python3
"""Local MCP server (stdio) exposing the YouTube scraper.

Register with Claude Code:
  claude mcp add yt-scraper --scope user -- <abs>/.venv/bin/python <abs>/mcp_server.py
Never print to stdout here: stdout is the MCP transport.
"""
import sys
from pathlib import Path

from typing import TypedDict

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scrape  # noqa: E402

mcp = MCPServer("yt-scraper")


class Transcript(TypedDict):
    video_id: str
    title: str
    channel: str
    url: str
    language: str
    language_code: str
    is_generated: bool
    transcript: str


def _guard(fn, *a, **kw):
    """Run fn; turn expected failures into ToolError so the client sees the reason."""
    try:
        return fn(*a, **kw)
    except (FileExistsError, FileNotFoundError, ValueError, RuntimeError, OSError) as e:
        raise ToolError(str(e)) from e


@mcp.tool(title="Get YouTube transcript",
          annotations=ToolAnnotations(read_only_hint=True, open_world_hint=True))
def get_transcript(video: str, languages: list[str] | None = None) -> Transcript:
    """Fetch title, channel, URL and the plain-text transcript of a YouTube video.
    `video` may be a video ID or any youtube.com / youtu.be URL. Leave `languages`
    unset to use the video's own captions (a human-written track if one exists,
    otherwise the auto-generated one); pass a list to force a preference order."""
    return _guard(scrape.get_transcript, video, languages)


@mcp.tool(title="Scrape video into output file")
def scrape_video(video: str, languages: list[str] | None = None,
                 overwrite: bool = False) -> str:
    """Fetch the transcript and write output/<YYYY-MM-DD>_<title>.md containing
    metadata, a `_(TODO)_` summary placeholder and the full transcript.
    Returns the absolute file path. Follow up with save_summary. Refuses to
    overwrite an existing file (which may hold a finished summary) unless overwrite=True."""
    return str(_guard(scrape.scrape_video, video, languages, overwrite))


@mcp.tool(title="Save summary into output file")
def save_summary(path: str, summary_markdown: str) -> str:
    """Replace the `_(TODO)_` placeholder in an output file (as returned by
    scrape_video) with a detailed markdown summary in the video's language.
    Use H3 headings; the file already carries the summary H2 above the placeholder."""
    return str(_guard(scrape.save_summary, path, summary_markdown))


@mcp.tool(title="List scraped output files",
          annotations=ToolAnnotations(read_only_hint=True))
def list_outputs() -> list[dict]:
    """List files in output/ with whether their summary is still a placeholder."""
    out = []
    for p in sorted(scrape.OUTPUT_DIR.glob("*.md")):
        out.append({"path": str(p), "name": p.name,
                    "summary_pending": scrape.PLACEHOLDER in p.read_text()})
    return out


if __name__ == "__main__":
    mcp.run()
