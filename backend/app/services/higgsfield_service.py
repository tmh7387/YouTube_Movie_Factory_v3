"""
HiggsfieldService — the primary generator, driven through the Higgsfield CLI.

Higgsfield publishes no HTTP API. It ships a CLI (`npm i -g @higgsfield/cli`, a thin
wrapper around a Go binary) and an MCP endpoint. Both authenticate with browser-based
OAuth, so neither can sign itself in on a server. The CLI wins anyway:

  - `--json` prints machine-readable output.
  - `--wait` blocks until the job finishes and reports the result.
  - media flags accept a local file path and upload it for you, which is exactly what
    the bible reference sheets need.
  - `higgsfield auth token` proves a token is stored and refreshed by the CLI, so the
    human signs in once per machine and the app runs unattended after that.

Shelling out is also the pattern this codebase already uses for ffmpeg, ffprobe and
yt-dlp, so it adds no new kind of dependency.

CometAPI stays wired as the fallback. Every method here returns {"error": ...} rather
than raising, so the caller can fall through without a try/except around each call.
"""
import asyncio
import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Keys worth searching for a finished asset, in preference order. The CLI's exact
# response shape is not documented; live_check prints it so this list can be tightened
# rather than guessed at.
URL_KEYS = ("url", "result_url", "output_url", "video_url", "image_url", "download_url")
NESTED_KEYS = ("results", "result", "outputs", "output", "jobs", "data", "items", "assets")

# Which flag carries a picture depends on the model, and the CLI's help is not the
# authority — `higgsfield model get <model>` is. Two live examples:
#
#   nano_banana_2 params: aspect_ratio, folder_id, input_images, prompt, resolution
#   seedance_2_5  params: ..., duration, medias, mode, prompt, resolution, ...
#
# So the image model takes `input_images` directly, while the video model takes the
# structured `medias` field that the CLI's --start-image sugar writes into. Neither
# accepts --image-references, which the CLI's own help advertises.
#
# The real names lead, and the rest stay as fallbacks: a model that declares something
# different should cost one wasted call, not an outage.
# Each candidate is (flag, style). "repeat" passes the flag once per file and lets the
# CLI's media sugar upload it. "array" is for a raw model parameter that declares an
# array type: nano_banana_2 answers "Invalid types: input_images should be array, got
# string" to the repeated form, so those files are uploaded first and the flag carries
# a JSON array of the returned ids.
IMAGE_REFERENCE_FLAGS = (
    ("--input_images", "array"),      # nano_banana_2 — name and type confirmed live
    ("--image-references", "repeat"),
    ("--image", "repeat"),
)
START_IMAGE_FLAGS = (
    ("--start-image", "repeat"),      # CLI sugar that writes into `medias`
    ("--medias", "array"),
    ("--image", "repeat"),
)

# Markers that mean "the flag or its value shape was wrong", as opposed to a real
# failure. Only these are worth retrying with the next candidate.
#   "unknown params"            — the flag is not in this model's parameter list
#   "invalid types"             — right name, wrong value type (string where array goes)
#   "should be a valid"         — right type, wrong element shape. nano_banana_2 answers
#                                 "params.input_images.0: Input should be a valid object"
#                                 to an array of plain id strings.
#   "input should be" / "validation error" — the same class of reply, other wordings
UNKNOWN_PARAM_MARKER = "unknown params"
WRONG_TYPE_MARKER = "invalid types"
RETRY_MARKERS = (
    UNKNOWN_PARAM_MARKER,
    WRONG_TYPE_MARKER,
    "should be a valid",
    "input should be",
    "validation error",
)

# How one uploaded picture is written into an array-typed parameter. The element is an
# object, not a bare id, but which object is not documented, so the shapes are tried in
# order and the winner is remembered per model. Shapes that need a URL are skipped when
# the upload reply carried none.
#
# Each entry is (name, needs_url, builder).
#
# "value/role" leads because that is the media object Higgsfield's own platform uses
# elsewhere: {"value": "<media uuid>", "role": "image"}. A bare id string is not in the
# list at all — it is the shape that produced the error above, so trying it wastes a call.
ARRAY_ELEMENT_SHAPES = (
    ("value/role", False, lambda m: {"value": m["id"], "role": "image"}),
    ("image_url block", True, lambda m: {"type": "image_url", "image_url": m["url"]}),
    ("typed id", False, lambda m: {"type": "image", "id": m["id"]}),
    ("id object", False, lambda m: {"id": m["id"]}),
    ("url object", True, lambda m: {"url": m["url"]}),
    ("value object", False, lambda m: {"value": m["id"]}),
)


class HiggsfieldService:
    def __init__(self):
        self._binary: Optional[str] = None
        self._authenticated: Optional[bool] = None
        self._auth_error: str = ""
        # model id -> the (flag, style) pair that model accepted, learned on first use.
        self._media_flag: Dict[str, tuple] = {}

    @staticmethod
    def _extract_id(payload: Any) -> Optional[str]:
        """Find the media id in an upload reply, without assuming the key."""
        if isinstance(payload, str):
            return payload or None
        if isinstance(payload, list):
            for item in payload:
                found = HiggsfieldService._extract_id(item)
                if found:
                    return found
            return None
        if isinstance(payload, dict):
            for key in ("id", "media_id", "upload_id", "uuid", "media", "job_id"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value
                if isinstance(value, (dict, list)):
                    found = HiggsfieldService._extract_id(value)
                    if found:
                        return found
            for value in payload.values():
                if isinstance(value, (dict, list)):
                    found = HiggsfieldService._extract_id(value)
                    if found:
                        return found
        return None

    async def upload_media(self, path: str) -> Dict[str, Any]:
        """
        Upload one local file and return {"id": ..., "url": ...}.

        Needed for array-typed parameters: the CLI's media sugar uploads for you, but a
        raw model parameter such as input_images wants the uploaded media, not a path.
        The URL may be absent; the element shapes that need it are skipped when it is.
        """
        result = await self._run(
            ["upload", "create", str(Path(path).resolve()), "--json"], timeout=300
        )
        if "error" in result:
            return result
        payload = self.parse_json(result["stdout"])
        media_id = self._extract_id(payload)
        if not media_id:
            return {"error": f"no media id in upload reply: {result['stdout'][:200]}"}
        return {"id": media_id, "url": self.extract_url(payload) or ""}

    async def _run_with_media_flag(
        self,
        model: str,
        base_args: List[str],
        media_paths: List[str],
        candidates: tuple,
        timeout: float,
    ) -> Dict[str, Any]:
        """
        Run the generate command, finding the media flag AND value shape this model wants.

        Three things vary per model and none of them is in the CLI's help:
          - the parameter name ("Unknown params: image-references")
          - the value type ("Invalid types: input_images should be array, got string")
          - the element shape ("params.input_images.0: Input should be a valid object")

        Candidates carry the first two, ARRAY_ELEMENT_SHAPES the third. What works is
        remembered, so the search costs a few cheap failures once per model per process
        rather than once per scene.
        """
        if not media_paths:
            return await self._run(base_args, timeout)

        known = self._media_flag.get(model)
        order = list(candidates)
        if known:
            order.sort(key=lambda pair: pair != known[:2])

        # Uploaded once and reused: the same media serves every flag and shape.
        uploaded: Optional[List[Dict[str, Any]]] = None
        upload_error: Optional[Dict[str, Any]] = None

        async def media() -> Optional[List[Dict[str, Any]]]:
            nonlocal uploaded, upload_error
            if uploaded is None and upload_error is None:
                items = []
                for path in media_paths:
                    reply = await self.upload_media(path)
                    if "error" in reply:
                        upload_error = reply
                        return None
                    items.append(reply)
                uploaded = items
            return uploaded

        def attempts(flag: str, style: str) -> List[tuple]:
            """(shape name, args) pairs to try for one candidate flag."""
            if style != "array":
                args = list(base_args)
                for path in media_paths:
                    args += [flag, path]
                return [("path", args)]
            items = uploaded or []
            out = []
            shapes = list(ARRAY_ELEMENT_SHAPES)
            if known and known[0] == flag:
                shapes.sort(key=lambda s: s[0] != known[2])
            for name, needs_url, build in shapes:
                if needs_url and not all(item.get("url") for item in items):
                    continue
                out.append((name, list(base_args) + [flag, json.dumps([build(i) for i in items])]))
            return out

        last: Dict[str, Any] = {"error": "no media flag attempted"}
        for flag, style in order:
            if style == "array" and await media() is None:
                # Treat a failed upload as this candidate failing, not as the end of the
                # road: another candidate may not need uploads.
                last = upload_error or last
                logger.debug(f"Higgsfield: upload for {flag} failed, trying the next")
                continue

            for shape, args in attempts(flag, style):
                result = await self._run(args, timeout)

                if "error" not in result:
                    if self._media_flag.get(model) != (flag, style, shape):
                        logger.info(f"Higgsfield: {model} takes {flag} as {style}/{shape}")
                        self._media_flag[model] = (flag, style, shape)
                    return result

                reason = result["error"].lower()
                if not any(marker in reason for marker in RETRY_MARKERS):
                    # A real failure — the request was wrong, not the flag.
                    return result
                last = result
                logger.debug(
                    f"Higgsfield: {model} refused {flag} as {style}/{shape}, trying the next"
                )

        return {
            "error": (
                f"{model} accepted none of "
                f"{', '.join(f'{f} ({s})' for f, s in candidates)} for media inputs, "
                f"in any of {len(ARRAY_ELEMENT_SHAPES)} element shapes. "
                f"Run `higgsfield model get {model}` to see its parameters. "
                f"Last reply: {last['error'][:200]}"
            )
        }

    # -- availability ------------------------------------------------------

    def binary(self) -> Optional[str]:
        """Path to the CLI, or None. Cached — this is called once per scene."""
        if self._binary is None:
            configured = settings.HIGGSFIELD_CLI
            self._binary = (
                shutil.which(configured)
                or shutil.which("higgsfield")
                or shutil.which("hf")
                or ""
            )
        return self._binary or None

    async def _run(self, args: List[str], timeout: float) -> Dict[str, Any]:
        """
        Run the CLI and return {"stdout": str} or {"error": str}.

        Blocking subprocess.run in a worker thread, NOT asyncio.create_subprocess_exec.
        On Windows those two requirements collide:

          - psycopg refuses to run async on the Proactor loop, so app/main.py and
            app/db/session.py select WindowsSelectorEventLoopPolicy.
          - asyncio subprocesses are not supported on the Selector loop and raise
            NotImplementedError.

        The app needs the database and this CLI in the same loop, so the async
        subprocess API is simply unavailable to it. Running the blocking call in a
        thread works on every loop and matches assembly_service and qa_service, which
        already shell out to ffmpeg this way.
        """
        binary = self.binary()
        if not binary:
            return {"error": "higgsfield CLI not found on PATH (npm i -g @higgsfield/cli)"}

        def _invoke() -> subprocess.CompletedProcess:
            return subprocess.run(
                [binary, *args],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

        try:
            proc = await asyncio.to_thread(_invoke)
        except subprocess.TimeoutExpired:
            return {"error": f"higgsfield {' '.join(args[:2])} timed out after {timeout:.0f}s"}
        except Exception as e:
            return {"error": f"could not run higgsfield: {type(e).__name__}: {e}"}

        if proc.returncode != 0:
            message = (proc.stderr or "").strip() or (proc.stdout or "").strip()
            return {"error": f"higgsfield {' '.join(args[:2])} failed: {message[-400:]}"}

        return {"stdout": proc.stdout or ""}

    async def is_authenticated(self) -> bool:
        """
        True when a token is stored. A human runs `higgsfield auth login` once per
        machine; the CLI refreshes the token itself from then on.

        The reason for a failure is reported, not collapsed into "not signed in" —
        that message sent someone re-running `auth login` when the real fault was the
        event loop refusing to spawn a subprocess at all.
        """
        if self._authenticated is not None:
            return self._authenticated

        result = await self._run(["auth", "token"], timeout=30)
        if "error" in result:
            self._auth_error = result["error"]
            self._authenticated = False
            logger.warning(
                f"Higgsfield unusable: {result['error']} — falling back to CometAPI"
            )
            return False

        self._authenticated = bool(result["stdout"].strip())
        if not self._authenticated:
            self._auth_error = "no token stored"
            logger.warning(
                "Higgsfield is not signed in — run `higgsfield auth login` on this "
                "machine. Generation will fall back to CometAPI."
            )
        return self._authenticated

    @property
    def last_auth_error(self) -> str:
        """Why availability failed, for a caller that wants to report it."""
        return getattr(self, "_auth_error", "") or ""

    async def available(self) -> bool:
        """Enabled by settings, installed, and signed in."""
        if not settings.HIGGSFIELD_ENABLED:
            return False
        if not self.binary():
            return False
        return await self.is_authenticated()

    # -- response parsing --------------------------------------------------

    @staticmethod
    def parse_json(stdout: str) -> Optional[Any]:
        """
        Pull the JSON document out of --json output.

        The CLI may print progress lines before the payload while --wait polls, so
        parsing the whole buffer is not enough — fall back to the last line, then to
        the outermost braces.
        """
        text = stdout.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        for line in reversed(text.splitlines()):
            line = line.strip()
            if line.startswith(("{", "[")):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue

        start = min((text.find(c) for c in "{[" if text.find(c) >= 0), default=-1)
        end = max(text.rfind("}"), text.rfind("]"))
        if 0 <= start < end:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                return None
        return None

    @classmethod
    def extract_url(cls, payload: Any, want: str = "") -> Optional[str]:
        """
        Find the finished asset's URL anywhere in the response.

        Deliberately tolerant: the CLI's schema is undocumented, and a generator that
        worked yesterday must not stop working because a key was renamed one level
        deeper. `want` ("image"/"video") biases the choice when several URLs appear.
        """
        found: List[str] = []

        def walk(node: Any) -> None:
            if isinstance(node, str):
                if node.startswith(("http://", "https://")):
                    found.append(node)
                return
            if isinstance(node, list):
                for item in node:
                    walk(item)
                return
            if isinstance(node, dict):
                for key in URL_KEYS:
                    value = node.get(key)
                    if isinstance(value, str) and value.startswith("http"):
                        found.append(value)
                for key in NESTED_KEYS:
                    if key in node:
                        walk(node[key])
                for key, value in node.items():
                    if key not in URL_KEYS and key not in NESTED_KEYS:
                        walk(value)

        walk(payload)
        if not found:
            return None

        if want:
            suffixes = (".mp4", ".mov", ".webm") if want == "video" else (".png", ".jpg", ".jpeg", ".webp")
            preferred = [u for u in found if u.lower().split("?")[0].endswith(suffixes)]
            if preferred:
                return preferred[0]
        return found[0]

    # -- generation --------------------------------------------------------

    async def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        reference_paths: Optional[List[str]] = None,
        aspect_ratio: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a still. Passing reference_paths anchors it to those pictures, which
        is what keeps a character consistent from scene to scene.
        """
        refs = [p for p in (reference_paths or []) if Path(p).is_file()]
        chosen = model or (
            settings.HIGGSFIELD_REFERENCE_IMAGE_MODEL if refs else settings.HIGGSFIELD_IMAGE_MODEL
        )

        args = ["generate", "create", chosen, "--prompt", prompt, "--json", "--wait",
                "--wait-timeout", settings.HIGGSFIELD_WAIT_TIMEOUT]
        if aspect_ratio:
            args += ["--aspect_ratio", aspect_ratio]

        paths = [str(Path(r).resolve()) for r in refs[:settings.HIGGSFIELD_MAX_REFERENCES]]
        result = await self._run_with_media_flag(
            chosen, args, paths, IMAGE_REFERENCE_FLAGS,
            timeout=settings.HIGGSFIELD_TIMEOUT_SECONDS,
        )
        if "error" in result:
            return result

        payload = self.parse_json(result["stdout"])
        url = self.extract_url(payload, want="image")
        if not url:
            logger.error(f"Higgsfield image reply had no URL: {result['stdout'][:400]}")
            return {"error": f"no image URL in Higgsfield reply: {result['stdout'][:200]}"}

        return {
            "url": url,
            "model": chosen,
            "service": "higgsfield",
            "ref_count": len(refs),
            "character_consistent": bool(refs),
        }

    async def animate_image(
        self,
        image_path: str,
        prompt: str = "",
        model: Optional[str] = None,
        duration: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Animate a still. image_path is a local file — the CLI uploads it for us, so
        there is no pre-signed URL to expire between generation and animation.
        """
        chosen = model or settings.HIGGSFIELD_VIDEO_MODEL
        source = Path(image_path)
        if not source.is_file():
            return {"error": f"start image not found: {image_path}"}

        args = ["generate", "create", chosen, "--json", "--wait",
                "--wait-timeout", settings.HIGGSFIELD_WAIT_TIMEOUT]
        if prompt:
            args += ["--prompt", prompt]
        if duration:
            args += ["--duration", str(duration)]

        result = await self._run_with_media_flag(
            chosen, args, [str(source.resolve())], START_IMAGE_FLAGS,
            timeout=settings.HIGGSFIELD_TIMEOUT_SECONDS,
        )
        if "error" in result:
            return result

        payload = self.parse_json(result["stdout"])
        url = self.extract_url(payload, want="video")
        if not url:
            logger.error(f"Higgsfield video reply had no URL: {result['stdout'][:400]}")
            return {"error": f"no video URL in Higgsfield reply: {result['stdout'][:200]}"}

        return {"url": url, "model": chosen, "service": "higgsfield"}

    async def list_models(self, kind: str = "video") -> Dict[str, Any]:
        """Model ids this account can reach. Used by live_check to check settings."""
        result = await self._run(["model", "list", f"--{kind}", "--json"], timeout=60)
        if "error" in result:
            return result
        payload = self.parse_json(result["stdout"])
        if not isinstance(payload, list):
            return {"error": f"unexpected model list shape: {str(payload)[:200]}"}
        return {"models": [m.get("job_set_type") for m in payload if isinstance(m, dict)]}

    async def describe_model(self, model: str) -> Dict[str, Any]:
        """`higgsfield model get <model>` — the definitive parameter list for a model."""
        result = await self._run(["model", "get", model, "--json"], timeout=60)
        if "error" in result:
            return result
        return {"raw": result["stdout"][:2000], "parsed": self.parse_json(result["stdout"])}


higgsfield_service = HiggsfieldService()
