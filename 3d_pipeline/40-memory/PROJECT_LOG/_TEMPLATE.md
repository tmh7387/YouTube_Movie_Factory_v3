# <PROJECT SLUG> — Production Log

**Dates:** YYYY-MM-DD → YYYY-MM-DD
**Platform:** Higgsfield · **Plan:** <plan> · **Credits at start:** <n> · **Credits at end:** <n>
**Total spend:** <n> credits
**Deliverable:** <what, resolution, runtime, aspect>

---

## 1. Brief

<The one thing this piece had to communicate. One paragraph, no style language.>

## 2. Shot list

| Shot | Duration | Location | Aspect | Notes |
|---|---|---|---|---|
| SH010 | 15 s | study | 16:9 | single continuous take |

## 3. Environments — the reuse ratio

| Environment | Built how | Shots served | Regenerated? |
|---|---|---|---|
| study | Blender code | SH010, SH020 | no |

**Reuse ratio:** <shots ÷ environments>. Target ≥ 3. A ratio near 1 means the shot list was not
grouped by location before generation, and that is the single largest avoidable cost in the pipeline.

## 4. Blockout approach

| Shot | Route (code / conversational) | Why | Iterations | Previz exported |
|---|---|---|---|---|
| SH010 | code (`shot.json` → `build_blockout.py`) | must be restylable later | 4 | `previz_SH010.mp4` |

## 5. Reference packs

| Shot | Slot | Asset | Built or reused | Credits |
|---|---|---|---|---|
| SH010 | image_1 | char-lead-v3 | built (Soul 2.0) | <n> |
| SH010 | image_2 | loc-study-v1 | **reused from project X** | 0 |

## 6. Generation

| Shot | Model | Duration | Res | Takes | Selected | Credits |
|---|---|---|---|---|---|---|
| SH010 | Seedance 2.5 | 30 s | 720p | 2 | B | <n> |

**Takes per shot (average):** <n>. **Pipeline target: 2.** Anything above 4 is a Stage Gate failure —
record where the gate was skipped.

## 7. Cost accounting

| Stage | Credits | % of total |
|---|---|---|
| L1 structure | | |
| L2 identity/look | | |
| L3 realisation | | |
| Upscale / finishing | | |
| **Total** | | 100% |

**Cost per finished second:** <n> cr/s
**Cost per shot:** <n> cr

## 8. What shipped

<Final deliverable and where it lives.>

## 9. Failures and root causes

| Count | What failed | Root cause | Fixable by |
|---|---|---|---|
| 6/14 takes | second character mirrored between cuts | blockout did not fix the action axis | blockout template |

**No bare counts.** A count without a cause cannot become a rule.

## 10. Library additions

| Asset | Type | Where it lives | Reusable for |
|---|---|---|---|
| study environment | environment `.blend` + `.glb` | `library/environments/` | any interior study scene |

If this table is empty, say so and say why. An empty library section means the next project pays
again for the same work.

## 11. Lessons produced

- → `LESSONS.md` : <entry title>
- → `MODEL_NOTES.md` : <platform behaviour that contradicted documentation>

## 12. Next time

<The single change that would most improve the next project like this. One sentence.>
