#!/usr/bin/env python3
"""Package a repo skill as a .skill zip for upload to claude.ai.

The repo is the source of truth for both delivery targets: the YTMF backend
loads SKILL.md off disk, and claude.ai gets the same content as a zip. This
script only does the packaging — it never edits a skill.

    python skills/_mirror/build_skill.py seedance2-director-v2
    python skills/_mirror/build_skill.py seedance2-director-v2 --as seedance2-director

`--as` sets the folder name inside the zip, for when the account's slug differs
from the repo folder (seedance2-director-v2 on disk, seedance2-director in the
account). It does not rename anything on disk.

Output lands in skills/_mirror/build/. Record every upload in SYNC_LOG.md.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CATEGORIES = ("general", "music_video", "product_brand", "asmr")
BUILD = REPO / "skills" / "_mirror" / "build"


def find_skill(slug: str) -> Path:
    for cat in CATEGORIES:
        d = REPO / "skills" / cat / slug
        if (d / "SKILL.md").is_file():
            return d
    sys.exit(
        f"error: no skills/<category>/{slug}/SKILL.md found.\n"
        f"       searched: {', '.join(CATEGORIES)}"
    )


def frontmatter_name(skill_md: Path) -> str | None:
    head = skill_md.read_text(encoding="utf-8")[:4000]
    m = re.search(r"^name:\s*(\S+)\s*$", head, re.M)
    return m.group(1) if m else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", help="repo folder name under skills/<category>/")
    ap.add_argument("--as", dest="as_slug", help="folder name inside the zip")
    args = ap.parse_args()

    src = find_skill(args.slug)
    skill_md = src / "SKILL.md"
    inner = args.as_slug or frontmatter_name(skill_md) or args.slug

    files = [skill_md]
    refs = src / "references"
    if refs.is_dir():
        files += sorted(p for p in refs.rglob("*") if p.is_file())

    BUILD.mkdir(parents=True, exist_ok=True)
    out = BUILD / f"{inner}.skill"

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f"{inner}/{f.relative_to(src).as_posix()}")

    digest = hashlib.sha256(out.read_bytes()).hexdigest()[:12]
    print(f"built  {out.relative_to(REPO)}")
    print(f"  slug inside zip : {inner}")
    print(f"  files           : {len(files)}")
    for f in files:
        print(f"      {f.relative_to(src).as_posix()}  ({sum(1 for _ in f.open(encoding='utf-8', errors='ignore'))} lines)")
    print(f"  size            : {out.stat().st_size:,} bytes")
    print(f"  sha256[:12]     : {digest}")
    print()
    print("Upload it, then add a line to skills/_mirror/SYNC_LOG.md.")


if __name__ == "__main__":
    main()
