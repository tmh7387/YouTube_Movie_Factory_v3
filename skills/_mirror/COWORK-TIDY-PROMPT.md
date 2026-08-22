# Instruction for Claude Cowork — tidy the claude.ai skills

**Run this in Cowork, with the seven `.skill` files from `skills/_mirror/build/`
attached.** Paste everything between the markers.

Cowork's job here is the account side only: upload, inventory, report. It does not
touch the repo — repo changes are made in Claude Code, where the whole tree is
editable.

---

## PROMPT STARTS HERE

My video production skills live in two places and have drifted apart. The repo
side is now sorted. This task is the account side.

**The rule:** the repo is the single source of truth. My claude.ai account is a
mirror of it. Where the two disagree, the repo wins — **except** for skills that
exist only in the account, which are not junk, they are work that never made it
back and which I need identified so I can pull it into the repo.

**Do not delete anything.** Not a skill, not a version, nothing. If something
looks redundant, say so and leave it. I will decide.

---

## Part 1 — Inventory what is actually there

Before uploading anything, list every skill in my account. For each one:

| Field | Why |
|---|---|
| Name | — |
| Description length in characters | The limit is 1024 and I have already hit it once |
| Has reference files? How many? | Several of mine should have references and do not |
| Last modified date | To spot which are stale |

Then group them into three buckets against this list of what the repo now holds:

**Repo skills (22):**

```
general/      audio-driven-lip-sync-video, automated-control-signal-extraction,
              content-intelligence-scraper, controlnet-guided-environment-replacement,
              credit-calculator, directors-sheet, higgsfield-creator,
              minimax-h3-director, multi-shot-camera-coverage,
              multi-shot-storyboard-extraction, music-video-producer, project-bible,
              reference-image-style-anchoring, ripple-edit, seedance2-director-v2,
              storyboard-generator, style-reference-character-transplant,
              video-production-planner, video-scene-deconstructor

music_video/  agent-driven-music-video-workflow,
              global-character-update-single-prompt,
              timestamped-choreography-text-description
```

Buckets:

- **A — in both.** These get replaced by the uploads in Part 2.
- **B — account only.** Report each with its description and roughly what it does.
  These are the ones I need to pull back into the repo. Do not touch them.
- **C — repo only.** Just note them; most are internal pipeline pieces the account
  does not need.

I believe bucket B includes at least: `ai-music-video-director`, `dance-motion`,
`scene-motion`, `lip-sync-music-video`, `seedance2-composition`,
`higgsfield-generate`, `higgsfield-soul-id`, `higgsfield-product-photoshoot`,
`higgsfield-marketplace-cards`, `thumbnail-strategy`, `channel-dna`,
`faceless-channel-builder`, `ingest-channel`, `ingest-content`, `ingest-movie`,
and the three `suno-*` skills. **Verify that against what is actually there
rather than trusting my list** — it came from a session listing, not from the
settings page.

Show me the inventory and the three buckets, then stop. I will confirm before you
upload anything.

---

## Part 2 — Upload the seven replacements

Seven `.skill` packages are attached. Each replaces the account's existing skill
of the same name, except `music-video-producer`, which I think is new.

| Package | Replaces | What changed |
|---|---|---|
| `seedance2-director.skill` | `seedance2-director` | 532 → 915 lines, plus 5 reference files it never had. Covers Seedance 2.0 **and** 2.5, with version routing. |
| `storyboard-generator.skill` | `storyboard-generator` | 339 → 508 lines, plus 3 references. Scene-plate-first, image-model split, cost gate. |
| `video-production-planner.skill` | `video-production-planner` | 534 → 572. Picks the Seedance version in the brief. |
| `directors-sheet.skill` | `directors-sheet` | 266 → 283. Records target version and per-shot runtime. |
| `credit-calculator.skill` | `credit-calculator` | 185 → 261. Seedance 2.5 pricing. |
| `higgsfield-creator.skill` | `higgsfield-creator` | Content unchanged — repackaged so its 3 references travel with it. |
| `music-video-producer.skill` | *(probably new)* | Unchanged content, first time in the account. |

**Before each upload**, tell me:

- the current description of the skill you are about to replace, and
- whether that description contains any trigger phrase the new one lacks.

That second check matters more than it sounds. A trigger phrase that exists only
in the account version disappears the moment you overwrite it, and the skill
silently stops firing on that phrase. It has already happened once: `storyboard
mode` and `bridge to video` existed only in the account's `seedance2-director`
and were nearly lost. **If you find any trigger in an account description that is
missing from the replacement, stop and tell me. Do not upload that one.**

Upload one at a time. Confirm each landed before starting the next.

---

## Part 3 — Flag the overlaps

Some account skills look like they cover the same ground as each other, or as a
repo skill under a different name. Tell me which of these are real duplicates and
which are genuinely different jobs. **Report only — change nothing.**

Pairs I already suspect:

| Account | Possibly overlaps | Question |
|---|---|---|
| `lip-sync-music-video` | repo's `audio-driven-lip-sync-video` | Same technique, two names? |
| `ai-music-video-director` | repo's `music-video-producer` | Director vs producer — different roles or the same skill twice? |
| `scene-motion` / `dance-motion` | `seedance2-director` | Are these thin wrappers, or do they carry motion vocabulary the director lacks? |
| `seedance2-composition` | `seedance2-director` | The director claims to use this for spatial blocking. Does it still hold anything the director does not? |
| The five `higgsfield-*` skills | each other | How much is shared boilerplate? |

For each, read both and answer in one line: **distinct**, **overlapping — merge
candidate**, or **superseded**.

---

## Part 4 — Report

1. The full inventory table.
2. The three buckets, with bucket B described properly — that is my pull-back list.
3. What uploaded cleanly, and anything you stopped on.
4. Any trigger phrase that would have been lost.
5. Your overlap verdicts from Part 3.
6. Anything you could not do from Cowork, stated plainly rather than worked around.

---

## What NOT to do

- **Do not delete or archive any skill**, however redundant it looks.
- **Do not edit a skill's body in the account.** The repo is the source; an edit
  made in the account is invisible to git and will be overwritten by the next
  upload. If a skill needs changing, tell me and I will change it in the repo.
- **Do not create new skills** beyond the seven attached.
- **Do not rewrite descriptions to fit the 1024 limit.** If one is over, report it
  — trimming a description is how triggers get lost.
- **Do not guess at a skill's contents.** Open it and read it. Every failure in
  this project so far has come from describing a file that was not read.

## PROMPT ENDS HERE

---

## After Cowork reports back

Bucket B is the interesting output. Those skills exist only in the account, which
means they are unversioned, unbacked-up, and invisible to the YTMF app. Each one
either belongs in the repo or should be retired deliberately.

Bring them back the way `skills/_mirror/README.md` describes: export, diff against
anything similar already in the repo, review, land, then publish back out so both
sides match.
