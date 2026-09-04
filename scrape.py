#!/usr/bin/env python3
"""Fetch a YouTube transcript and write output/<YYYY-MM-DD>_<title>.md
with a summary placeholder followed by the full transcript.

CLI:  .venv/bin/python scrape.py <video_id_or_url> [--languages de en]
Also imported by mcp_server.py.
"""
import argparse, datetime, json, re, subprocess, sys, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
PLACEHOLDER = "_(TODO)_"
DEFAULT_LANGS = ["de", "en"]


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


def fetch_transcript(vid: str, languages: list[str] | None = None) -> str:
    """Raw transcript text via the youtube_transcript_api CLI in this venv."""
    exe = Path(sys.executable).parent / "youtube_transcript_api"
    r = subprocess.run([str(exe), "--languages", *(languages or DEFAULT_LANGS),
                        "--format", "text", "--", vid], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr.strip()[-1000:] or "youtube_transcript_api failed")
    return r.stdout


def get_transcript(video: str, languages: list[str] | None = None) -> dict:
    vid = video_id(video)
    title, author = title_of(vid)
    text = "\n\n".join(paragraphs(fetch_transcript(vid, languages)))
    return {"video_id": vid, "title": title, "channel": author,
            "url": f"https://www.youtube.com/watch?v={vid}", "transcript": text}


def scrape_video(video: str, languages: list[str] | None = None, overwrite: bool = False) -> Path:
    """Write the output file with a summary placeholder; return its path.
    Refuses to overwrite an existing file unless overwrite=True."""
    langs = languages or DEFAULT_LANGS
    t = get_transcript(video, langs)
    today = datetime.date.today().isoformat()
    path = OUTPUT_DIR / f"{today}_{slug(t['title'])}.md"
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists (pass overwrite=True to replace it)")
    OUTPUT_DIR.mkdir(exist_ok=True)
    path.write_text(
        f"# {t['title']}\n\n"
        f"- **Kanal:** {t['channel']}\n- **Video:** {t['url']}\n"
        f"- **Gescraped:** {today}\n- **Sprachen (Priorität):** {', '.join(langs)}\n\n"
        f"---\n\n## Zusammenfassung\n\n{PLACEHOLDER}\n\n---\n\n## Volltranskript\n\n"
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
    ap.add_argument("--languages", nargs="+", default=DEFAULT_LANGS)
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    try:
        print(scrape_video(a.video, a.languages, a.overwrite))
    except Exception as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
