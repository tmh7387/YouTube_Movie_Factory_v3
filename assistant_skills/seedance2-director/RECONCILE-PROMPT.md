# Prompt — reconcile `seedance2-director` into a canonical master

**Run this in Claude Code, locally, with `D:\App development\YouTube_Movie_Factory_v3`
as the project folder, on `main`.**

Do not run it in claude.ai. Every path below is a real file in the repo. The whole
point of this version is that the session reads the actual documents instead of
being told what they contain — which is how the three previous attempts went wrong.

Paste everything between the markers.

---

## PROMPT STARTS HERE

You are producing the canonical master for my `seedance2-director` assistant
skill. It does not exist yet. Two half-versions do, and neither is a superset of
the other.

**Read these first, in this order, in full. Do not skim and do not start writing
until all of them are read.**

| Path | What it is | Lines |
|---|---|---|
| `docs/SKILL_ARCHITECTURE_REVIEW.md` | Why there are two skill systems and why they keep getting confused | — |
| `assistant_skills/README.md` | The layout and publish process you are feeding into | — |
| `skills/general/seedance2-director-v2/SKILL.md` | **Source A** — the production master | 600 |
| `assistant_skills/seedance2-director/_live_export/SKILL.md` | **Source B** — what is actually live in my claude.ai account, exported 2026-07-24 | 532 |

Also read, because Source A points at them and the master will inherit them:

- `skills/general/seedance2-director-v2/references/shot-spine.md` (182)
- `skills/general/seedance2-director-v2/references/seedance2-5-capabilities.md` (294)
- `skills/general/seedance2-director-v2/references/seedance2-capabilities.md` (225)
- `skills/general/seedance2-director-v2/references/camera-bible.md` (294)
- `skills/general/seedance2-director-v2/references/prompt-examples.md` (268)

### The situation

Source A and Source B describe the same skill and share a common ancestor, but
each carries roughly eight feature areas the other does not. Publishing either one
over the other deletes real work. That has already happened repeatedly on this
project and produced seven divergent builds.

From my own comparison — **verify it yourself, do not take it on trust**:

**In A, not in B:** `STEP 0.5` version routing, the shot-spine reference, the 2.5
capabilities reference, `DURATION CALIBRATION`, Smart Cuts and cut discipline,
Seedance native camera controls, whip pan discipline, creative principles.

**In B, not in A:** `UPSTREAM / DOWNSTREAM SKILL MAP`, `HIGGSFIELD MCP EXECUTION`,
`MODE C` storyboard-driven, `OUTPUT SETTINGS`, `PLATFORM CONSTRAINTS`,
`PROMPT DISCIPLINE RULES` (four, including phoneme articulation), `Manifest
Integration`, and the R2V / V2V modes.

### Task

Produce `assistant_skills/seedance2-director/SKILL.md` — the union of both, with
the conflicts resolved.

### Rules

1. **Nothing may be dropped silently.** If you leave anything out of either
   source, list it explicitly in your report with a reason. A section you judge
   redundant still gets named.

2. **On direct conflict, the more specific and more recent statement wins** — but
   say which you chose and why. The known conflicts:

   - **Mode numbering.** A uses Mode A/B/C; B uses A/B/C plus R2V and V2V and an
     `OPERATIONAL MODES` section. Reconcile into one scheme, do not leave two.
   - **Step numbering.** A has `STEP 0.5 VERSION ROUTING` then `STEP 1 MODE
     DETECTION`; B numbers steps 1-5 differently. Renumber cleanly, keeping
     version routing first — the target version changes the prompt's grammar, so
     it has to be decided before anything else.
   - **Prompt header ordering.** B's `OUTPUT SETTINGS` says what goes at the top
     of a prompt; A's shot spine slot 1 also does. Merge into one ordered header.
     Do not leave two competing instructions about what goes first.

3. **Fix these three known defects while you are in there.** All three are
   confirmed, not suspected:

   - **B's `PLATFORM CONSTRAINTS` states a flat 15-second maximum** as an engine
     fact. It is 2.0's limit. 2.5 runs to 30s. Split the row by version. Then add,
     directly under the table, that the ceiling is an upper bound and the actual
     runtime is derived from the scene's beats — A's shot spine already states the
     principle as *"runtime available is not runtime required"*; reuse that wording
     rather than inventing new.
   - **The dialogue word budget** ("~25-30 spoken words fit into 15 seconds")
     appears in both. It breaks at 30s. Make it a rate: roughly 2 spoken words per
     second, budgeted against the shot's derived runtime.
   - **Both call the skill a Seedance 2.0 skill** in places. It covers 2.0 and 2.5.
     Update the title, the description and the opening line. **Keep every trigger
     phrase from both descriptions** — union them, drop none. List the triggers
     before and after so I can compare.

4. **References.** The live account build has no reference files; the production
   master has five. Copy all five into
   `assistant_skills/seedance2-director/references/`, and make the master's
   "read these first" step list them. If any reference contradicts the merged body
   after your edits, fix the reference too and say which.

5. **Do not invent capability claims.** Every factual statement must trace to one
   of the sources or to
   `reference_documents/proposed_skill_updates/seedance-2-5-rollout/seedance-2-5-practitioner-findings.md`.
   That findings file is itself sourced from two creator videos transcribed from
   auto-captions — the 30s ceiling, the 50-asset limit and the [0.4, 2.5] ratio
   range are **not** vendor-confirmed. Mark anything resting on them as
   unverified rather than stating it flatly.

6. **Do not touch `skills/general/`.** That tree is the production skill, loaded by
   the backend at runtime. It is a different consumer with a different contract.
   This task only writes under `assistant_skills/`.

7. **Do not touch `_live_export/`.** It is evidence of what the account held. It
   must stay exactly as exported.

### Working method

- Build a section-by-section mapping table first — every heading in A, every
  heading in B, and what happens to it (keep / merge-into-X / drop-because-Y).
  **Show me that table and stop.** I will approve it before you write the file.
- Then write the file.
- Then produce the report below.

### Report when done

1. The mapping table, with the final disposition of every section.
2. Everything dropped, and why.
3. Every conflict resolved, and which side won.
4. Trigger phrases before (A), before (B), and after.
5. Line count of the result, against A's 600 and B's 532.
6. Anything you found that contradicts what I said above. I would rather be
   corrected than agreed with.

### What NOT to do

- Do not build or upload a `.skill` package. Publishing is a separate, deliberate
  step with its own log entry.
- Do not edit anything in `C:\Users\Admin\Documents\Claude\Projects\Content_Intelligence\`.
  The vault is downstream and gets refreshed from the repo afterwards.
- Do not "tidy" sections you were not asked to change. A diff full of unrelated
  rewording is a diff I cannot review.

## PROMPT ENDS HERE

---

## After this lands

1. I review and commit the master.
2. Build `.build/seedance2-director.skill` and upload it to claude.ai.
3. Record it in `SYNC_LOG.md`.
4. Refresh the vault copy from the same commit.
5. Repeat the same reconciliation for the other assistant skills — the audit found
   the same split in `storyboard-generator`, `credit-calculator` and
   `video-production-planner`. `seedance2-composition` and `ai-music-video-director`
   have no local copy at all and need exporting from the account first.
