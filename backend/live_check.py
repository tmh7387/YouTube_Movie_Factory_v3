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

# Windows defaults to the Proactor loop, which psycopg refuses to run async on
# ("Psycopg cannot use the 'ProactorEventLoop'"). run.py and app/main.py already do
# this; a standalone entry point has to do it for itself or every database call fails.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
    import logging

    from sqlalchemy import text

    # The engine is built with echo on. Its SQL log prints between the check lines and
    # pushes the report off the screen, which is the one thing this script must not do.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

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
    from app.services.anthropic_response import response_text

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = await client.messages.create(
        model=settings.CLAUDE_FAST_MODEL,
        max_tokens=16,
        messages=[{"role": "user", "content": "Reply with the single word: ready"}],
    )
    return Result(OK, f"{settings.CLAUDE_FAST_MODEL} -> {response_text(response).strip()[:40]!r}")


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

    # A PNG, not a text file: the bucket restricts mime types, and images are what the
    # reference-sheet feature actually uploads. Testing with text/plain proved nothing
    # about the path the app uses and failed on a correctly configured bucket.
    upload = await supabase_storage.upload_file(
        file_bytes=_tiny_png(), filename=f"live_check_{int(time.time())}.png",
        folder="live_check",
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


async def check_higgsfield_cli(_ctx: Context) -> Result:
    """
    Installed, signed in, and pointed at models this account can reach.

    A wrong model id here is the likeliest failure: Higgsfield's ids use underscores
    (seedance_2_5) and are not the CometAPI names (doubao-seedance-2-5).
    """
    from app.core.config import settings
    from app.services.higgsfield_service import higgsfield_service

    if not settings.HIGGSFIELD_ENABLED:
        return Result(SKIP, "HIGGSFIELD_ENABLED is false — CometAPI is doing all the work")
    if not higgsfield_service.binary():
        return Result(FAIL, "CLI not on PATH — run: npm i -g @higgsfield/cli")
    if not await higgsfield_service.is_authenticated():
        return Result(FAIL, higgsfield_service.last_auth_error or
                      "not signed in — run: higgsfield auth login")

    problems = []
    for kind, configured in (
        ("video", settings.HIGGSFIELD_VIDEO_MODEL),
        ("image", settings.HIGGSFIELD_IMAGE_MODEL),
        ("image", settings.HIGGSFIELD_REFERENCE_IMAGE_MODEL),
    ):
        listing = await higgsfield_service.list_models(kind)
        if "error" in listing:
            return Result(FAIL, listing["error"][:200])
        if configured not in listing["models"]:
            close = [m for m in listing["models"] if configured.split("_")[0] in m][:4]
            problems.append(f"{configured} is not a {kind} model this account has" +
                            (f" (did you mean {', '.join(close)}?)" if close else ""))

    if problems:
        return Result(FAIL, " | ".join(problems))
    return Result(OK, "signed in, all three configured models available")


async def check_higgsfield_params(_ctx: Context) -> Result:
    """
    Print each configured model's real parameter list.

    Media flag names differ per model — nano_banana_2 refuses --image-references even
    though the CLI's own help advertises it. The service searches a candidate list at
    runtime; this check shows the authoritative answer so the list can be trimmed.
    """
    from app.core.config import settings
    from app.services.higgsfield_service import higgsfield_service

    if not await higgsfield_service.available():
        return Result(SKIP, f"Higgsfield unavailable: {higgsfield_service.last_auth_error}")

    lines = []
    for model in (settings.HIGGSFIELD_REFERENCE_IMAGE_MODEL, settings.HIGGSFIELD_VIDEO_MODEL):
        described = await higgsfield_service.describe_model(model)
        if "error" in described:
            lines.append(f"{model}: {described['error'][:120]}")
            continue
        lines.append(f"{model}: {_param_names(described)}")
    return Result(OK, " || ".join(lines))


def _param_names(described: dict) -> str:
    """
    The parameter names live under `params`, not at the top level of the model record.

    `higgsfield model get` returns {display_name, job_set_type, params, type}; printing
    those four keys says nothing about which flags a model accepts, which is the whole
    question. `params` may be a mapping of name -> spec or a list of specs, so handle
    both and fall back to the raw text.
    """
    parsed = described.get("parsed")
    if not isinstance(parsed, dict):
        return described.get("raw", "")[:300]

    params = parsed.get("params")
    if isinstance(params, dict):
        return ", ".join(sorted(params.keys())) or "(no params declared)"
    if isinstance(params, list):
        names = [
            item.get("name") or item.get("key") or str(item)
            for item in params
            if isinstance(item, (dict, str))
        ]
        return ", ".join(str(n) for n in names) or "(empty params list)"
    return f"params was {type(params).__name__}: {str(params)[:250]}"


async def check_higgsfield_schema(_ctx: Context) -> Result:
    """
    Print the FULL spec of each model's media parameter, not just its name.

    The name alone is not enough. `input_images` is an array of objects, and the object
    shape is not documented: an array of ids answers "params.input_images.0: Input
    should be a valid object". The service searches candidate shapes at runtime; this
    check prints the authoritative spec so the search can be replaced by the answer.
    """
    from app.core.config import settings
    from app.services.higgsfield_service import higgsfield_service

    if not await higgsfield_service.available():
        return Result(SKIP, f"Higgsfield unavailable: {higgsfield_service.last_auth_error}")

    media_names = ("input_images", "medias", "image", "images", "reference_images")
    lines = []
    for model in (settings.HIGGSFIELD_REFERENCE_IMAGE_MODEL, settings.HIGGSFIELD_VIDEO_MODEL):
        described = await higgsfield_service.describe_model(model)
        parsed = described.get("parsed")
        if not isinstance(parsed, dict):
            lines.append(f"{model}: {described.get('raw', described.get('error', ''))[:300]}")
            continue

        params = parsed.get("params")
        specs = {}
        if isinstance(params, dict):
            specs = {k: v for k, v in params.items() if k in media_names}
        elif isinstance(params, list):
            specs = {
                item.get("name"): item
                for item in params
                if isinstance(item, dict) and item.get("name") in media_names
            }
        if not specs:
            lines.append(f"{model}: no media parameter among {', '.join(media_names)}")
            continue
        lines.append(f"{model}: {json.dumps(specs)[:800]}")
    return Result(OK, " || ".join(lines))


async def check_higgsfield_image(ctx: Context) -> Result:
    """The primary still generator, with a reference picture attached."""
    from app.core.config import settings
    from app.services.higgsfield_service import higgsfield_service

    if not await higgsfield_service.available():
        return Result(SKIP, f"Higgsfield unavailable: {higgsfield_service.last_auth_error}")

    ref_dir = BACKEND_ROOT / "env" / "tmp" / "live_check_refs"
    ref_dir.mkdir(parents=True, exist_ok=True)
    ref = ref_dir / "hf_ref.png"
    ref.write_bytes(_tiny_png(colour=(180, 120, 60)))

    result = await higgsfield_service.generate_image(
        prompt="the same round object on a plain background, three-quarter view",
        reference_paths=[str(ref)],
    )
    if "error" in result:
        # Not truncated. When the CLI answers with the list of values it accepts,
        # that list IS the answer, and cutting it throws the answer away.
        return Result(FAIL, result["error"])
    ctx.image_url = result["url"]

    # Keep the generated still on disk so the animation check animates a real generated
    # picture, which is what production does — not the tiny reference PNG.
    try:
        import httpx

        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            payload = (await client.get(result["url"])).content
        still = ref_dir / "hf_generated.png"
        still.write_bytes(payload)
        ctx.local_image = still
    except Exception:                      # noqa: BLE001 - the still is a convenience
        pass

    # Name the flag and element shape that worked. The service searches for them on
    # first use and forgets at process end; printing them is how the search gets
    # replaced by the answer in ARRAY_ELEMENT_SHAPES.
    settled = higgsfield_service._media_flag.get(settings.HIGGSFIELD_REFERENCE_IMAGE_MODEL)
    how = f" via {settled[0]} {settled[2]}" if settled else ""
    return Result(
        OK,
        f"{result['model']}, {result['ref_count']} ref{how} -> {result['url'][:60]}",
    )


async def check_cometapi_image(ctx: Context) -> Result:
    from app.core.config import settings
    from app.services.media_gen_service import media_gen_service

    result = await media_gen_service.generate_image(
        "a single grey pebble on white seamless background, product photo",
        model=settings.DEFAULT_IMAGE_MODEL,
        size="1280x720",
    )
    if "error" in result:
        # "model_not_found" is a settings problem, not a broken integration. Say which
        # models the key can actually reach, so the fix is one line in env/.env.
        hint = ""
        if "model_not_found" in result["error"] or "no available channel" in result["error"]:
            available = await _cometapi_models()
            hint = (
                f" | DEFAULT_IMAGE_MODEL={settings.DEFAULT_IMAGE_MODEL} is not served to "
                f"this key. Image models this key can reach: {available}"
            )
        return Result(FAIL, result["error"][:160] + hint)
    if result.get("b64_json"):
        # gpt-image models return base64 and never a URL, even through the gateway.
        # No ctx.image_url, so the video check that animates it will skip.
        return Result(OK, f"{settings.DEFAULT_IMAGE_MODEL} -> {len(result['b64_json'])} b64 chars")
    ctx.image_url = result["url"]
    return Result(OK, f"{settings.DEFAULT_IMAGE_MODEL} -> {result['url'][:70]}")


async def _cometapi_models(limit: int = 12) -> str:
    """Ask CometAPI which models this key can use. Best effort — never raises."""
    import httpx

    from app.core.config import settings

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                "https://api.cometapi.com/v1/models",
                headers={"Authorization": f"Bearer {settings.COMETAPI_API_KEY}"},
            )
        if response.status_code != 200:
            return f"(could not list models: HTTP {response.status_code})"
        ids = [m.get("id", "") for m in response.json().get("data", [])]
    except Exception as e:
        return f"(could not list models: {e})"

    picture = [
        i for i in ids
        if any(k in i.lower() for k in ("image", "seedream", "flux", "banana", "dall"))
    ]
    shown = sorted(picture)[:limit]
    more = f" (+{len(picture) - len(shown)} more)" if len(picture) > len(shown) else ""
    return ", ".join(shown) + more if shown else f"none matched, {len(ids)} models total"


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


async def check_higgsfield_video(ctx: Context) -> Result:
    """
    The primary animator. Never run for real until now — the check did not exist, which
    is why `--only higgsfield_video` answered "unknown check".

    It animates a LOCAL still, not a URL. That is the path production uses: the CLI
    uploads the file itself, so there is no pre-signed URL to expire between generating
    a still and animating it.
    """
    from app.core.config import settings
    from app.services.higgsfield_service import higgsfield_service

    if not await higgsfield_service.available():
        return Result(SKIP, f"Higgsfield unavailable: {higgsfield_service.last_auth_error}")

    still = ctx.local_image
    if not still or not Path(still).is_file():
        still = BACKEND_ROOT / "env" / "tmp" / "live_check_refs" / "hf_ref.png"
        still.parent.mkdir(parents=True, exist_ok=True)
        still.write_bytes(_tiny_png(colour=(180, 120, 60)))

    result = await higgsfield_service.animate_image(
        image_path=str(still),
        prompt="slow push in, static subject",
        duration=4,
    )
    if "error" in result:
        return Result(FAIL, result["error"])
    settled = higgsfield_service._media_flag.get(settings.HIGGSFIELD_VIDEO_MODEL)
    how = f" via {settled[0]} {settled[2]}" if settled else ""
    return Result(OK, f"{settings.HIGGSFIELD_VIDEO_MODEL}{how} -> {result['url'][:60]}")


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
    Check("higgsfield_cli", "CLI installed, signed in, configured models exist", check_higgsfield_cli),
    Check("higgsfield_params", "show each model's real parameter names", check_higgsfield_params),
    Check("higgsfield_schema", "show the media parameter's full spec", check_higgsfield_schema),
    Check("higgsfield_image", "primary still generation with a reference", check_higgsfield_image, slow=True),
    Check("cometapi_image", "fallback still image generation", check_cometapi_image),
    Check("openai_generate", "plain OpenAI image generation", check_openai_generate),
    Check("openai_edit", "reference-anchored generation with 2 references", check_openai_edit),
    Check("higgsfield_video", "primary animation (slow, the expensive one)", check_higgsfield_video, slow=True),
    Check("cometapi_video", "fallback animation (slow, the expensive one)", check_cometapi_video, slow=True),
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
