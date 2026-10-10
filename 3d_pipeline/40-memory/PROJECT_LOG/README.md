# PROJECT_LOG — Episodic Memory

**Lives at:** `3d_pipeline/40-memory/PROJECT_LOG/`

One markdown file per completed production, named `<project-slug>.md`.

This is **episodic** memory — what actually happened. `LESSONS.md`, `PATTERNS.md` and
`MODEL_NOTES.md` are the **distilled** layer. Nothing gets distilled that was not first recorded here.

The distinction matters: the log is evidence, the distilled files are conclusions. Keeping them
separate is what allows a conclusion to be revised when new evidence contradicts it.

---

## Required contents of a project log

Copy [`_TEMPLATE.md`](_TEMPLATE.md) and fill every section. A section with nothing in it says so
explicitly — an empty section is information, a missing section is a gap.

| Section | What goes in it |
|---|---|
| **Header** | project slug, dates, platform, account credit start/end, total spend |
| **Brief** | the one thing the piece had to communicate |
| **Shot list** | shots, durations, locations, aspect |
| **Environments** | which environments were built and how many shots each served (the reuse ratio) |
| **Blockout approach** | code-driven or conversational, per shot, and why |
| **Reference packs** | which L2 assets were built, per shot; which were reused from the library |
| **Generation** | model, duration, resolution, takes generated per shot, selected take |
| **Cost accounting** | credits per stage; cost per finished second; cost per shot |
| **What shipped** | final deliverable, resolution, runtime |
| **Failures** | generation success/failure counts **with root causes** — not just counts |
| **Library additions** | what entered the reusable library: environments, blockouts, templates, prompts |
| **Lessons produced** | links to the `LESSONS.md` entries this project generated |
| **Next time** | the one change that would most improve the next project like this |

---

## Why "library additions" is a required section

The pipeline's economics depend on reuse. A project that added nothing to the library is a project
that will be paid for again next time. Making the section mandatory makes the omission visible.

## Why "failures with root causes" is a required section

A failed generation that is not explained is a generation that will fail again. Counts without causes
cannot be distilled into rules. "6 of 14 takes rejected" is a statistic; "6 rejected because the
second character's position mirrored between cuts, because the blockout did not fix the action axis"
is a fixable defect — and is exactly the kind of entry that becomes a `LESSONS.md` rule and then a
convention in the blockout templates.

---

## Index

*(Newest first. Maintain this table — it is the fastest way to answer "have we done this before?")*

| Project | Dates | Shots | Spend | Environments | Notable reuse | Log |
|---|---|---|---|---|---|---|
| demo-infinite-loop **calibration** | 2026-09-13 | 1 | ~106 cr | 1 | toolkit + loop pattern + L2 plates | [`demo-infinite-loop.md`](demo-infinite-loop.md) |

**Calibration projects are marked as such.** `demo-infinite-loop` stopped at Gate 3 deliberately and
spent its budget on *measuring* the paid layer rather than on delivering a shot. Its value is the
routing data it produced — most importantly that a blockout locks motion and timing but **not**
composition. Do not read its spend as the cost of a delivered shot.
