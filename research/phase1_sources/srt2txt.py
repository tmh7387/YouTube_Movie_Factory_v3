"""Convert YouTube auto-caption SRT files to de-duplicated plain-text transcripts.

Auto-captions emit rolling two-line cues, so naively concatenating cues repeats
most words twice.  This script strips indices/timestamps, normalises whitespace
and drops a line when it is a prefix-repeat of the line already emitted.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

TIME_RE = re.compile(r"^\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->")
TAG_RE = re.compile(r"<[^>]+>")


def clean_cues(raw: str) -> list[str]:
    lines: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.isdigit() or TIME_RE.match(line):
            continue
        line = TAG_RE.sub("", line)
        line = line.replace("&nbsp;", " ").replace("&amp;", "&")
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    return lines


def dedupe(lines: list[str]) -> str:
    """Collapse rolling-caption duplication into flowing prose."""
    out: list[str] = []
    for line in lines:
        if not out:
            out.append(line)
            continue
        prev = out[-1]
        if line == prev:
            continue
        # Roll-up caption: the new cue repeats the tail of the previous one.
        if line.startswith(prev):
            out[-1] = line
            continue
        if prev.endswith(line):
            continue
        # Overlap on word boundary (previous tail == new head).
        pw, lw = prev.split(), line.split()
        merged = False
        for n in range(min(len(pw), len(lw), 12), 2, -1):
            if pw[-n:] == lw[:n]:
                out[-1] = prev + " " + " ".join(lw[n:])
                merged = True
                break
        if not merged:
            out.append(line)
    return " ".join(out)


def paragraphs(text: str, target: int = 110) -> str:
    """Wrap into readable paragraphs, breaking only at sentence ends."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    buf: list[str] = []
    count = 0
    for sentence in sentences:
        buf.append(sentence)
        count += len(sentence.split())
        if count >= target:
            chunks.append(" ".join(buf))
            buf, count = [], 0
    if buf:
        chunks.append(" ".join(buf))
    return "\n\n".join(chunks)


def main(paths: list[str]) -> None:
    for p in paths:
        src = Path(p)
        text = dedupe(clean_cues(src.read_text(encoding="utf-8", errors="replace")))
        dst = src.with_suffix(".txt")
        dst.write_text(paragraphs(text) + "\n", encoding="utf-8")
        print(f"{src.name} -> {dst.name}  ({len(text.split())} words)")


if __name__ == "__main__":
    main(sys.argv[1:])
