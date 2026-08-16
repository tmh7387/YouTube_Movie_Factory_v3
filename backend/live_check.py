"""
live_check — the one command that talks to the real outside world.

Everything in tests/ replaces the vendors with stand-ins. That proves the wiring
executes; it cannot prove the vendors answer the way the code expects. This script
makes the smallest real call to each one and reports what actually came back.

    python -m live_check              # everything except video generation
    python -m live_check --all        # including video generation (slow, costs more)
    python -m live_check --only openai_edit anthropic_vision
    python -m live_check --list

Exit code is 0 when every check that ran passed. Skipped checks (no credentials) do
not fail the run — they are reported so you can see what was not covered.

Costs real money. The default set is a handful of cents; --all adds one video
generation, which is the expensive one.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import io
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Awaitable, Callable, Optional

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

OK, FAIL, SKIP = "ok", "fail", "skip"


@dataclass
class Result:
    status: str
    detail: str


@dataclass
class Check:
    name: str
    what: str
    run: Callable[["Context"], Awaitable[Result]]
    slow: bool = False


@dataclass
class Context:
    """Carries artefacts between checks — the video check needs the image check's URL."""
    image_url: Optional[str] = None
    local_image: Optional[Path] = None
    notes: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Fixtures the checks need
# ---------------------------------------------------------------------------

def _tiny_png(size=(256, 256), colour=(40, 90, 120)) -> bytes:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", size, colour)
    draw = ImageDraw.Draw(img)
    draw.ellipse((size[0] // 4, size[1] // 4, size[0] * 3 // 4, size[1] * 3 // 4),
                 fill=(220, 200, 150))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def _tiny_jpeg() -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (320, 180), (30, 70, 50)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _keys(payload) -> str:
    if isinstance(payload, dict):
        return "{" + ", ".join(sorted(payload)[:8]) + "}"
    if isinstance(payload, list):
        return f"[{len(payload)} items]"
    return type(payload).__name__


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

async def check_config(_ctx: Context) -> Result:
    from app.core.config import settings

    required = {
        "COMETAPI_API_KEY": settings.COMETAPI_API_KEY,
        "ANTHROPIC_API_KEY": settings.ANTHROPIC_API_KEY,
        "GEMINI_API_KEY": settings.GEMINI_API_KEY,
        "YOUTUBE_API_KEY": settings.YOUTUBE_API_KEY,
        "DATABASE_URL": settings.DATABASE_URL,
    }
    optional = {
        "OPENAI_API_KEY": settings.OPENAI_API_KEY,
        "SUPABASE_URL": settings.SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": settings.SUPABASE_SERVICE_KEY,
    }
    missing = [k for k, v in required.items() if not v]
    absent_optional = [k for k, v in optional.items() if not v]

    detail = f"optional missing: {', '.join(absent_optional) or 'none'}"
    if missing:
        return Result(FAIL, f"required missing: {', '.join(missing)}")
    return Result(OK, detail)


async def check_binaries(_ctx: Context) -> Result:
    missing = [b for b in ("ffmpeg", "ffprobe") if not shutil.which(b)]
    if missing:
        return Result(FAIL, f"not on PATH: {', '.join(missing)} — assembly and QA will fail")
    version = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout
    return Result(OK, version.splitlines()[0][:60])


async def check_database(_ctx: Context) -> Result:
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
        current = (await session.execute(
            text("SELECT version_num FROM alembic_version")
        )).scalar_one_or_none()

    heads = subprocess.run(
        [sys.executable, "-c", "from alembic.config import main; main(argv=['heads'])"],
        cwd=str(BACKEND_ROOT), capture_output=True, text=True, timeout=120,
    ).stdout.strip()

    if not current:
        return Result(FAIL, "no alembic_version row — run `alembic upgrade head`")
    if current not in heads:
        return Result(FAIL, f"schema at {current}, head is {heads.split()[0]} — run `alembic upgrade head`")
    return Result(OK, f"connected, schema at head ({current})")


async def check_anthropic_text(_ctx: Context) -> Result:
    from anthropic import AsyncAnthropic

    from app.core.config import settings

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = await client.messages.create(
        model=settings.CLAUDE_FAST_MODEL,
        max_tokens=16,
        messages=[{"role": "user", "content": "Reply with the single word: ready"}],
    )
    return Result(OK, f"{settings.CLAUDE_FAST_MODEL} -> {response.content[0].text.strip()[:40]!r}")


async def check_anthropic_vision(_ctx: Context) -> Result:
    """
    The QA gate's exact call. Worth its own check because it asks the model for strict
    JSON — a model that answers in prose turns every scene into 'skipped', which reads
    as 'QA is off' rather than 'QA is broken'.
    """
    from app.services.qa_service import qa_service

    frame = BACKEND_ROOT / "env" / "tmp" / "live_check_frame.jpg"
    frame.parent.mkdir(parents=True, exist_ok=True)
    frame.write_bytes(_tiny_jpeg())

    verdict = await qa_service._ask_claude(
        frame,
        qa_service.build_review_prompt(
            image_prompt="a flat green field, no people",
            style_lock={"color_palette": ["#1e4632"], "visual_rules": ["flat colour"]},
            character=None,
        ),
    )

    required = {"pass", "character_match", "style_match", "prompt_adherence", "artifacts", "notes"}
    missing = required - set(verdict)
    if missing:
        return Result(FAIL, f"verdict JSON missing keys: {sorted(missing)}")
    status = qa_service.classify(verdict)
    return Result(OK, f"strict JSON honoured, classified {status}")


async def check_gemini(_ctx: Context) -> Result:
    from app.core.config import settings

    import httpx

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models"
        f"?key={settings.GEMINI_API_KEY}"
    )
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url)
    if response.status_code != 200:
        return Result(FAIL, f"HTTP {response.status_code}: {response.text[:150]}")
    names = [m["name"].split("/")[-1] for m in response.json().get("models", [])]
    configured = settings.GEMINI_MODEL
    if configured not in names:
        return Result(FAIL, f"GEMINI_MODEL={configured} not in the {len(names)} models this key can see")
    return Result(OK, f"{len(names)} models visible, {configured} available")


async def check_youtube(_ctx: Context) -> Result:
    from app.services.youtube_service import youtube_service

    videos = await asyncio.to_thread(youtube_service.search_videos, "cinematic b roll")
    if not videos:
        return Result(FAIL, "search returned nothing — check quota and API enablement")
    return Result(OK, f"search returned {len(videos)}, first: {videos[0].get('title', '?')[:40]!r}")


async def check_supabase(_ctx: Context) -> Result:
    import httpx

    from app.core.config import settings
    from app.services.supabase_storage_service import supabase_storage

    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY):
        return Result(SKIP, "SUPABASE_URL / SUPABASE_SERVICE_KEY not set")

    payload = f"live_check {time.time()}".encode()
    upload = await supabase_storage.upload_file(
        file_bytes=payload, filename="live_check.txt", folder="live_check"
    )
    if "error" in upload:
        return Result(FAIL, upload["error"][:200])

    # A successful upload to a private bucket still breaks the pipeline, because
    # CometAPI and ffmpeg fetch these URLs anonymously.
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(upload["public_url"])
    if response.status_code != 200:
        return Result(FAIL, f"uploaded but public URL returned HTTP {response.status_code} — bucket is not public")
    return Result(OK, "uploaded and publicly readable")


async def check_cometapi_image(ctx: Context) -> Result:
    from app.core.config import settings
    from app.services.media_gen_service import media_gen_service

    result = await media_gen_service.generate_image(
        "a single grey pebble on white seamless background, product photo",
        model=settings.DEFAULT_IMAGE_MODEL,
        size="1280x720",
    )
    if "error" in result:
        return Result(FAIL, result["error"][:200])
    ctx.image_url = result["url"]
    return Result(OK, f"{settings.DEFAULT_IMAGE_MODEL} -> {result['url'][:70]}")


async def check_openai_generate(_ctx: Context) -> Result:
    from app.core.config import settings
    from app.services.gpt_image_service import gpt_image_service

    if not settings.OPENAI_API_KEY:
        return Result(SKIP, "OPENAI_API_KEY not set — reference anchoring will be unavailable")

    result = await gpt_image_service.generate_image(
        "a single grey pebble on white seamless background", size="1024x1024"
    )
    if "error" in result:
        return Result(FAIL, result["error"][:200])
    return Result(OK, f"{settings.OPENAI_IMAGE_MODEL} returned {len(result['b64_json'])} b64 chars")


async def check_openai_edit(ctx: Context) -> Result:
    """
    The single highest-risk call in the product: reference-anchored generation with
    more than one reference. It is the whole basis of character consistency, and until
    now it had never been executed.
    """
    from app.core.config import settings
    from app.services.gpt_image_service import gpt_image_service

    if not settings.OPENAI_API_KEY:
        return Result(SKIP, "OPENAI_API_KEY not set")

    ref_dir = BACKEND_ROOT / "env" / "tmp" / "live_check_refs"
    ref_dir.mkdir(parents=True, exist_ok=True)
    refs = []
    for i, colour in enumerate([(200, 60, 60), (60, 200, 120)]):
        path = ref_dir / f"ref{i}.png"
        path.write_bytes(_tiny_png(colour=colour))
        refs.append(str(path))

    result = await gpt_image_service.generate_with_character(
        prompt="the same round object, three-quarter view, plain background",
        character_description="a round object, cream coloured, matte finish",
        reference_image_paths=refs,
        size="1024x1024",
    )
    if "error" in result:
        return Result(FAIL, result["error"][:200])
    if not result.get("character_consistent"):
        return Result(
            FAIL,
            "fell back to plain generation — the edits call failed, see the log above",
        )
    return Result(OK, f"{result['ref_count']} references accepted, {len(result['b64_json'])} b64 chars")


async def check_cometapi_video(ctx: Context) -> Result:
    from app.core.config import settings
    from app.services.media_gen_service import media_gen_service

    if not ctx.image_url:
        return Result(SKIP, "no image from the CometAPI image check to animate")

    result = await media_gen_service.animate_image(
        image_url=ctx.image_url,
        prompt="slow push in, static subject",
        model=settings.SEEDANCE_VIDEO_MODEL,
        duration=4,
        mode="std",
    )
    if "error" in result:
        return Result(FAIL, result["error"][:250])
    return Result(OK, f"{settings.SEEDANCE_VIDEO_MODEL} -> {result['url'][:70]}")


CHECKS: list[Check] = [
    Check("config", "required and optional credentials present", check_config),
    Check("binaries", "ffmpeg and ffprobe on PATH", check_binaries),
    Check("database", "connects and schema is at head", check_database),
    Check("anthropic_text", "Claude answers a trivial prompt", check_anthropic_text),
    Check("anthropic_vision", "QA gate gets strict JSON back from a real frame", check_anthropic_vision),
    Check("gemini", "the configured Gemini model is visible to this key", check_gemini),
    Check("youtube", "search returns results", check_youtube),
    Check("supabase", "upload succeeds and the URL is publicly readable", check_supabase),
    Check("cometapi_image", "still image generation", check_cometapi_image),
    Check("openai_generate", "plain OpenAI image generation", check_openai_generate),
    Check("openai_edit", "reference-anchored generation with 2 references", check_openai_edit),
    Check("cometapi_video", "animate a still (slow, the expensive one)", check_cometapi_video, slow=True),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

SYMBOL = {OK: "PASS", FAIL: "FAIL", SKIP: "SKIP"}


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all", action="store_true", help="include slow/expensive checks")
    parser.add_argument("--only", nargs="+", metavar="NAME", help="run only these checks")
    parser.add_argument("--list", action="store_true", help="list check names and exit")
    args = parser.parse_args()

    if args.list:
        for check in CHECKS:
            print(f"  {check.name:<18} {check.what}{'  [slow]' if check.slow else ''}")
        return 0

    selected = [c for c in CHECKS if (args.all or not c.slow)]
    if args.only:
        unknown = set(args.only) - {c.name for c in CHECKS}
        if unknown:
            print(f"unknown check(s): {', '.join(sorted(unknown))}")
            return 2
        selected = [c for c in CHECKS if c.name in args.only]

    print(f"live_check — {len(selected)} checks against real services\n")
    ctx = Context()
    results: list[tuple[Check, Result, float]] = []

    for check in selected:
        started = time.monotonic()
        try:
            result = await check.run(ctx)
        except Exception as e:
            result = Result(FAIL, f"{type(e).__name__}: {e}"[:250])
        elapsed = time.monotonic() - started
        results.append((check, result, elapsed))
        print(f"  {SYMBOL[result.status]}  {check.name:<18} {elapsed:6.1f}s  {result.detail}")

    failures = [c.name for c, r, _ in results if r.status == FAIL]
    skipped = [c.name for c, r, _ in results if r.status == SKIP]

    print()
    print(f"{len(results) - len(failures) - len(skipped)} passed, "
          f"{len(failures)} failed, {len(skipped)} skipped")
    if skipped:
        print(f"not covered: {', '.join(skipped)}")
    if failures:
        print(f"failed: {', '.join(failures)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
