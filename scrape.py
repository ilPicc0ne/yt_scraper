#!/usr/bin/env python3
"""Fetch a YouTube transcript and write output/<YYYY-MM-DD>_<title>.md
with a summary placeholder followed by the full transcript.

CLI:  .venv/bin/python scrape.py <video_id_or_url> [--languages de en]
Also imported by mcp_server.py.
"""
import argparse, datetime, json, re, sys, urllib.request, urllib.parse
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
PLACEHOLDER = "_(TODO)_"
# None = auto: use whatever caption track the video actually has, preferring a
# human-written one. Pass an explicit list to force a preference order.
DEFAULT_LANGS = None

# Headings written into each output file. Swap in another language if you like --
# only SUMMARY_HEADING is referenced elsewhere (mcp_server.py mentions it in a docstring).
# German set: "Kanal", "Video", "Gescraped", "Sprachen (Priorität)",
#             "Zusammenfassung", "Volltranskript"
LABEL_CHANNEL = "Channel"
LABEL_VIDEO = "Video"
LABEL_SCRAPED = "Scraped"
LABEL_TRANSCRIPT = "Transcript"
SUMMARY_HEADING = "Summary"
TRANSCRIPT_HEADING = "Full transcript"


def video_id(s: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", s)
    return m.group(1) if m else s.strip()


def title_of(vid: str) -> tuple[str, str]:
    url = ("https://www.youtube.com/oembed?url="
           + urllib.parse.quote(f"https://www.youtube.com/watch?v={vid}", safe="")
           + "&format=json")
    with urllib.request.urlopen(url, timeout=15) as r:
        d = json.load(r)
    return d["title"], d.get("author_name", "")


def slug(t: str) -> str:
    t = re.sub(r"[/\\:*?\"<>|]", "", t)
    return re.sub(r"\s+", " ", t).strip()[:120]


def paragraphs(raw: str, width: int = 600) -> list[str]:
    words = re.sub(r"\s+", " ", " ".join(l.strip() for l in raw.splitlines() if l.strip()))
    out, cur = [], ""
    for s in re.split(r"(?<=[.!?]) ", words):
        cur = (cur + " " + s).strip()
        if len(cur) > width:
            out.append(cur); cur = ""
    if cur:
        out.append(cur)
    return out


def pick_track(tracks, languages: list[str] | None = None):
    """Choose which caption track to fetch.

    With `languages` given, honour that preference order (a human-written track
    still wins over an auto-generated one in the same language). Without it,
    take the video's own captions: a human-written track if there is one,
    otherwise the first auto-generated track, whatever language that is.
    """
    if languages:
        return tracks.find_transcript(languages)
    available = list(tracks)
    if not available:
        raise RuntimeError("video has no captions")
    return next((t for t in available if not t.is_generated), available[0])


def fetch_transcript(vid: str, languages: list[str] | None = None) -> dict:
    """Fetch the best caption track; return its text and which track it was."""
    try:
        track = pick_track(YouTubeTranscriptApi().list(vid), languages)
        fetched = track.fetch()
    except Exception as e:
        raise RuntimeError(f"could not fetch a transcript for {vid}: {e}") from e
    return {"text": " ".join(s.text for s in fetched.snippets),
            "language": fetched.language, "language_code": fetched.language_code,
            "is_generated": fetched.is_generated}


def get_transcript(video: str, languages: list[str] | None = None) -> dict:
    vid = video_id(video)
    title, author = title_of(vid)
    t = fetch_transcript(vid, languages)
    return {"video_id": vid, "title": title, "channel": author,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "language": t["language"], "language_code": t["language_code"],
            "is_generated": t["is_generated"],
            "transcript": "\n\n".join(paragraphs(t["text"]))}


def scrape_video(video: str, languages: list[str] | None = None, overwrite: bool = False) -> Path:
    """Write the output file with a summary placeholder; return its path.
    Refuses to overwrite an existing file unless overwrite=True."""
    t = get_transcript(video, languages or DEFAULT_LANGS)
    today = datetime.date.today().isoformat()
    path = OUTPUT_DIR / f"{today}_{slug(t['title'])}.md"
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists (pass overwrite=True to replace it)")
    OUTPUT_DIR.mkdir(exist_ok=True)
    path.write_text(
        f"# {t['title']}\n\n"
        f"- **{LABEL_CHANNEL}:** {t['channel']}\n- **{LABEL_VIDEO}:** {t['url']}\n"
        f"- **{LABEL_SCRAPED}:** {today}\n"
        f"- **{LABEL_TRANSCRIPT}:** {t['language']}\n\n"
        f"---\n\n## {SUMMARY_HEADING}\n\n{PLACEHOLDER}\n\n---\n\n## {TRANSCRIPT_HEADING}\n\n"
        + t["transcript"] + "\n"
    )
    return path


def save_summary(path: str, summary_markdown: str) -> Path:
    """Replace the placeholder in an output file with the summary."""
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    p = p.resolve()
    if OUTPUT_DIR.resolve() not in p.parents:
        raise ValueError(f"refusing to write outside {OUTPUT_DIR}: {p}")
    txt = p.read_text()
    if PLACEHOLDER not in txt:
        raise ValueError(f"no {PLACEHOLDER} placeholder in {p.name}; summary already present?")
    p.write_text(txt.replace(PLACEHOLDER, summary_markdown.strip(), 1))
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--languages", nargs="+", default=DEFAULT_LANGS,
                    help="caption language preference order; default: the video's own")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    try:
        print(scrape_video(a.video, a.languages, a.overwrite))
    except Exception as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
