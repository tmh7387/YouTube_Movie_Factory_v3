# Core GPT Image 2 Prompt Guide Library

## Overview

This document is a publication-ready draft for a broad creator audience using GPT Image 2 for still-image generation and for producing reference images that feed downstream AI video workflows.[cite:2][cite:3] It combines official OpenAI guidance with practical prompting patterns from Fal and other current GPT Image 2 guides, then organizes them into reusable templates, style systems, and categorized prompt libraries.[cite:2][cite:3][cite:4][cite:6][cite:16]

The core premise is simple: GPT Image 2 performs best when prompts behave like creative briefs rather than vague descriptions.[cite:2][cite:3] For creators building image sets, storyboards, or video-reference packs, prompts should not only describe how an image should look, but also explicitly define what must remain stable across iterations.[cite:2][cite:3][cite:28]

## Audience and use cases

This guide is designed for general AI creators producing polished still images, concept frames, ads, product mockups, character references, environment plates, diagrams, UI screens, and continuity frames for later video generation.[cite:2][cite:16][cite:26] GPT Image 2 is especially suited to photorealism, text-heavy layouts, structured visuals such as infographics and diagrams, identity-sensitive edits, and compositing workflows where fewer retries matter.[cite:2][cite:24]

Recommended creator workflows include:

- One-off still image generation for campaigns, posters, and editorial visuals.[cite:2][cite:3]
- Edit-based refinement where a base image is preserved while a single element changes.[cite:2][cite:3][cite:28]
- Multi-image reference workflows where subject, wardrobe, lighting, props, and background references are combined into a controlled composite.[cite:2][cite:3][cite:28]
- Reference-image packs for AI video systems, where the goal is consistency of identity, styling, environment, and shot language before motion is added later.[cite:2][cite:6][cite:26]

## GPT Image 2 capabilities

OpenAI positions `gpt-image-2` as the default image model for new builds and highlights high-fidelity photorealism, reliable text rendering, complex structured visuals, strong style control, and robust identity preservation in edits and multi-step workflows.[cite:2] The official API documentation also describes it as the recommended default for highest-quality generation and editing, especially for text-heavy images, compositing, and identity-sensitive work.[cite:2][cite:24]

Useful model guidance for production:

| Topic | Guidance |
|---|---|
| Default model | `gpt-image-2` is the recommended default for new workflows.[cite:2][cite:24] |
| Quality settings | `low`, `medium`, and `high` are supported; `low` is useful for speed, while `medium` and `high` fit dense text, close-up portraits, high-resolution outputs, and identity-sensitive edits.[cite:2] |
| Resolution rules | Output sizes must respect edge, ratio, and pixel-count constraints; OpenAI notes that outputs above 2560x1440 should be treated as more variable or experimental.[cite:2] |
| Reference-heavy work | Official guidance emphasizes multi-image inputs, explicit preserve/change instructions, and structured prompts for compositing and edits.[cite:2][cite:28] |

## Prompting principles

Official OpenAI guidance recommends a stable prompt order such as background or scene, then subject, then key details, then constraints, optionally including the intended use case so the model understands the artifact type and level of polish.[cite:2] Fal’s GPT Image 2 guide converges on nearly the same logic, using five explicit prompt slots: Scene, Subject, Important details, Use case, and Constraints.[cite:3]

Across sources, the consistent pattern is that high-performing prompts rely on visual facts instead of praise words.[cite:2][cite:3] Terms such as “stunning,” “epic,” or “masterpiece” contribute little, while concrete specifications such as lighting direction, material texture, framing, lens feel, text placement, and a preserve list give the model measurable targets.[cite:2][cite:3][cite:6]

### Prompting rules

- Use structure before style; a clean prompt skeleton is more valuable than piles of adjectives.[cite:2][cite:3]
- State the intended artifact, such as editorial photo, UI screen, infographic, concept frame, billboard, or character sheet.[cite:2][cite:3]
- Use explicit constraints such as “no watermark,” “no extra text,” “preserve layout,” “preserve face,” or “change only the background.”[cite:2][cite:3][cite:28]
- Treat in-image text as typography, not mood; quote exact strings and specify placement, font feel, contrast, and duplication constraints.[cite:2][cite:3][cite:16]
- Iterate with one change at a time instead of rewriting the entire brief every round.[cite:2][cite:3]

## Universal prompt structure

The most reusable publication-ready prompt structure for GPT Image 2 is a merged version of the OpenAI and Fal patterns.[cite:2][cite:3] This structure works for still-image creators because it is short enough to reuse at scale, but explicit enough for both first-pass generation and edit workflows.[cite:2][cite:3][cite:4]

### Standard template

```text
Scene:
[where this happens, time of day, background, environment]

Subject:
[who or what is the main focus]

Action:
[what is happening in this moment]

Important details:
[materials, clothing, texture, lighting, camera angle, lens feel, composition, mood]

Style:
[photorealistic / watercolor / anime / blueprint / isometric / etc.]

Use case:
[editorial photo / product mockup / poster / UI screen / infographic / concept frame / character sheet]

Constraints:
[no watermark / no logos / no extra text / preserve face / preserve layout / exact text only]
```

This template extends Fal’s five-slot method by separating Action and Style into their own blocks, which improves reuse across editorial, product, diagram, and video-reference work.[cite:3][cite:4][cite:6] It also aligns with OpenAI’s emphasis on structure, intended use, composition, and explicit preservation constraints.[cite:2]

### Reference-image extension

For AI video preparation, the standard template should be extended with a dedicated continuity section.[cite:2][cite:6][cite:26] This is where identity, wardrobe, color palette, background geometry, lens feel, lighting direction, and shot framing are locked before motion is introduced in a downstream video tool.[cite:2][cite:6]

```text
Continuity locks:
[preserve exact facial features, hair silhouette, outfit design, accessory placement,
background geometry, lighting direction, camera height, lens feel, and color palette]
```

This extra block turns a general image prompt into a production reference prompt.[cite:2][cite:28] For creators building video-reference stills, continuity instructions are often more important than raw stylistic flourish.[cite:6][cite:26]

## Style tiles system

A style-tile system makes the guide easier to browse and apply because creators can choose a visual language first, then attach it to any category prompt.[cite:4][cite:13][cite:18] Current GPT Image 2 prompt guides and broader AI art taxonomies repeatedly show that naming the medium or visual system directly leads to better control than using fuzzy aesthetic labels.[cite:3][cite:4][cite:13]

Each tile in a visual picker should contain:

- Style name.[cite:4]
- A one-line descriptor.[cite:13]
- A reusable prompt snippet.[cite:4][cite:18]
- Typical use cases.[cite:11][cite:21]
- A note on continuity strength for video-reference work.[cite:26]

### Style tiles

| Tile | Descriptor | Prompt snippet | Best uses |
|---|---|---|---|
| Photorealistic | Natural camera realism | “photorealistic, natural lighting, realistic materials, subtle film grain”[cite:2][cite:18] | Editorial, portraits, product, cinematic frames[cedite:2] |
| Minimalist | Clean, restrained composition | “minimalist composition, neutral background, generous negative space, clear subject hierarchy”[cite:4][cite:18] | Ads, product, layouts, clean posters[cite:4] |
| Watercolor | Soft painterly illustration | “watercolor illustration, soft edges, visible paper texture, gentle color transitions”[cite:4][cite:18] | Storybooks, concept art, mood pieces[cite:4] |
| Anime | Stylized 2D cel look | “anime style, clean cel shading, crisp line work, bold flat color areas”[cite:4][cite:18] | Characters, key art, stylized frames[cite:4] |
| Blueprint | Technical line drawing | “technical blueprint, white linework on blue background, orthographic view, precise labels”[cite:2][cite:23] | Schematics, exploded views, instructional visuals[cite:2][cite:23] |
| Isometric | Controlled 3D diagram style | “isometric 3D illustration, fixed-angle perspective, soft global illumination”[cite:4][cite:23] | Layouts, apps, city scenes, diagrams[cite:4][cite:23] |
| Pixel art | Retro grid-based image | “16-bit pixel art, crisp pixels, limited palette, retro game aesthetic”[cite:4][cite:13] | Retro scenes, gaming, stylized posters[cite:13] |
| Voxel | Blocky 3D form language | “voxel art, block-built 3D forms, playful lighting, game-like geometry”[cite:4][cite:13] | Worldbuilding, game concepts, toy-like scenes[cite:13] |
| Noir | High-contrast dramatic realism | “film noir lighting, strong contrast, deep shadow, moody monochrome or restrained color”[cite:18] | Crime visuals, moody portraits, cinematic stills[cite:18] |
| Cyberpunk | Neon urban sci-fi | “neon-lit cyberpunk city, wet reflections, dense signage, magenta and teal accents”[cite:18] | Futuristic scenes, concept frames, posters[cite:18] |
| Fantasy | Epic painterly worldbuilding | “epic fantasy illustration, atmospheric scale, dramatic landscape, cinematic light”[cite:18][cite:21] | Characters, worlds, book covers[cite:21] |
| Data Viz / UI | Structured informational output | “clean dashboard or infographic layout, legible charts, modern UI hierarchy, crisp labels”[cite:2][cite:17][cite:23] | UI screens, dashboards, explainers[cite:2][cite:23] |

For video-reference work, Photorealistic, Minimalist, Blueprint, Isometric, and Architectural-style outputs generally provide the strongest continuity anchors because they keep form, lighting, and geometry stable.[cite:2][cite:23][cite:26] Surreal, heavily painterly, or highly abstract styles may be excellent for ideation but weaker as continuity anchors when later converted to motion.[cite:7][cite:26]

## Workflow patterns

The best creator workflows can be organized into three practical modes: generate from scratch, edit one image, and combine multiple images.[cite:3] This matches Fal’s operational framing and closely aligns with OpenAI’s guidance around generation, surgical edits, and multi-image compositing.[cite:2][cite:3][cite:28]

### 1. Generate from scratch

Use this mode for editorial stills, posters, concept art, product scenes, character sheets, diagrams, and UI mockups.[cite:2][cite:3] The universal prompt structure is usually sufficient here, with style and use-case blocks doing most of the control work.[cite:2][cite:3]

### 2. Edit one image

Use this mode when a single existing image should remain mostly intact while a narrow attribute changes, such as outfit, weather, object removal, background cleanup, or relighting.[cite:2][cite:3][cite:28] OpenAI and Fal both recommend the same wording pattern: describe the exact change, then explicitly list what must remain fixed.[cite:2][cite:3]

Edit template:

```text
Change:
[exactly what should change]

Preserve:
[face, identity, pose, lighting, framing, background, geometry, text, layout]

Constraints:
[no extra objects, no redesign, no logo drift, no watermark]
```

### 3. Combine multiple images

Use this mode for compositing, virtual try-on, style transfer, and reference-image blending.[cite:2][cite:3][cite:28] Source guidance recommends labeling each image by role rather than assuming the model will infer which image supplies content, style, wardrobe, subject, or environment.[cite:2][cite:3]

Composite template:

```text
Image 1: base scene to preserve.
Image 2: subject or identity reference.
Image 3: outfit or prop reference.
Image 4: style or lighting reference.

Instruction:
[combine the desired elements]
Preserve [identity / background / camera angle / scale / lighting] from Image 1.
Do not add extra accessories, objects, or text.
```

Fal explicitly notes support for up to 16 reference images in GPT Image family edit workflows, and the OpenAI edit reference documents multi-image input support for image-editing operations.[cite:3][cite:28]

## Reference images for AI video

For creators preparing images that will later be animated in AI video systems, the still image should be treated as a production reference rather than a standalone artwork.[cite:2][cite:6][cite:26] The goal is not only visual quality but also continuity: stable identity, costume, proportions, camera logic, and environment detail across multiple frames or shots.[cite:2][cite:6]

### Recommended reference packs

| Pack type | Contents | Why it matters |
|---|---|---|
| Character pack | Front view, 3/4 view, side view, expression sheet, full-body outfit view.[cite:6][cite:26] | Locks identity, proportions, and wardrobe for later animation.[cite:6] |
| Environment pack | Wide establishing shot, medium framing, detail shot, lighting reference.[cite:2][cite:18] | Stabilizes world design, atmosphere, and light logic.[cite:2] |
| Prop pack | Hero object, close-up material detail, context-in-use shot.[cite:20][cite:26] | Preserves object design and material behavior across scenes.[cite:20] |
| Anchor keyframe | A single “gold standard” still defining the ideal composition, grading, and mood.[cite:2][cite:6] | Serves as the baseline for all later edits and motion translations.[cite:6] |

### Reference-image prompt rules

- State the role of each input image explicitly.[cite:2][cite:3]
- Separate “change” instructions from “preserve” instructions.[cite:2][cite:3][cite:28]
- Use a continuity lock list in every prompt round to reduce drift.[cite:2][cite:6]
- Keep one variable changing at a time: identity, then wardrobe, then background, then lighting, rather than changing everything in one pass.[cite:2][cite:26]
- Reuse one master keyframe as the anchor image for all future edits.[cite:2][cite:6]

### Example reference prompt

```text
Image 1: character identity reference.
Image 2: outfit reference.
Image 3: environment lighting reference.

Instruction:
Create a photorealistic full-body keyframe of the same woman from Image 1 wearing the outfit from Image 2 in the environment mood of Image 3.

Continuity locks:
Preserve exact facial structure, hair silhouette, body proportions, outfit construction, skin tone,
camera height, 50mm lens feel, and soft side-light direction.

Constraints:
No extra accessories, no text, no logos, no watermark.
```

## Prompt library by category

The most practical way to publish the guide is to group prompts by creator intent rather than by abstract aesthetics alone.[cite:11][cite:17][cite:21] Each category below includes a recommended structure and copy-ready examples.

### Character portraits and turnarounds

Character prompts should define identity markers, clothing, expression range, and proportion rules in a way that supports later re-use.[cite:2][cite:6] This is essential for storyboards, comics, and AI video reference packs.[cite:6][cite:26]

Template:

```text
Scene:
Neutral studio backdrop or simple environment.

Subject:
[character identity, age, face shape, hair, build, clothing]

Action:
Standing front-facing / 3/4 / side profile.

Important details:
[expression, material texture, silhouette, accessories, camera height]

Style:
[photoreal / anime / watercolor / etc.]

Use case:
Character turnaround or continuity sheet.

Constraints:
No redesign between views, preserve proportions, no text, no watermark.
```

Example prompt:

```text
Scene:
Neutral light-gray studio backdrop with soft diffuse lighting.

Subject:
A woman in her late 20s with a narrow face, dark shoulder-length hair tied loosely back,
athletic build, olive field jacket, charcoal cargo pants, and brown leather boots.

Action:
Full-body 3/4 standing pose, relaxed posture, facing slightly left.

Important details:
Realistic skin texture, minimal makeup, visible fabric folds, practical outdoor clothing,
eye-level framing, 50mm lens feel, calm confident expression.

Style:
Photorealistic.

Use case:
Character continuity sheet for AI video generation.

Continuity locks:
Preserve exact face shape, hairstyle silhouette, jacket design, body proportions, and color palette.

Constraints:
No extra props, no jewelry, no text, no watermark.
```

### Environment plates and establishing shots

Environment prompts work best when they specify time, atmosphere, scale, and foreground-to-background structure.[cite:2][cite:18] For video prep, they should also lock the lens feel and lighting logic so later shots belong to the same world.[cite:2][cite:6]

Example prompt:

```text
Scene:
A mountain village road just after rainfall at blue hour, with mist hanging low between the houses.

Subject:
The environment itself is the focus.

Action:
No human activity; the image captures the stillness of the place.

Important details:
Wet cobblestones, warm window lights, distant hills fading into fog,
subtle reflections, wide establishing composition, 35mm cinematic lens feel.

Style:
Photorealistic.

Use case:
Environment plate for a narrative AI video sequence.

Continuity locks:
Preserve the road layout, house spacing, mist level, and warm-versus-cool lighting contrast.

Constraints:
No people, no vehicles, no signage drift, no text, no watermark.
```

### Storyboard keyframes

Storyboard prompts should describe a narrative beat rather than a generic image concept.[cite:7][cite:26] Action, camera angle, and emotional clarity matter more than visual excess.[cite:18][cite:26]

Example prompt:

```text
Scene:
Small roadside diner parking lot at dawn.

Subject:
A tired traveler stepping out of an old sedan.

Action:
She pauses with one hand on the open door, looking toward the lit diner sign in the distance.

Important details:
Low-angle medium-wide framing, pale morning sky, slight ground fog,
car headlights fading, realistic jacket wrinkles, honest documentary mood.

Style:
Photorealistic with subtle film-grain realism.

Use case:
Storyboard keyframe for a road-trip video sequence.

Constraints:
No stylized grading, no extra people, no text, no watermark.
```

### Product shots and marketing stills

Product prompts need material accuracy, lighting control, packaging fidelity, and clean composition.[cite:2][cite:20] Marketing-oriented prompts should be written like mini creative briefs with clear audience, mood, layout, and text constraints.[cite:2][cite:20]

Example prompt:

```text
Scene:
Softly lit café tabletop at sunrise.

Subject:
A premium craft coffee bag standing upright.

Action:
Static product hero shot.

Important details:
Matte kraft paper material, subtle crinkles, shallow depth of field,
warm rim light, ceramic cup blurred in the background, realistic print texture.

Style:
Photorealistic product photography.

Use case:
Lifestyle product advertisement.

Constraints:
Label text must remain sharp and legible, no extra products, no logos beyond the package design,
no watermark.
```

### UI screens and dashboards

OpenAI explicitly identifies GPT Image 2 as strong for structured visuals, UI mockups, charts, and infographics when prompts define hierarchy, layout, real copy, and readability constraints.[cite:2] Fal’s guide also shows that interface prompts improve sharply when the screen type, exact text, and spacing logic are specified directly.[cite:3]

Template:

```text
Scene:
None; this is a flat interface artifact.

Subject:
[dashboard / mobile app / onboarding screen / analytics panel]

Action:
Static screen state.

Important details:
[layout regions, panels, navigation, exact labels, chart types, spacing, color system]

Style:
Clean modern UI, crisp typography, flat or lightly dimensional.

Use case:
UI mockup or product screenshot.

Constraints:
No lorem ipsum, no fake logos, no illegible widgets, no watermark.
```

Example prompt:

```text
Scene:
Desktop SaaS analytics product.

Subject:
A fleet management dashboard.

Action:
Static logged-in dashboard overview screen.

Important details:
Left navigation rail with icons, top bar with search and account menu,
main content area with KPI cards, a live map panel on the left, a trips table on the right,
teal accent color on a deep navy interface, legible labels reading “Vehicles,” “Trips,” “Alerts,” and “Fuel Usage,”
clean chart hierarchy, generous spacing, crisp modern sans-serif typography.

Style:
Clean UI screenshot.

Use case:
Marketing screenshot for a software landing page.

Constraints:
No lorem ipsum, no brand theft, no extra modal windows, no watermark.
```

### Infographics and educational visuals

OpenAI’s cookbook explicitly calls out infographics, diagrams, timelines, and educational explainers as strong use cases for GPT Image 2, especially at higher quality settings for denser layouts and labels.[cite:2] These prompts should be treated as instructional artifact specs, not generic illustration requests.[cite:2]

Example prompt:

```text
Scene:
White classroom-handout background.

Subject:
A clean infographic explaining the flow of a solar-powered irrigation system.

Action:
A left-to-right labeled process from solar panel to controller to pump to field irrigation.

Important details:
Clear arrows, consistent icon style, labels for panel, inverter, controller, battery, pump, and water outlet,
legible typography, generous white space, restrained blue-green palette.

Style:
Flat educational infographic.

Use case:
Teacher slide and training handout.

Constraints:
No clutter, no tiny labels, no decorative stock-photo elements, no watermark.
```

### Technical diagrams and blueprints

Technical prompts should define the diagram type, view angle, label strategy, and precision expectations.[cite:2][cite:23] Blueprint and isometric approaches are especially effective because they constrain the visual language tightly.[cite:23]

Example prompt:

```text
Scene:
Neutral white background.

Subject:
An aircraft maintenance hangar layout.

Action:
Static technical overview.

Important details:
Top-down isometric view with clearly separated zones labeled “Receiving,” “Inspection,” “Repair Bays,”
“Parts Storage,” and “Quality Control,” precise linework, restrained gray-blue-orange palette,
clean vector-like labels and arrows.

Style:
Isometric technical diagram.

Use case:
Operations explainer for training materials.

Constraints:
No decorative icons, no watermark, no text artifacts, no extra zones.
```

### Ads and poster concepts

Advertising prompts work best when they include audience, culture, composition, and exact copy, allowing the model to interpret art direction within clear bounds.[cite:2] This is particularly effective for rapid campaign exploration and still-image concepting.[cite:2][cite:21]

Example prompt:

```text
Scene:
Urban rooftop gathering at twilight.

Subject:
A small group of friends wearing a fictional youth streetwear brand.

Action:
They are laughing together in a candid fashion-campaign moment.

Important details:
Premium fashion-photography feel, clean composition, natural body language,
strong warm-versus-cool color direction, exact tagline “Yours to Create” rendered once,
clear ad hierarchy with subject grouping on the right and negative space on the left.

Style:
Polished contemporary campaign photography.

Use case:
Streetwear ad concept.

Constraints:
No unrelated logos, no extra text, no watermark.
```

## Edit prompt library

Edit prompts should be concise, surgical, and repeatable.[cite:2][cite:3] The strongest formulation is usually a three-part instruction: define the change, define the preserve list, then define realism or cleanup constraints.[cite:2][cite:3]

### Object removal

```text
Change:
Remove the flower from the man’s hand.

Preserve:
Face, clothing, pose, camera angle, lighting, background, and all other objects exactly.

Constraints:
Reconstruct the hand naturally, no ghosting, no added objects, no watermark.
```

### Outfit change

```text
Change:
Replace only the clothing with a dark olive waxed jacket, charcoal trousers, and brown leather boots.

Preserve:
Face, skin tone, body shape, hands, hair, expression, pose, background, camera angle, framing,
and original lighting exactly.

Constraints:
Fit garments naturally with realistic folds and shadows, no jewelry, no text, no logos.
```

### Weather transformation

```text
Change:
Make the scene look like a winter evening with light snowfall.

Preserve:
Identity, geometry, camera angle, object placement, signs, buildings, and composition.

Constraints:
Adjust only weather, ambient light, and surface wetness, no new objects, no watermark.
```

### Background cleanup

```text
Change:
Remove every advertising poster from the shop windows.

Preserve:
Awning, brick facade, window mullions, sidewalk reflections, every person, camera framing, and color balance.

Constraints:
Reconstruct glass reflections naturally, no adhesive marks, no logo drift, no watermark.
```

## Copy-paste prompt starter set

The following starter prompts are suitable for direct inclusion in a public prompt library because they are specific, reusable, and category-balanced.[cite:2][cite:3][cite:4]

### Photoreal editorial still

```text
Scene:
A quiet neighborhood fish market just after dawn.

Subject:
A fishmonger unloading crates of mackerel.

Action:
He places fresh fish onto crushed ice while checking a handwritten paper ledger.

Important details:
Cold air visible in breath, wet concrete floor, rubber boots, warm incandescent lamp,
35mm documentary lens feel, realistic scales and skin texture, shallow depth of field.

Style:
Photorealistic documentary photography.

Use case:
Editorial newspaper feature image.

Constraints:
No commercial styling, no watermark, no logos.
```

### Readable billboard mockup

```text
Scene:
Roadside billboard at sunset.

Subject:
A shampoo campaign billboard.

Action:
Static advertising mockup.

Important details:
Product bottle on the right, generous negative space on the left,
headline rendered once as exact text: “Fresh and clean,” bold sans-serif typography,
high contrast, readable from a distance.

Style:
Photorealistic outdoor advertising mockup.

Use case:
Marketing concept frame.

Constraints:
Render text verbatim, no extra words, no duplicate text, no extra logos, no watermark.
```

### Mobile onboarding screen

```text
Scene:
Vertical mobile app interface.

Subject:
An onboarding screen for a fictional app called NESTING.

Action:
Static welcome screen.

Important details:
Headline “WELCOME TO NESTING,” supporting line “A quieter way to gather people around a table,”
buttons “Get started” and “I already have an account,” small line illustration of three plates and two wine glasses,
warm cream background, coral primary button, rounded sans-serif typography.

Style:
Clean mobile UI mockup.

Use case:
App concept and marketing screenshot.

Constraints:
Exact readable copy, no watermark, no real app branding.
```

### Character anchor frame

```text
Scene:
Simple forest clearing with soft daylight.

Subject:
A young forest helper wearing a green hooded tunic, soft brown boots, and a small belt pouch.

Action:
Standing calmly and looking slightly toward the viewer.

Important details:
Kind expression, gentle eyes, warm but brave personality, hand-painted watercolor look,
earthy palette, soft outlines, slightly oversized storybook proportions.

Style:
Children’s book watercolor illustration.

Use case:
Character anchor image for a multi-scene story and AI video reference pack.

Continuity locks:
Preserve same face, tunic design, proportions, and color palette in all later versions.

Constraints:
No text, no watermark, no redesign.
```

## Extra tips and anti-slop rules

Current GPT Image 2 prompting guidance strongly favors literal visual specificity over inflated quality jargon.[cite:2][cite:3] The most common failure mode is not model weakness, but prompt vagueness: creators describe taste while omitting structure, geometry, and preservation rules.[cite:2][cite:3][cite:6]

### What to do

- Put the main subject near the start of the prompt.[cite:3][cite:18]
- Use explicit camera and framing language such as “eye-level medium shot” or “wide establishing frame.”[cite:2][cite:18]
- Describe materials, wear, texture, and physical realism directly.[cite:2][cite:3]
- Quote exact text and specify that it must appear once, verbatim, with no extra words.[cite:2][cite:3][cite:16]
- For edits, repeat the preserve list every round rather than assuming the model remembers what matters most.[cite:2][cite:3]
- For video-reference work, change one variable at a time and keep one anchor keyframe constant across the sequence.[cite:2][cite:6][cite:26]

### What to avoid

- Vague praise words such as “stunning,” “masterpiece,” or “epic.”[cite:3]
- Style piles without visual anchors, such as “minimalist brutalist editorial luxury modern premium.”[cite:3]
- Multi-change edit prompts that ask for better text, better outfit, better background, and preserved everything in one pass.[cite:3]
- Implicit preserve rules; if identity, layout, or brand assets must remain stable, they should be stated directly.[cite:2][cite:3]

## Editorial guidance for publication

For publication as a public-facing guide, the strongest structure is: introduction, model capabilities, universal prompt template, style tiles, workflow modes, reference-image methods for AI video, category-based prompt library, edit patterns, and practical tips.[cite:2][cite:3][cite:6] This sequence mirrors how creators actually work: first understanding the system, then choosing a visual mode, then selecting a task-specific pattern.[cite:2][cite:3]

Recommended presentation choices:

- Use one master prompt template near the front of the guide.[cite:2][cite:3]
- Present style tiles as cards or a visual grid, each with a descriptor and prompt snippet.[cite:4][cite:13]
- Organize examples by creator task, not just by art style.[cite:11][cite:17][cite:21]
- Mark prompts that are especially suitable for AI video reference generation with a continuity icon or callout.[cite:6][cite:26]
- Keep prompts copy-ready and avoid over-explaining obvious wording inside the examples.[cite:3]

## Closing note

A useful GPT Image 2 guide is not just a list of prompts; it is a control system for visual intent.[cite:2][cite:3] For general still-image creators and for teams preparing reference images for AI video, the most successful prompts combine clear artifact intent, strong visual facts, explicit preservation rules, and a repeatable template that can scale from one image to a full continuity pack.[cite:2][cite:3][cite:6][cite:28]
