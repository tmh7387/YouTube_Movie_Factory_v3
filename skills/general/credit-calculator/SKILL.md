---
name: credit-calculator
description: >-
  Estimate video generation costs across CometAPI (SeeDream 4.5, Nanobanana, Seedance 2.0,
  Kling 3.0) and Higgsfield direct. Takes a video project scope and outputs cost estimates,
  credit breakdowns, and platform recommendations. Use this skill whenever the user asks
  about costs, credits, budget, pricing, how much a video will cost, credit comparison,
  "how many credits", "what will this cost", "budget estimate", "compare pricing",
  "cheapest option", "most cost-efficient", or wants to know the financial implications
  before starting a video generation project. Also trigger when the user is deciding
  between platforms or models for a project and cost is a factor.
---

# Credit Calculator — Video Generation Cost Estimator

Estimate the cost of a video generation project across your available platforms and
models before spending anything.

---

## Supported Platforms & Models

### CometAPI
| Model | Cost per Generation | Duration | Notes |
|---|---|---|---|
| **Seedance 2.0** | ~$0.40-0.60 per clip | 5-15s | Primary video model |
| **Kling 3.0** | ~$0.30-0.50 per clip | 5-10s | Good for I2V, fast |
| **SeeDream 4.5** | ~$0.15-0.30 per image | N/A (image) | Storyboard generation |
| **Nanobanana** | ~$0.10-0.25 per image | N/A (image) | Character/reference images |

### Higgsfield Direct
| Feature | Cost | Notes |
|---|---|---|
| **Seedance 2.0** | Credits-based (varies by plan) | Full Omni Reference, multi-character |
| **GPT Image 2** | Credits-based | Storyboard generation |
| **Cinema Studio 2.5** | Credits-based | Premium quality, real optics |
| **Soul Cast** | Included with plan | Character creation |

> **Note:** Exact pricing changes frequently. Ask the user to confirm current rates
> from their CometAPI dashboard or Higgsfield plan page if precision is critical.
> The estimates below use approximate ranges for planning purposes.

---

## Step 1 — PROJECT SCOPE

Gather these parameters to calculate:

1. **Number of final shots/clips** — How many separate video generations?
2. **Duration per clip** — 5s, 10s, 15s? (longer = more credits on some platforms)
3. **Storyboard needed?** — How many storyboard generations (usually 1-3 iterations)
4. **Character references needed?** — How many character images to generate?
5. **Re-generation buffer** — What % of clips might need re-doing? (default: 30%)
6. **Platform preference** — CometAPI, Higgsfield, or "recommend best value"?

---

## Step 2 — CALCULATE

### Formula:

```
TOTAL COST = Storyboard Cost + Character Cost + Video Cost + Buffer

Where:
  Storyboard Cost = storyboard_generations × image_cost_per_gen
  Character Cost  = character_images × image_cost_per_gen
  Video Cost      = num_clips × video_cost_per_clip
  Buffer          = Video Cost × buffer_percentage
```

### Cost Estimate Template:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COST ESTIMATE — [Project Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROJECT SCOPE:
  Clips: [N]
  Duration: [Xs per clip]
  Storyboard iterations: [N]
  Character images: [N]
  Re-gen buffer: [30%]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OPTION A: CometAPI (Seedance 2.0)
  Storyboard (SeeDream 4.5):  [N] × $[X] = $[total]
  Characters (Nanobanana):    [N] × $[X] = $[total]
  Video (Seedance 2.0):      [N] × $[X] = $[total]
  Buffer (30%):                           + $[total]
  ─────────────────────────────────────────────
  ESTIMATED TOTAL:                          $[TOTAL]

OPTION B: CometAPI (Kling 3.0)
  Storyboard (SeeDream 4.5):  [N] × $[X] = $[total]
  Characters (Nanobanana):    [N] × $[X] = $[total]
  Video (Kling 3.0):         [N] × $[X] = $[total]
  Buffer (30%):                           + $[total]
  ─────────────────────────────────────────────
  ESTIMATED TOTAL:                          $[TOTAL]

OPTION C: Higgsfield Direct
  Storyboard (GPT Image 2):  [N] generations (credits)
  Characters (Soul Cast):    Included
  Video (Seedance 2.0):     [N] generations (credits)
  Buffer (30%):              [N] extra generations
  ─────────────────────────────────────────────
  ESTIMATED TOTAL:           [N] credits (~$[equivalent])

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RECOMMENDATION: [Which option and why]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Step 3 — RECOMMEND

### Decision Matrix:

| Priority | Recommend | Why |
|---|---|---|
| Lowest cost per clip | CometAPI Kling 3.0 | Cheapest per generation |
| Best quality / control | Higgsfield Seedance 2.0 | Full Omni Reference, Cinema Studio |
| Multi-character precision | Higgsfield Seedance 2.0 | Best character locking system |
| Speed / volume | CometAPI Seedance 2.0 | API-driven, parallelizable |
| Budget-constrained short | CometAPI Kling 3.0 | Low cost, good quality for simple scenes |
| Premium brand content | Higgsfield Cinema Studio 2.5 | Real optical physics, Soul Cast |

### Real-World Benchmarks (anecdotal, added 2026-07-15)

Two creator-reported figures from Higgsfield AI's own tutorial comment sections — useful
as sanity-check reference points for client budgeting, **not** official pricing (Higgsfield
pricing changes frequently; always confirm current rates per Step 0's note above):

| Project type | Reported spend | Source |
|---|---|---|
| ~35s fully-AI 4K product commercial (5 scenes, asset-heavy) | Commenter-reported range ~$1,000–$1,500 in Higgsfield credits | YouTube comment on "3-Step Workflow To Make Ultra-Realistic AI Ads" (2026-06-23), unverified |
| Full brand video project, professional-grade | ~$1,000 credits + 5 days of work, on a $12,000 client budget | YouTube comment, same video, unverified |

Use these as an order-of-magnitude gut check when a client asks "roughly what does a
polished 30–60s AI commercial cost in credits" before running the full Step 2 calculation
— not as a quoted number. Both figures are third-party comments, not confirmed platform
pricing.

### Model Selection by Use Case:

| Use Case | Best Model | Platform | Reason |
|---|---|---|---|
| 2+ character interaction | Seedance 2.0 | Higgsfield | Omni Reference + storyboard |
| Single character action | Seedance 2.0 | CometAPI or Higgsfield | Either works well |
| Product/brand reveal | Cinema Studio 2.5 | Higgsfield | Real optics, Soul HEX color |
| Quick social content | Kling 3.0 | CometAPI | Fast, cheap, good enough |
| Cinematic short film | Seedance 2.0 | Higgsfield | Maximum control |
| Batch content (10+ clips) | Seedance 2.0 | CometAPI | API automation, parallel |
| Character reference gen | Nanobanana | CometAPI | Cost-effective image gen |
| Storyboard generation | SeeDream 4.5 | CometAPI | Or GPT Image 2 on Higgsfield |

---

## Step 4 — OPTIMIZATION TIPS

Always include applicable tips:

- **Storyboard first = fewer re-generations.** A $0.20 storyboard can save $2-3 in failed video generations.
- **Generate hero shot first.** Spend fresh attention on the hardest shot. Easier shots are forgiving.
- **Simpler backgrounds = higher consistency.** Complex environments burn credits on re-dos.
- **One model per project.** Mixing models breaks visual consistency and requires more iterations.
- **Front-facing references save credits.** Clean references = fewer character drift re-generations.

---

## MODES

**FULL MODE** (default) — Complete cost breakdown with all options and recommendation.

**QUICK MODE** — "Quick estimate for N clips on [platform]" → Single number + buffer.

**COMPARE MODE** — Side-by-side comparison of two specific options the user is considering.

**BUDGET MODE** — "I have $X budget" → How many clips/shots can they afford on each platform?
