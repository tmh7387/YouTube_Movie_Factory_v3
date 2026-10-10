"""Shot spec — the pipeline's central data contract.

A *prompt* is prose and drifts. A *spec* is data and does not. This module defines the
shot-spec document, validates it hard enough that a malformed spec fails before Blender
starts, and derives every quantity the blockout builder and prompt writer need.

The schema is documented in full in `00-overview/PIPELINE_ARCHITECTURE.md` §4.1. This module
is the executable definition; if the two disagree, this one wins (and the doc gets fixed).

Deliberately stdlib-only: it is imported both by host-side tooling (Python 3.12) and inside
Blender's bundled interpreter (Python 3.13). No third-party imports, ever.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

# --------------------------------------------------------------------------------------
# Pipeline-wide constants
#
# These are conventions, not physics. They exist so that blockouts read consistently and so
# that a reviewer can spot an anomaly at a glance. Change them in one place, deliberately.
# --------------------------------------------------------------------------------------

#: Colour-coded cast proxies (linear RGBA).
#:
#: Tuned for *readability on a mid-grey ambient background*, not for beauty. Two rules
#: learned the hard way: keep every role light enough to separate from a mid-grey world,
#: and keep the roles apart in LUMINANCE as well as hue, so a blockout is still readable to
#: someone who cannot distinguish the hues (and to a vision model reading a compressed
#: frame). See CAMERA_MOVE_CATALOGUE.md §3 for the role definitions.
ROLE_COLOURS: dict[str, tuple[float, float, float, float]] = {
    "lead": (0.90, 0.13, 0.13, 1.0),       # red    — hero
    "support": (0.15, 0.38, 0.95, 1.0),    # blue   — supporting cast
    "crowd": (0.62, 0.62, 0.65, 1.0),      # light grey — extras
    "prop": (0.20, 0.80, 0.45, 1.0),       # green  — meaningful props
    "camera": (0.98, 0.85, 0.15, 1.0),     # yellow — camera path / targets
    # Set volumes are deliberately DARK. A mid-grey room surround sits at almost the same
    # chroma as the light-grey "crowd" role, so a blockout shot inside a mid-grey room turns
    # into a field of indistinguishable grey and stops being colour-coded at all. Dark walls,
    # bright figures: the surround can never be mistaken for a performer.
    "set": (0.20, 0.21, 0.24, 1.0),        # dark slate — set volumes, walls, floors
}

#: Default proxy geometry per cast kind.
PROXY_KINDS = ("capsule", "box", "sphere", "cone")

DEFAULT_ASPECTS: dict[str, tuple[int, int]] = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "4:3": (1440, 1080),
    "3:4": (1080, 1440),
    "21:9": (2560, 1080),
}

#: The exclusion clause that MUST reach every downstream prompt. Written once, here, because
#: its absence is the known cause of models trying to preserve the blockout's grey look.
EXCLUDE_FROM_REALISATION = (
    "grey proxy materials",
    "proxy geometry proportions beyond the camera-path intent",
    "previz lighting",
)


class SpecError(ValueError):
    """Raised when a shot spec is structurally or numerically invalid."""


# --------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------


def _vec3(value: Any, where: str) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise SpecError(f"{where}: expected [x, y, z], got {value!r}")
    try:
        return (float(value[0]), float(value[1]), float(value[2]))
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise SpecError(f"{where}: non-numeric component in {value!r}") from exc


def _require(mapping: dict[str, Any], key: str, where: str) -> Any:
    if key not in mapping:
        raise SpecError(f"{where}: missing required field '{key}'")
    return mapping[key]


# --------------------------------------------------------------------------------------
# Sub-documents
# --------------------------------------------------------------------------------------


@dataclass
class Volume:
    """A set volume — a box of space the camera and cast must live inside."""

    id: str
    min: tuple[float, float, float]
    max: tuple[float, float, float]
    role: str = "primary"

    @property
    def size(self) -> tuple[float, float, float]:
        return tuple(self.max[i] - self.min[i] for i in range(3))  # type: ignore[return-value]

    @property
    def centre(self) -> tuple[float, float, float]:
        return tuple((self.max[i] + self.min[i]) / 2.0 for i in range(3))  # type: ignore[return-value]

    def contains(self, point: tuple[float, float, float], margin: float = 0.0) -> bool:
        return all(
            self.min[i] - margin <= point[i] <= self.max[i] + margin for i in range(3)
        )

    @classmethod
    def from_dict(cls, d: dict[str, Any], where: str) -> "Volume":
        return cls(
            id=str(_require(d, "id", where)),
            min=_vec3(_require(d, "min", where), f"{where}.min"),
            max=_vec3(_require(d, "max", where), f"{where}.max"),
            role=str(d.get("role", "primary")),
        )


@dataclass
class CastMember:
    """A colour-coded proxy standing in for a performer or prop."""

    id: str
    role: str = "support"
    proxy: str = "box"
    start: tuple[float, float, float] = (0.0, 0.0, 0.0)
    end: tuple[float, float, float] | None = None
    height_m: float = 1.75
    radius_m: float = 0.30
    motion: str = ""
    facing_deg: float = 0.0

    @property
    def colour(self) -> tuple[float, float, float, float]:
        return ROLE_COLOURS.get(self.role, ROLE_COLOURS["crowd"])

    @classmethod
    def from_dict(cls, d: dict[str, Any], where: str) -> "CastMember":
        proxy = str(d.get("proxy", "box"))
        if proxy not in PROXY_KINDS:
            raise SpecError(f"{where}.proxy: '{proxy}' not in {PROXY_KINDS}")
        end = d.get("end")
        return cls(
            id=str(_require(d, "id", where)),
            role=str(d.get("role", "support")),
            proxy=proxy,
            start=_vec3(d.get("start", [0, 0, 0]), f"{where}.start"),
            end=_vec3(end, f"{where}.end") if end is not None else None,
            height_m=float(d.get("height_m", 1.75)),
            radius_m=float(d.get("radius_m", 0.30)),
            motion=str(d.get("motion", "")),
            facing_deg=float(d.get("facing_deg", 0.0)),
        )


@dataclass
class CameraKey:
    """One point on the camera path. `target` is what makes framing survive the move."""

    t: float
    pos: tuple[float, float, float]
    target: tuple[float, float, float]
    note: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any], where: str) -> "CameraKey":
        return cls(
            t=float(_require(d, "t", where)),
            pos=_vec3(_require(d, "pos", where), f"{where}.pos"),
            target=_vec3(_require(d, "target", where), f"{where}.target"),
            note=str(d.get("note", "")),
        )


@dataclass
class Beat:
    """A timeline marker: what must be true, and when."""

    t: float
    label: str
    action: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any], where: str) -> "Beat":
        return cls(
            t=float(_require(d, "t", where)),
            label=str(_require(d, "label", where)),
            action=str(d.get("action", "")),
        )


# --------------------------------------------------------------------------------------
# The spec
# --------------------------------------------------------------------------------------


@dataclass
class ShotSpec:
    shot_id: str
    project: str
    duration_s: float
    fps: int = 24
    aspect: str = "16:9"
    resolution: tuple[int, int] | None = None
    version: int = 1

    intent: str = ""
    format_mode: str = "ONE SINGLE UNBROKEN SHOT"
    audio: dict[str, Any] = field(default_factory=dict)

    optic: dict[str, Any] = field(default_factory=dict)
    camera: dict[str, Any] = field(default_factory=dict)
    set: dict[str, Any] = field(default_factory=dict)

    volumes: list[Volume] = field(default_factory=list)
    cast: list[CastMember] = field(default_factory=list)
    camera_path: list[CameraKey] = field(default_factory=list)
    beats: list[Beat] = field(default_factory=list)

    exclude_from_realisation: list[str] = field(
        default_factory=lambda: list(EXCLUDE_FROM_REALISATION)
    )
    source_path: Path | None = None

    # -- validation ---------------------------------------------------------------

    def validate(self) -> list[str]:
        """Return a list of problems. Empty list means the spec may be built.

        Hard errors raise via SpecError during parsing; this method reports the
        *semantic* problems that parsing cannot see — a camera that starts outside its
        own set, a beat past the end of the shot, a loop whose ends do not match.
        """
        problems: list[str] = []

        if self.duration_s <= 0:
            problems.append("duration_s must be > 0")
        if self.fps <= 0:
            problems.append("fps must be > 0")
        if self.aspect not in DEFAULT_ASPECTS and self.resolution is None:
            problems.append(
                f"aspect '{self.aspect}' unknown and no explicit resolution given"
            )
        if not self.camera_path:
            problems.append("camera.path is empty — a shot needs at least a start and an end")
        if len(self.camera_path) >= 2:
            if self.camera_path[0].t != 0.0:
                problems.append(
                    f"camera.path first key t={self.camera_path[0].t} — must be 0.0"
                )
            if abs(self.camera_path[-1].t - self.duration_s) > 1e-6:
                problems.append(
                    f"camera.path last key t={self.camera_path[-1].t} — must equal "
                    f"duration_s ({self.duration_s})"
                )
        for key in self.camera_path:
            if not (0.0 <= key.t <= self.duration_s):
                problems.append(f"camera key t={key.t} outside 0..{self.duration_s}")
        for beat in self.beats:
            if not (0.0 <= beat.t <= self.duration_s):
                problems.append(
                    f"beat '{beat.label}' t={beat.t} outside 0..{self.duration_s}"
                )
        if not self.volumes:
            problems.append("set.volumes is empty — the camera has no room to be in")

        # Camera must start inside the union of the volumes.
        if self.volumes and self.camera_path:
            start = self.camera_path[0].pos
            if not any(v.contains(start, margin=0.5) for v in self.volumes):
                problems.append(
                    f"camera start {start} is not inside any set volume "
                    "(+0.5 m tolerance) — check units"
                )

        # Beats should be strictly increasing in time.
        times = [b.t for b in self.beats]
        if times != sorted(times):
            problems.append("beats are not in ascending time order")

        # Cast ids must be unique.
        ids = [c.id for c in self.cast]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            problems.append(f"duplicate cast ids: {sorted(dupes)}")

        # Loop integrity — a loop is a claim that the clip can replay without a seam. Two
        # independent things must hold, and only one of them is about the camera.
        if self.is_loop:
            if not any(
                "loop" in (k.note or "").lower() for k in (self.camera_path or [])
            ):
                problems.append(
                    "spec looks like a loop (first and last beats carry 'loop') but no camera "
                    "key is annotated as a loop key"
                )
            # TRAVELLING CAST BREAKS A LOOP. A performer who walks 2 m and never comes back
            # cannot be in the same place in the closing frame as the opening one. This is
            # not a nitpick: it is the most common way an authored loop fails, it is
            # invisible in any single frame, and it can only be caught by comparing the ends.
            # Position must therefore hold across a loop; describe the movement in the prompt
            # instead, where the model can animate it without breaking continuity (P-03).
            for member in self.cast:
                if member.end is None:
                    continue
                travel = math.dist(member.start, member.end)
                if travel > 0.10:
                    problems.append(
                        f"loop integrity: cast '{member.id}' travels {travel:.2f} m across "
                        "the shot but a loop must return it to its opening position. Set "
                        "'end' equal to 'start' and describe the movement in the prompt, or "
                        "mark the shot as not-a-loop."
                    )
        return problems

    # -- derived ------------------------------------------------------------------

    @property
    def total_frames(self) -> int:
        """Frame count for the clip. `duration_s * fps`, rounded to nearest."""
        return int(round(self.duration_s * self.fps))

    @property
    def frame_end(self) -> int:
        """Blender's inclusive end frame (frame_start is 1)."""
        return max(1, self.total_frames)

    @property
    def resolved_resolution(self) -> tuple[int, int]:
        if self.resolution:
            return self.resolution
        return DEFAULT_ASPECTS.get(self.aspect, (1920, 1080))

    @property
    def aspect_ratio(self) -> float:
        w, h = self.resolved_resolution
        return w / h

    @property
    def is_loop(self) -> bool:
        if len(self.beats) < 2:
            return False
        first, last = self.beats[0], self.beats[-1]
        return (
            "loop" in first.label.lower() or "loop" in last.label.lower()
        ) and abs(first.t) < 1e-6 and abs(last.t - self.duration_s) < 1e-6

    @property
    def fov_diagonal_deg(self) -> float:
        """Diagonal FOV. 47° is the house default (see CAMERA_MOVE_CATALOGUE.md §3)."""
        return float(self.optic.get("fov_diagonal_deg", 47.0))

    @property
    def rig(self) -> str:
        return str(self.camera.get("rig", "locked"))

    @property
    def constraints(self) -> list[str]:
        return [str(c) for c in self.camera.get("constraints", [])]

    @property
    def volumes_by_id(self) -> dict[str, Volume]:
        return {v.id: v for v in self.volumes}

    def frame_for_time(self, t: float) -> int:
        """Convert a second offset to a Blender frame number (1-based)."""
        return max(1, min(self.frame_end, int(round(t * self.fps)) + 1))

    def check_camera_clearance(
        self, samples_per_second: int = 8, margin: float = 0.05
    ) -> list[str]:
        """Sample the interpolated path and report points outside every set volume.

        This is a cheap approximation of collision detection: it answers "did the camera
        ever leave the room", which is the failure that ruins a take. Precise ray-cast
        collision is Blender's job (see blockout_report.json).
        """
        issues: list[str] = []
        if len(self.camera_path) < 2 or not self.volumes:
            return issues
        n = max(2, int(self.duration_s * samples_per_second))
        for i in range(n + 1):
            t = self.duration_s * i / n
            pos = self.sample_camera_position(t)
            if not any(v.contains(pos, margin=margin) for v in self.volumes):
                issues.append(
                    f"t={t:.2f}s camera at "
                    f"({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}) is outside all volumes"
                )
        return issues

    def sample_camera_position(self, t: float) -> tuple[float, float, float]:
        """Linearly interpolate the camera position at time `t`."""
        keys = self.camera_path
        if not keys:
            return (0.0, 0.0, 0.0)
        if t <= keys[0].t:
            return keys[0].pos
        if t >= keys[-1].t:
            return keys[-1].pos
        for a, b in zip(keys, keys[1:]):
            if a.t <= t <= b.t:
                span = b.t - a.t
                f = 0.0 if span <= 0 else (t - a.t) / span
                return tuple(a.pos[i] + (b.pos[i] - a.pos[i]) * f for i in range(3))  # type: ignore[return-value]
        return keys[-1].pos

    def sample_camera_target(self, t: float) -> tuple[float, float, float]:
        """Linearly interpolate the camera target at time `t`."""
        keys = self.camera_path
        if not keys:
            return (0.0, 0.0, 0.0)
        if t <= keys[0].t:
            return keys[0].target
        if t >= keys[-1].t:
            return keys[-1].target
        for a, b in zip(keys, keys[1:]):
            if a.t <= t <= b.t:
                span = b.t - a.t
                f = 0.0 if span <= 0 else (t - a.t) / span
                return tuple(
                    a.target[i] + (b.target[i] - a.target[i]) * f for i in range(3)
                )  # type: ignore[return-value]
        return keys[-1].target

    # -- I/O ----------------------------------------------------------------------

    @classmethod
    def from_dict(cls, d: dict[str, Any], source: Path | None = None) -> "ShotSpec":
        where = "shot"
        for required in ("shot_id", "duration_s"):
            _require(d, required, where)

        cam_d = dict(d.get("camera", {}) or {})
        path = [
            CameraKey.from_dict(k, f"camera.path[{i}]")
            for i, k in enumerate(cam_d.get("path", []) or [])
        ]
        cam_d["path"] = path

        set_d = dict(d.get("set", {}) or {})
        volumes = [
            Volume.from_dict(v, f"set.volumes[{i}]")
            for i, v in enumerate(set_d.get("volumes", []) or [])
        ]

        res = d.get("resolution")
        spec = cls(
            shot_id=str(d["shot_id"]),
            project=str(d.get("project", "unnamed")),
            duration_s=float(d["duration_s"]),
            fps=int(d.get("fps", 24)),
            aspect=str(d.get("aspect", "16:9")),
            resolution=(int(res[0]), int(res[1])) if res else None,
            version=int(d.get("version", 1)),
            intent=str(d.get("intent", "")),
            format_mode=str(d.get("format_mode", "ONE SINGLE UNBROKEN SHOT")),
            audio=dict(d.get("audio", {}) or {}),
            optic=dict(d.get("optic", {}) or {}),
            camera=cam_d,
            set=set_d,
            volumes=volumes,
            cast=[
                CastMember.from_dict(c, f"cast[{i}]")
                for i, c in enumerate(d.get("cast", []) or [])
            ],
            camera_path=path,
            beats=[
                Beat.from_dict(b, f"beats[{i}]")
                for i, b in enumerate(d.get("beats", []) or [])
            ],
            source_path=source,
        )
        if "exclude_from_realisation" in d:
            spec.exclude_from_realisation = [
                str(x) for x in d["exclude_from_realisation"]
            ]
        return spec

    @classmethod
    def load(cls, path: str | Path) -> "ShotSpec":
        p = Path(path)
        if not p.is_file():
            raise SpecError(f"shot spec not found: {p}")
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SpecError(f"{p}: invalid JSON — {exc}") from exc
        return cls.from_dict(data, source=p)

    def to_dict(self) -> dict[str, Any]:
        return {
            "shot_id": self.shot_id,
            "project": self.project,
            "version": self.version,
            "duration_s": self.duration_s,
            "fps": self.fps,
            "aspect": self.aspect,
            "resolution": list(self.resolved_resolution),
            "intent": self.intent,
            "format_mode": self.format_mode,
            "audio": self.audio,
            "optic": self.optic,
            "camera": {
                **{k: v for k, v in self.camera.items() if k != "path"},
                "path": [
                    {"t": k.t, "pos": list(k.pos), "target": list(k.target), "note": k.note}
                    for k in self.camera_path
                ],
            },
            "set": {
                **{k: v for k, v in self.set.items() if k != "volumes"},
                "volumes": [
                    {
                        "id": v.id,
                        "min": list(v.min),
                        "max": list(v.max),
                        "role": v.role,
                    }
                    for v in self.volumes
                ],
            },
            "cast": [
                {
                    "id": c.id,
                    "role": c.role,
                    "proxy": c.proxy,
                    "start": list(c.start),
                    "end": list(c.end) if c.end else None,
                    "height_m": c.height_m,
                    "radius_m": c.radius_m,
                    "motion": c.motion,
                    "facing_deg": c.facing_deg,
                }
                for c in self.cast
            ],
            "beats": [
                {"t": b.t, "label": b.label, "action": b.action} for b in self.beats
            ],
            "exclude_from_realisation": list(self.exclude_from_realisation),
        }


# --------------------------------------------------------------------------------------
# Convenience
# --------------------------------------------------------------------------------------


def load_and_validate(path: str | Path, strict: bool = True) -> tuple[ShotSpec, list[str]]:
    """Load a spec and return it with its problem list.

    With `strict=True`, clearance warnings are included and any problem raises. Used by the
    CLI so that a bad spec never reaches Blender.
    """
    spec = ShotSpec.load(path)
    problems = spec.validate() + spec.check_camera_clearance()
    if strict and problems:
        raise SpecError(
            f"{path}: spec failed validation with {len(problems)} problem(s):\n  - "
            + "\n  - ".join(problems)
        )
    return spec, problems


def summary_lines(spec: ShotSpec) -> Iterable[str]:
    """Human-readable one-screen summary, used by `--dry-run` output."""
    w, h = spec.resolved_resolution
    yield f"shot          {spec.shot_id}  (project {spec.project}, v{spec.version})"
    yield f"duration      {spec.duration_s}s @ {spec.fps} fps  ->  {spec.total_frames} frames"
    yield f"frame range   {1}..{spec.frame_end}"
    yield f"format        {spec.aspect}  {w}x{h}  ratio {spec.aspect_ratio:.3f}"
    yield f"mode          {spec.format_mode}"
    yield f"rig           {spec.rig}"
    yield f"optic         {spec.fov_diagonal_deg}° diagonal  ({spec.optic.get('character', 'n/a')})"
    yield f"volumes       {len(spec.volumes)}  ({', '.join(v.id for v in spec.volumes) or 'none'})"
    yield f"cast          {len(spec.cast)}  ({', '.join(c.id for c in spec.cast) or 'none'})"
    yield f"camera keys   {len(spec.camera_path)}"
    yield f"beats         {len(spec.beats)}"
    yield f"loop          {'YES' if spec.is_loop else 'no'}"
    if spec.intent:
        yield f"intent        {spec.intent}"


def haversine_like_path_length(spec: ShotSpec, samples: int = 256) -> float:
    """Approximate camera path length in metres — used for speed sanity checks."""
    if len(spec.camera_path) < 2:
        return 0.0
    length = 0.0
    prev = spec.sample_camera_position(0.0)
    for i in range(1, samples + 1):
        t = spec.duration_s * i / samples
        cur = spec.sample_camera_position(t)
        length += math.dist(prev, cur)
        prev = cur
    return length
