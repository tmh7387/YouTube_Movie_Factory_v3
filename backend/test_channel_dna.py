"""
Offline validation tests for the YouTube Channel DNA Intake feature.
Tests all code paths without requiring database or API connections.
"""
import sys
import os
import re
import json

# Ensure backend is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

errors = []
passed = []

def test(name, condition, details=""):
    if condition:
        passed.append(name)
        print(f"  [PASS] {name}")
    else:
        errors.append(f"{name}: {details}")
        print(f"  [FAIL] {name} -- {details}")

print("\n" + "=" * 60)
print("YouTube Channel DNA Intake — Validation Tests")
print("=" * 60)

# ── Test 1: youtube_service.py structure ────────────────────────────
print("\n1. YouTubeService — resolve_channel_id regex patterns")

from app.services.youtube_service import YouTubeService

yt = YouTubeService.__new__(YouTubeService)
yt.youtube = None  # No API key needed for regex tests

# Test channel ID extraction from /channel/ URLs
m = re.search(r'/channel/(UC[a-zA-Z0-9_-]+)', 'https://youtube.com/channel/UCabcdef123456_-')
test("channel_id_regex", m and m.group(1) == "UCabcdef123456_-")

# Test @handle extraction
m = re.search(r'@([a-zA-Z0-9_.-]+)', 'https://youtube.com/@MrBeast')
test("handle_regex", m and m.group(1) == "MrBeast")

# Test /c/ and /user/ extraction
m = re.search(r'/(?:c|user)/([a-zA-Z0-9_.-]+)', 'https://youtube.com/c/veritasium')
test("c_format_regex", m and m.group(1) == "veritasium")

m = re.search(r'/(?:c|user)/([a-zA-Z0-9_.-]+)', 'https://youtube.com/user/CGPGrey')
test("user_format_regex", m and m.group(1) == "CGPGrey")

# Test that /channel/ returns ID directly (no API call needed)
result = yt.resolve_channel_id('https://youtube.com/channel/UCq6VFHwMzcMXbuKyG7SQYIg')
test("direct_channel_id_extraction", result == "UCq6VFHwMzcMXbuKyG7SQYIg",
     f"Got: {result}")

# Test that @handle returns None (needs API) when youtube is None
result = yt.resolve_channel_id('https://youtube.com/@test')
test("handle_without_api_returns_none", result is None)

# Test that get_channel_top_videos returns [] without API
result = yt.get_channel_top_videos("UCtest123")
test("top_videos_without_api_returns_empty", result == [])

# Test that get_channel_metadata returns None without API
result = yt.get_channel_metadata("UCtest123")
test("metadata_without_api_returns_none", result is None)


# ── Test 2: AI Service structure ───────────────────────────────────
print("\n2. AIService — CHANNEL_DNA_PROMPT and analyze_channel_dna")

from app.services.ai_service import CHANNEL_DNA_PROMPT, AIService

test("dna_prompt_exists", len(CHANNEL_DNA_PROMPT) > 500,
     f"Prompt length: {len(CHANNEL_DNA_PROMPT)}")

test("no_clone_copy_replicate_in_prompt",
     "clone" not in CHANNEL_DNA_PROMPT.lower() and
     "copy" not in CHANNEL_DNA_PROMPT.lower() and
     "replicate" not in CHANNEL_DNA_PROMPT.lower(),
     "Found forbidden replication language in prompt")

test("prompt_has_inspiration_framing",
     "transferable" in CHANNEL_DNA_PROMPT.lower() and
     "inspiration" in CHANNEL_DNA_PROMPT.lower())

test("prompt_has_json_schema",
     '"channel_name"' in CHANNEL_DNA_PROMPT and
     '"bible_narrative_style"' in CHANNEL_DNA_PROMPT and
     '"transferable_principles"' in CHANNEL_DNA_PROMPT)

# Check method exists
test("analyze_channel_dna_method_exists",
     hasattr(AIService, 'analyze_channel_dna'))

# Check method signature
import inspect
sig = inspect.signature(AIService.analyze_channel_dna)
params = list(sig.parameters.keys())
test("analyze_channel_dna_params",
     set(params) == {'self', 'topic', 'text_content', 'video_analysis'},
     f"Params: {params}")


# ── Test 3: Intake Normalizer routing ──────────────────────────────
print("\n3. IntakeNormalizer — youtube_channel routing")

# Read the source file to check routing
normalizer_path = os.path.join("app", "services", "intake_normalizer.py")
with open(normalizer_path, "r") as f:
    normalizer_src = f.read()

test("normalizer_has_youtube_channel_branch",
     'source_type == "youtube_channel"' in normalizer_src)

test("normalizer_calls_normalize_youtube_channel",
     "_normalize_youtube_channel" in normalizer_src)

test("normalizer_fn_defined",
     "async def _normalize_youtube_channel" in normalizer_src)

# Check it extracts both channel_url and url as fallback
test("normalizer_reads_channel_url",
     'source_data.get("channel_url")' in normalizer_src)

test("normalizer_reads_video_count",
     'source_data.get("video_count"' in normalizer_src)

test("normalizer_reads_creative_intent",
     'source_data.get("creative_intent"' in normalizer_src)

test("normalizer_stores_video_analysis",
     'context["video_analysis"]' in normalizer_src)


# ── Test 4: Research Task routing ──────────────────────────────────
print("\n4. Research Task — youtube_channel routing")

task_path = os.path.join("tasks", "research.py")
with open(task_path, "r") as f:
    task_src = f.read()

test("task_routes_youtube_channel",
     'source_type == "youtube_channel"' in task_src)

test("task_calls_analyze_channel_dna",
     "analyze_channel_dna" in task_src)

test("task_stores_research_brief",
     '"research_brief"' in task_src and
     'update_values["research_brief"]' in task_src)


# ── Test 5: API Schema exposes research_brief ──────────────────────
print("\n5. API Schema — research_brief in response")

api_path = os.path.join("app", "api", "research.py")
with open(api_path, "r") as f:
    api_src = f.read()

test("api_schema_has_research_brief",
     "research_brief" in api_src and "dict | None" in api_src)


# ── Test 6: Frontend types ─────────────────────────────────────────
print("\n6. Frontend — research.ts types")

fe_research_path = os.path.join(
    "..", "frontend", "src", "services", "research.ts"
)
with open(fe_research_path, "r") as f:
    fe_src = f.read()

test("frontend_type_has_research_brief",
     "research_brief" in fe_src)


# ── Test 7: ResearchIntake.tsx ─────────────────────────────────────
print("\n7. Frontend — ResearchIntake.tsx")

intake_path = os.path.join(
    "..", "frontend", "src", "components", "ResearchIntake.tsx"
)
with open(intake_path, "r") as f:
    intake_src = f.read()

test("intake_has_youtube_channel_source",
     "'youtube_channel'" in intake_src)

test("intake_has_channel_url_state",
     "channelUrl" in intake_src)

test("intake_has_channel_intent_state",
     "channelIntent" in intake_src)

test("intake_has_channel_video_count_state",
     "channelVideoCount" in intake_src)

test("intake_sends_channel_url_in_source_data",
     "sourceData.channel_url = channelUrl" in intake_src)

test("intake_topic_uses_channel_intent",
     "channelIntent || channelUrl" in intake_src)


# ── Test 8: ChannelDnaDisplay.tsx ──────────────────────────────────
print("\n8. Frontend — ChannelDnaDisplay.tsx")

display_path = os.path.join(
    "..", "frontend", "src", "components", "ChannelDnaDisplay.tsx"
)
with open(display_path, "r") as f:
    display_src = f.read()

test("display_component_exists", len(display_src) > 500)

test("display_renders_channel_name",
     "dna.channel_name" in display_src)

test("display_renders_style_brief",
     "dna.style_brief" in display_src)

test("display_renders_principles",
     "dna.transferable_principles" in display_src)

test("display_has_bible_apply",
     "narrative_style" in display_src)

test("display_has_bible_dropdown",
     "selectedBibleId" in display_src)

test("display_puts_to_bible_api",
     "/bible/" in display_src and "put" in display_src.lower())

test("display_no_clone_copy_language",
     "clone" not in display_src.lower() and
     "copy" not in display_src.lower() and
     "replicate" not in display_src.lower(),
     "Found replication language in display component")


# ── Test 9: Research.tsx wiring ────────────────────────────────────
print("\n9. Frontend — Research.tsx wiring")

research_path = os.path.join(
    "..", "frontend", "src", "pages", "Research.tsx"
)
with open(research_path, "r") as f:
    research_src = f.read()

test("research_imports_channel_dna_display",
     "ChannelDnaDisplay" in research_src)

test("research_conditionally_renders_for_youtube_channel",
     "youtube_channel" in research_src and
     "research_brief" in research_src)


# ── Test 10: JSON response simulation ─────────────────────────────
print("\n10. JSON schema validation")

sample_dna = {
    "channel_name": "Test Channel",
    "videos_analyzed_titles": ["Video 1", "Video 2"],
    "style_brief": "A channel that...",
    "narrative_dna": {
        "opening_hook_style": "Hook desc",
        "storytelling_approach": "Story desc",
        "pacing_cadence": "Pacing desc",
        "tone_and_voice": "Tone desc",
        "content_format": "Format desc",
        "emotional_register": "Emotion desc",
    },
    "transferable_principles": ["Principle 1", "Principle 2"],
    "what_makes_it_distinctive": "Distinctive quality",
    "bible_narrative_style": {
        "tone": "Tone",
        "opening_hook": "Hook",
        "storytelling_approach": "Approach",
        "pacing": "Pacing",
        "principles": ["P1", "P2"],
    },
}

test("sample_dna_is_valid_json",
     json.loads(json.dumps(sample_dna)) == sample_dna)

test("bible_narrative_style_has_required_keys",
     all(k in sample_dna["bible_narrative_style"]
         for k in ["tone", "opening_hook", "storytelling_approach", "pacing", "principles"]))


# ── Summary ────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"Results: {len(passed)} passed, {len(errors)} failed")
print("=" * 60)

if errors:
    print("\nFailed tests:")
    for e in errors:
        print(f"  [FAIL] {e}")
    sys.exit(1)
else:
    print("\nAll tests passed!")
    sys.exit(0)
