# Skill build audit — read this before applying any rollout

**Status: the Seedance 2.5 rollout is blocked.** Not because the findings are
wrong, but because there is no agreed base to apply them to.

This document records what is actually on the workstation, what each copy
uniquely holds, what is missing, and what has to happen before any skill is
edited again.

Audit run 2026-08-22 across `D:\App development`, `C:\Users\Admin\Documents\Claude`
and `C:\Users\Admin\.claude\skills`.

---

## 1. The headline

`seedance2-director` exists in **six copies. All six are different builds.** No two
are byte-identical, and no copy is marked as authoritative.

| Build | Lines | Date | Location |
|---|---|---|---|
| **A** | 697 | 2026-07-15 | `Content_Intelligence\skills-output\2026-07-15-cinema-studio-upgrade\seedance2-director\seedance2-director.skill` |
| **B** | 660 | 2026-05-07 | `Content_Intelligence\skills-output\seedance2-director--SKILL.md` |
| **C** | 624 | 2026-05-07 | `Content_Intelligence\seedance2-director.skill` |
| **D** | 615 | 2026-08-22 | `YouTube_Movie_Factory_v3\skills\general\seedance2-director-v2\SKILL (1).md` |
| **E** | 557 | 2026-04-30 | `Claude_Movie\claude-movie-director\skills\seedance2-director\SKILL.md` |
| **live** | ? | ? | claude.ai account — **not readable from this machine** |

A sixth on-disk copy exists at `YouTube_Movie_Factory_v3\.agent\skills\seedance2-director\SKILL.md`;
it is build D plus three frontmatter lines.

## 2. Two builds each own content the other does not have

This is the part that matters. A and B are not versions of each other. They are
divergent forks, and **nobody has ever merged them.**

**Build A alone holds four craft rules** — added by the 2026-07-15 cinema studio
upgrade:

- 180-degree line lock
- Match cut via last-frame attach
- Embedded multi-shot hard cuts (timestamped sub-shots)
- Whip pan discipline

**Build B alone holds the entire integration layer:**

- Upstream / downstream skill map
- Higgsfield MCP execution
- Executing a generated prompt via MCP
- Credit check before execution
- Post-generation handling

Build B also **lacks** `DURATION CALIBRATION` and `CREATIVE PRINCIPLES`, which A,
C, D and E all have.

Builds C and E hold nothing unique. They are subsets.

## 3. The build I edited was the wrong one

On 2026-08-22 I added the model-selection gate and the derived-duration rule to
**build D**. D descends from the E/C line. It is missing:

| Missing from D | Held by |
|---|---|
| Mode C — storyboard-driven, 3-image shot-block format | A, B, C |
| 180-degree line lock | A |
| Match cut via last-frame attach | A |
| Embedded multi-shot hard cuts | A |
| Whip pan discipline | A |
| Upstream / downstream skill map | B |
| Higgsfield MCP execution (4 sections) | B |

So the `STEP 0.5` work is correct in substance but sits on a dead branch.
Uploading D would silently delete Mode C, four craft rules and the whole
Higgsfield execution path.

**That edit should be re-applied to the consolidated build, not shipped as-is.**

## 4. The rollout spec describes sections absent from every LOCAL build

> **Corrected 2026-08-22.** This section originally concluded that the rollout
> spec might have described sections that were never read. That was wrong, and
> the error was mine: I searched local copies only. The live skill was exported
> from claude.ai shortly afterwards and **all four sections are in it**. The
> drafting session read the live skill correctly. The corrected finding follows.

`README.md` in this folder — and the handover prompt built from it — instruct an
editor to change four specific things in `seedance2-director`:

| Named in the rollout spec | Across the 6 local builds | In the live 2026-07-24 build |
|---|---|---|
| `PLATFORM CONSTRAINTS` table | **0** | **line 420** |
| `OUTPUT SETTINGS` section | **0** | **line 408** |
| `PROMPT DISCIPLINE RULES` | **0** | **line 438** |
| "zero memory" / self-contained rule | **0** | **line 444** (Rule 1) |

The live build carries the constraint row verbatim:

> **Max duration** — **15 seconds** — Seedance 2.0 supports 4-15s. Do NOT default
> to 10s. If a segment is 11s, 12s, 13s, 14s, or 15s, use that exact value.

So the rollout's central factual claim is **confirmed, not unverified**. What the
audit actually establishes is narrower and still useful: the live build is a
seventh distinct build that matches no local copy, which is why instructions
written against it fail when pointed at anything on this workstation.

The 15-second figure also appears in every local build as a dialogue word budget
("~25-30 spoken words fit into 15 seconds"), which is a separate instance of the
same problem and is tracked in the branch review.

## 5. Two target skills have no local copy at all

- **`seedance2-composition`** — zero copies found. The 2026-07-15 upgrade README
  confirms it: *"weren't in this project folder as editable .skill files, so no
  changes were made."*
- **`ai-music-video-director`** — zero copies found.

Priority 2 of the rollout targets `seedance2-composition`. There is nothing here
to apply it to.

## 6. The same fragmentation affects every other target skill

| Skill | Copies | Distinct builds | Notes |
|---|---|---|---|
| `seedance2-director` | 6 | **6** | see above |
| `credit-calculator` | 4 | 3 | 170 / 181 / 186 lines |
| `storyboard-generator` | 4 | 3 | 264 / 314 / 465 lines |
| `video-production-planner` | 4 | 3 | 264 / 438 / 503 lines |
| `higgsfield-generate` | 2 | 2 | 233 / 245 lines, both v0.3.0 |
| `audio-driven-lip-sync` | 3 | 2 | 42 / 46 lines |
| `seedance2-composition` | 0 | 0 | account only |
| `ai-music-video-director` | 0 | 0 | account only |

`storyboard-generator` shows the same A/B split as the director: the 465-line
build holds the Higgsfield MCP and upstream/downstream sections; the 314-line
July build holds the newer craft work. Neither contains the other.

## 7. Root cause

Every skill upgrade session on this machine has followed the same pattern:

1. Read whatever `.skill` package happened to be in the folder it was pointed at.
2. Write an improved build next to it.
3. End with "these are not yet live — upload them manually via Settings."

Nothing records which package was uploaded, or when, or from which source. So:

- each session forks from a different ancestor,
- forks are never merged back,
- the live copy drifts out of reach of every local copy,
- and the next session forks again from whichever file it found first.

Six builds is the arithmetic result of four upgrade sessions and no merge step.

## 8. What has to happen, in order

**Do not apply the Seedance 2.5 rollout yet.** Applying it now would fork a
seventh build.

### Step 1 — Establish ground truth (blocked on you)

Export the live `seedance2-director` from the claude.ai account and put it on
disk. Same for `seedance2-composition` and `ai-music-video-director`, which have
no local copy at all.

Nothing else can be decided without this. Until the live build is readable, every
instruction of the form "the skill has X" is a guess.

### Step 2 — Reconcile against the live build

With the live copy in hand, answer:

- Which of A-E is it closest to? Is it a seventh build?
- Was the 2026-07-15 cinema studio upgrade ever uploaded? Its four craft rules
  tell you — if they are absent from live, it was not.
- Do the Platform Constraints / OUTPUT SETTINGS / Prompt Discipline sections
  exist there? If not, the rollout spec needs rewriting against reality.

### Step 3 — Consolidate to one canonical build

Merge, do not pick. The merge target must carry:

- everything the live build has (it is what actually runs),
- A's four craft rules,
- B's integration layer,
- `DURATION CALIBRATION` and `CREATIVE PRINCIPLES`,
- Mode C.

Publish that as the single source of truth, in one location, under version
control. Every other copy becomes read-only history.

### Step 4 — Re-apply the STEP 0.5 work on top

The model-selection gate and derived-duration rule from build D are sound. Port
them onto the consolidated build rather than shipping D.

### Step 5 — Then, and only then, apply the 2.5 rollout

Against a known base, with the spec corrected per Step 2.

### Step 6 — Retire the obsolete copies

Once the canonical build is live and verified, delete or archive the rest so the
next session cannot fork from a stale ancestor. **Confirm before deleting
anything** — some of these folders may be deliberate history.

## 9. Open questions for you

1. Can you export a skill from claude.ai to a file? If not, pasting the live
   `SKILL.md` into a file here is enough.
2. Was the 2026-07-15 cinema studio upgrade ever uploaded? If you remember, it
   saves a comparison.
3. Where should the canonical copy live — this repo, or the Content_Intelligence
   vault? Both currently hold copies, which is part of the problem.
4. Are `Claude_Movie\claude-movie-director\skills\` and
   `Content_Intelligence\skills-output\` meant to be archives, or live sources?
