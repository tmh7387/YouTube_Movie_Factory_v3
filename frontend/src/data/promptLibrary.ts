/**
 * Core Prompt Guide Library
 *
 * Curated, version-controlled prompt reference for image and video generation.
 *
 * Provenance:
 *  - GPT Image 2 content is derived from `reference_documents/core-gpt-image-2-prompt-guide-library.md`,
 *    which synthesizes official OpenAI guidance with Fal's GPT Image 2 guide.
 *  - Other model guides are general prompting practice, marked `sourced: false`, and should be
 *    treated as starting points rather than vendor-verified specifications.
 *
 * This library is intentionally static and Git-tracked. It is the stable, human-curated
 * counterpart to the `video_production_skills` table, which grows automatically from
 * tutorial ingestion.
 */

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

/** How reliably a style holds identity/geometry across frames when used as a video reference. */
export type ContinuityStrength = 'strong' | 'medium' | 'weak';

export interface StyleTile {
    id: number;
    slug: string;
    name: string;
    /** Two-line descriptor shown on the tile face. */
    descriptor: string;
    /** Copy-ready snippet appended to the Style block of a prompt. */
    snippet: string;
    bestUses: string[];
    continuity: ContinuityStrength;
    /** Tailwind classes producing a visual signature for the tile face. */
    swatch: string;
    /** Accent colour used for the tile number badge and selection ring. */
    accent: string;
}

export interface PromptStructure {
    slug: string;
    name: string;
    summary: string;
    template: string;
    /** When this structure is the right one to reach for. */
    whenToUse: string[];
    notes?: string;
}

export interface PromptExample {
    title: string;
    prompt: string;
    /** Marks prompts especially suited to AI-video reference generation. */
    continuityAnchor?: boolean;
}

export interface PromptCategory {
    slug: string;
    name: string;
    icon: string;
    summary: string;
    guidance: string[];
    template?: string;
    examples: PromptExample[];
}

export interface ModelGuide {
    slug: string;
    name: string;
    vendor: string;
    kind: 'image' | 'video' | 'audio';
    /** True when content traces to the reference document; false for general practice. */
    sourced: boolean;
    summary: string;
    strengths: string[];
    settings?: { label: string; value: string }[];
    syntax: { label: string; detail: string }[];
    doThis: string[];
    avoidThis: string[];
    examples: PromptExample[];
}

export interface ReferencePack {
    slug: string;
    name: string;
    contents: string[];
    why: string;
}

export interface TipGroup {
    kind: 'do' | 'avoid';
    title: string;
    items: string[];
}

/* ------------------------------------------------------------------ */
/* Style tiles                                                         */
/* ------------------------------------------------------------------ */

/**
 * 24 selectable style tiles. Snippets for the 12 styles covered by the reference
 * document use its exact wording; the remainder follow the same "visual facts,
 * not praise words" convention.
 */
export const STYLE_TILES: StyleTile[] = [
    {
        id: 1,
        slug: 'photorealistic',
        name: 'Photorealistic',
        descriptor: 'Realistic Lighting & Texture',
        snippet: 'photorealistic, natural lighting, realistic materials, subtle film grain',
        bestUses: ['Editorial', 'Portraits', 'Product', 'Cinematic frames'],
        continuity: 'strong',
        swatch: 'bg-gradient-to-br from-slate-400 via-slate-600 to-slate-800',
        accent: 'text-slate-300',
    },
    {
        id: 2,
        slug: 'oil-painting',
        name: 'Oil Painting',
        descriptor: 'Rich Brushstrokes & Canvas Texture',
        snippet: 'oil painting, visible impasto brushwork, canvas weave texture, layered pigment, warm varnish tone',
        bestUses: ['Fine-art stills', 'Portraiture', 'Classical scenes'],
        continuity: 'weak',
        swatch: 'bg-gradient-to-br from-amber-700 via-orange-800 to-stone-900',
        accent: 'text-amber-300',
    },
    {
        id: 3,
        slug: 'watercolor',
        name: 'Watercolor',
        descriptor: 'Fluid Washes & Paper Grain',
        snippet: 'watercolor illustration, soft edges, visible paper texture, gentle color transitions',
        bestUses: ['Storybooks', 'Concept art', 'Mood pieces'],
        continuity: 'weak',
        swatch: 'bg-gradient-to-br from-sky-200 via-rose-200 to-amber-100',
        accent: 'text-sky-700',
    },
    {
        id: 4,
        slug: 'anime',
        name: 'Anime',
        descriptor: 'Clean Lines & Expressive Style',
        snippet: 'anime style, clean cel shading, crisp line work, bold flat color areas',
        bestUses: ['Characters', 'Key art', 'Stylized frames'],
        continuity: 'medium',
        swatch: 'bg-gradient-to-br from-sky-400 via-blue-500 to-emerald-400',
        accent: 'text-sky-200',
    },
    {
        id: 5,
        slug: 'blueprint',
        name: 'Blueprint',
        descriptor: 'Technical Lines & Precision',
        snippet: 'technical blueprint, white linework on blue background, orthographic view, precise labels',
        bestUses: ['Schematics', 'Exploded views', 'Instructional visuals'],
        continuity: 'strong',
        swatch: 'bg-gradient-to-br from-blue-800 via-blue-900 to-indigo-950',
        accent: 'text-blue-300',
    },
    {
        id: 6,
        slug: 'isometric',
        name: 'Isometric',
        descriptor: '3D Angles & Depth',
        snippet: 'isometric 3D illustration, fixed-angle perspective, soft global illumination',
        bestUses: ['Layouts', 'Apps', 'City scenes', 'Diagrams'],
        continuity: 'strong',
        swatch: 'bg-gradient-to-br from-stone-300 via-amber-200 to-stone-400',
        accent: 'text-stone-700',
    },
    {
        id: 7,
        slug: 'pixel-art',
        name: 'Pixel Art',
        descriptor: 'Retro Charm & Limited Palette',
        snippet: '16-bit pixel art, crisp pixels, limited palette, retro game aesthetic',
        bestUses: ['Retro scenes', 'Gaming', 'Stylized posters'],
        continuity: 'medium',
        swatch: 'bg-gradient-to-br from-indigo-400 via-purple-500 to-pink-400',
        accent: 'text-indigo-200',
    },
    {
        id: 8,
        slug: 'voxel',
        name: 'Voxel',
        descriptor: 'Blocky Worlds & 3D Pixels',
        snippet: 'voxel art, block-built 3D forms, playful lighting, game-like geometry',
        bestUses: ['Worldbuilding', 'Game concepts', 'Toy-like scenes'],
        continuity: 'medium',
        swatch: 'bg-gradient-to-br from-lime-400 via-emerald-500 to-teal-600',
        accent: 'text-lime-200',
    },
    {
        id: 9,
        slug: 'minimalist',
        name: 'Minimalist',
        descriptor: 'Simplicity & Clarity',
        snippet: 'minimalist composition, neutral background, generous negative space, clear subject hierarchy',
        bestUses: ['Ads', 'Product', 'Layouts', 'Clean posters'],
        continuity: 'strong',
        swatch: 'bg-gradient-to-br from-neutral-100 via-neutral-200 to-neutral-400',
        accent: 'text-neutral-600',
    },
    {
        id: 10,
        slug: 'line-art',
        name: 'Line Art',
        descriptor: 'Pure Lines & Contour',
        snippet: 'clean line art, uniform stroke weight, no fill, high contrast contour drawing on white',
        bestUses: ['Icons', 'Editorial spot art', 'Coloring layouts'],
        continuity: 'strong',
        swatch: 'bg-gradient-to-br from-white via-neutral-100 to-neutral-300',
        accent: 'text-neutral-700',
    },
    {
        id: 11,
        slug: 'charcoal',
        name: 'Charcoal',
        descriptor: 'Depth, Smudge & Texture',
        snippet: 'charcoal drawing, smudged tonal gradients, visible paper tooth, deep blacks, hand-drawn edges',
        bestUses: ['Portrait studies', 'Moody figures', 'Concept sketches'],
        continuity: 'weak',
        swatch: 'bg-gradient-to-br from-neutral-300 via-neutral-600 to-neutral-900',
        accent: 'text-neutral-300',
    },
    {
        id: 12,
        slug: 'noir',
        name: 'Noir',
        descriptor: 'High Contrast & Mood',
        snippet: 'film noir lighting, strong contrast, deep shadow, moody monochrome or restrained color',
        bestUses: ['Crime visuals', 'Moody portraits', 'Cinematic stills'],
        continuity: 'medium',
        swatch: 'bg-gradient-to-br from-neutral-700 via-neutral-900 to-black',
        accent: 'text-neutral-400',
    },
    {
        id: 13,
        slug: 'cyberpunk',
        name: 'Cyberpunk',
        descriptor: 'Neon Lights & Dystopia',
        snippet: 'neon-lit cyberpunk city, wet reflections, dense signage, magenta and teal accents',
        bestUses: ['Futuristic scenes', 'Concept frames', 'Posters'],
        continuity: 'medium',
        swatch: 'bg-gradient-to-br from-fuchsia-600 via-purple-800 to-cyan-600',
        accent: 'text-fuchsia-300',
    },
    {
        id: 14,
        slug: 'synthwave',
        name: 'Synthwave',
        descriptor: 'Retro Future & Glow',
        snippet: 'synthwave aesthetic, horizon grid, gradient sunset bands, chrome highlights, magenta and cyan glow',
        bestUses: ['Music visuals', 'Title cards', 'Retro-future promos'],
        continuity: 'medium',
        swatch: 'bg-gradient-to-br from-orange-400 via-pink-600 to-indigo-900',
        accent: 'text-pink-200',
    },
    {
        id: 15,
        slug: 'steampunk',
        name: 'Steampunk',
        descriptor: 'Gears, Brass & Victorian',
        snippet: 'steampunk design, brass and copper fittings, exposed gearwork, riveted panels, Victorian silhouette',
        bestUses: ['Prop design', 'Character worlds', 'Alt-history scenes'],
        continuity: 'medium',
        swatch: 'bg-gradient-to-br from-amber-600 via-yellow-800 to-stone-800',
        accent: 'text-amber-200',
    },
    {
        id: 16,
        slug: 'fantasy',
        name: 'Fantasy',
        descriptor: 'Epic Worlds & Magic',
        snippet: 'epic fantasy illustration, atmospheric scale, dramatic landscape, cinematic light',
        bestUses: ['Characters', 'Worlds', 'Book covers'],
        continuity: 'weak',
        swatch: 'bg-gradient-to-br from-emerald-700 via-teal-900 to-slate-900',
        accent: 'text-emerald-300',
    },
    {
        id: 17,
        slug: 'surreal',
        name: 'Surreal',
        descriptor: 'Dreamlike & Abstract',
        snippet: 'surrealist composition, impossible scale relationships, dreamlike juxtaposition, soft uncanny lighting',
        bestUses: ['Ideation', 'Album art', 'Editorial concepts'],
        continuity: 'weak',
        swatch: 'bg-gradient-to-br from-stone-200 via-amber-300 to-sky-400',
        accent: 'text-stone-700',
    },
    {
        id: 18,
        slug: 'pop-art',
        name: 'Pop Art',
        descriptor: 'Bold Dots & Vibrant',
        snippet: 'pop art style, halftone dot shading, heavy black outlines, flat primary color blocks',
        bestUses: ['Campaign graphics', 'Merch', 'Bold posters'],
        continuity: 'weak',
        swatch: 'bg-gradient-to-br from-yellow-400 via-red-500 to-blue-600',
        accent: 'text-yellow-200',
    },
    {
        id: 19,
        slug: 'typography',
        name: 'Typography',
        descriptor: 'Letters as Art & Layout',
        snippet: 'typographic composition, letterforms as primary subject, deliberate kerning and hierarchy, high-contrast layout',
        bestUses: ['Title cards', 'Editorial covers', 'Lyric frames'],
        continuity: 'medium',
        swatch: 'bg-gradient-to-br from-neutral-50 via-neutral-200 to-neutral-500',
        accent: 'text-neutral-800',
    },
    {
        id: 20,
        slug: 'data-viz',
        name: 'Data Viz',
        descriptor: 'Information & Beautiful',
        snippet: 'clean dashboard or infographic layout, legible charts, modern UI hierarchy, crisp labels',
        bestUses: ['UI screens', 'Dashboards', 'Explainers'],
        continuity: 'strong',
        swatch: 'bg-gradient-to-br from-slate-800 via-slate-900 to-orange-900',
        accent: 'text-orange-300',
    },
    {
        id: 21,
        slug: 'infographic',
        name: 'Infographic',
        descriptor: 'Structured Info & Clear',
        snippet: 'flat educational infographic, consistent icon style, labeled process flow, generous white space, restrained palette',
        bestUses: ['Training handouts', 'Explainer slides', 'Process diagrams'],
        continuity: 'strong',
        swatch: 'bg-gradient-to-br from-white via-sky-100 to-emerald-200',
        accent: 'text-sky-700',
    },
    {
        id: 22,
        slug: 'ui-ux-mockup',
        name: 'UI/UX Mockup',
        descriptor: 'Interfaces & Interaction',
        snippet: 'clean modern UI mockup, crisp typography, defined layout regions, real legible copy, generous spacing',
        bestUses: ['Product screenshots', 'App concepts', 'Landing visuals'],
        continuity: 'strong',
        swatch: 'bg-gradient-to-br from-slate-900 via-slate-800 to-teal-800',
        accent: 'text-teal-300',
    },
    {
        id: 23,
        slug: 'fashion-sketch',
        name: 'Fashion Sketch',
        descriptor: 'Design Lines & Elegance',
        snippet: 'fashion illustration sketch, elongated croquis proportions, loose confident linework, selective fabric rendering',
        bestUses: ['Wardrobe design', 'Lookbooks', 'Costume references'],
        continuity: 'medium',
        swatch: 'bg-gradient-to-br from-neutral-100 via-rose-100 to-neutral-300',
        accent: 'text-rose-700',
    },
    {
        id: 24,
        slug: 'architectural',
        name: 'Architectural',
        descriptor: 'Structures & Spaces',
        snippet: 'architectural visualization, accurate perspective, material-honest surfaces, controlled daylight, clean structural lines',
        bestUses: ['Building exteriors', 'Interiors', 'Environment plates'],
        continuity: 'strong',
        swatch: 'bg-gradient-to-br from-stone-200 via-stone-400 to-slate-700',
        accent: 'text-stone-300',
    },
];

export const CONTINUITY_NOTE =
    'Photorealistic, Minimalist, Blueprint, Isometric and Architectural outputs give the strongest continuity anchors because they hold form, lighting and geometry stable. Surreal, heavily painterly and highly abstract styles are excellent for ideation but drift more once converted to motion.';

/* ------------------------------------------------------------------ */
/* Universal prompt structures                                         */
/* ------------------------------------------------------------------ */

export const PROMPT_STRUCTURES: PromptStructure[] = [
    {
        slug: 'standard',
        name: 'Standard template',
        summary:
            'The master structure. Merges OpenAI’s recommended prompt order with Fal’s five-slot method, splitting Action and Style into their own blocks for reuse across editorial, product, diagram and video-reference work.',
        whenToUse: [
            'Any first-pass generation from scratch',
            'Editorial stills, posters, concept art, product scenes',
            'Character sheets, diagrams and UI mockups',
        ],
        template: `Scene:
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
[no watermark / no logos / no extra text / preserve face / preserve layout / exact text only]`,
        notes:
            'Stating the intended artifact in the Use case block tells the model what kind of thing it is making and how much polish to apply. This is one of the highest-leverage lines in the prompt.',
    },
    {
        slug: 'continuity-locks',
        name: 'Continuity locks extension',
        summary:
            'Appended to the standard template when the still will feed a downstream AI video system. Locks identity, wardrobe, palette, geometry, lens feel and lighting before motion is introduced.',
        whenToUse: [
            'Generating reference stills for AI video',
            'Building a character, environment or prop pack',
            'Any prompt round that must not drift from an anchor keyframe',
        ],
        template: `Continuity locks:
[preserve exact facial features, hair silhouette, outfit design, accessory placement,
background geometry, lighting direction, camera height, lens feel, and color palette]`,
        notes:
            'This block is what turns a general image prompt into a production reference prompt. For video-reference work it matters more than stylistic flourish.',
    },
    {
        slug: 'edit',
        name: 'Edit template',
        summary:
            'For surgical single-attribute changes to an existing image. Three parts: define the change, define the preserve list, then define realism and cleanup constraints.',
        whenToUse: [
            'Outfit, weather, object removal, background cleanup, relighting',
            'Any change where the rest of the frame must stay identical',
            'Iterating one variable at a time across a sequence',
        ],
        template: `Change:
[exactly what should change]

Preserve:
[face, identity, pose, lighting, framing, background, geometry, text, layout]

Constraints:
[no extra objects, no redesign, no logo drift, no watermark]`,
        notes:
            'Repeat the preserve list every round rather than assuming the model remembers what mattered last time.',
    },
    {
        slug: 'composite',
        name: 'Multi-image composite template',
        summary:
            'For compositing, virtual try-on, style transfer and reference blending. Each input image is labelled by role so the model never has to infer which image supplies what.',
        whenToUse: [
            'Combining subject, wardrobe, prop and environment references',
            'Virtual try-on and style transfer',
            'Building a keyframe from a pack of established references',
        ],
        template: `Image 1: base scene to preserve.
Image 2: subject or identity reference.
Image 3: outfit or prop reference.
Image 4: style or lighting reference.

Instruction:
[combine the desired elements]
Preserve [identity / background / camera angle / scale / lighting] from Image 1.
Do not add extra accessories, objects, or text.`,
        notes:
            'GPT Image family edit workflows support up to 16 reference images. Label every one of them — role assignment is not inferred reliably.',
    },
];

/* ------------------------------------------------------------------ */
/* Prompt library by category                                          */
/* ------------------------------------------------------------------ */

export const PROMPT_CATEGORIES: PromptCategory[] = [
    {
        slug: 'character',
        name: 'Character Portraits & Turnarounds',
        icon: 'User',
        summary:
            'Identity markers, clothing, expression range and proportion rules defined so the character can be re-used across storyboards, comics and video reference packs.',
        guidance: [
            'Define identity markers explicitly — face shape, hair silhouette, build, wardrobe construction',
            'Use a neutral backdrop so nothing competes with the identity read',
            'Generate front, 3/4 and side views from the same locked description',
            'State "no redesign between views" as a hard constraint',
        ],
        template: `Scene:
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
No redesign between views, preserve proportions, no text, no watermark.`,
        examples: [
            {
                title: 'Photoreal continuity sheet',
                continuityAnchor: true,
                prompt: `Scene:
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
No extra props, no jewelry, no text, no watermark.`,
            },
            {
                title: 'Storybook character anchor',
                continuityAnchor: true,
                prompt: `Scene:
Simple forest clearing with soft daylight.

Subject:
A young forest helper wearing a green hooded tunic, soft brown boots, and a small belt pouch.

Action:
Standing calmly and looking slightly toward the viewer.

Important details:
Kind expression, gentle eyes, warm but brave personality, hand-painted watercolor look,
earthy palette, soft outlines, slightly oversized storybook proportions.

Style:
Children's book watercolor illustration.

Use case:
Character anchor image for a multi-scene story and AI video reference pack.

Continuity locks:
Preserve same face, tunic design, proportions, and color palette in all later versions.

Constraints:
No text, no watermark, no redesign.`,
            },
        ],
    },
    {
        slug: 'environment',
        name: 'Environment Plates & Establishing Shots',
        icon: 'Mountain',
        summary:
            'Time, atmosphere, scale and foreground-to-background structure specified so every later shot belongs to the same world.',
        guidance: [
            'Specify time of day and weather as physical facts, not mood words',
            'Describe foreground, midground and background separately',
            'Lock the lens feel and lighting logic so subsequent shots match',
            'Name what must NOT appear — people, vehicles, signage drift',
        ],
        examples: [
            {
                title: 'Blue-hour mountain village',
                continuityAnchor: true,
                prompt: `Scene:
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
No people, no vehicles, no signage drift, no text, no watermark.`,
            },
        ],
    },
    {
        slug: 'storyboard',
        name: 'Storyboard Keyframes',
        icon: 'Layers',
        summary:
            'Narrative beats rather than generic image concepts. Action, camera angle and emotional clarity matter more than visual excess.',
        guidance: [
            'Describe the beat — what just happened and what is about to happen',
            'Name the camera position and framing explicitly',
            'Keep emotional read legible at thumbnail size',
            'Resist decorative detail that will not survive into motion',
        ],
        examples: [
            {
                title: 'Dawn diner arrival',
                prompt: `Scene:
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
No stylized grading, no extra people, no text, no watermark.`,
            },
        ],
    },
    {
        slug: 'product',
        name: 'Product Shots & Marketing Stills',
        icon: 'Package',
        summary:
            'Material accuracy, lighting control, packaging fidelity and clean composition. Written as mini creative briefs with clear audience, mood, layout and text constraints.',
        guidance: [
            'Name the actual material — matte kraft paper, brushed aluminium, frosted glass',
            'Specify the light source and its direction',
            'State depth-of-field intent explicitly',
            'Require label text to stay sharp and legible as a constraint',
        ],
        examples: [
            {
                title: 'Lifestyle coffee hero',
                prompt: `Scene:
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
no watermark.`,
            },
            {
                title: 'Readable billboard mockup',
                prompt: `Scene:
Roadside billboard at sunset.

Subject:
A shampoo campaign billboard.

Action:
Static advertising mockup.

Important details:
Product bottle on the right, generous negative space on the left,
headline rendered once as exact text: "Fresh and clean," bold sans-serif typography,
high contrast, readable from a distance.

Style:
Photorealistic outdoor advertising mockup.

Use case:
Marketing concept frame.

Constraints:
Render text verbatim, no extra words, no duplicate text, no extra logos, no watermark.`,
            },
        ],
    },
    {
        slug: 'ui',
        name: 'UI Screens & Dashboards',
        icon: 'LayoutDashboard',
        summary:
            'Structured visuals where hierarchy, layout, real copy and readability constraints are defined directly. One of GPT Image 2’s strongest categories.',
        guidance: [
            'Name the screen type — dashboard, onboarding, analytics panel',
            'Quote the exact label text you want rendered',
            'Describe layout regions: nav rail, top bar, content area, panels',
            'Ban lorem ipsum and fake logos explicitly',
        ],
        template: `Scene:
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
No lorem ipsum, no fake logos, no illegible widgets, no watermark.`,
        examples: [
            {
                title: 'Fleet management dashboard',
                prompt: `Scene:
Desktop SaaS analytics product.

Subject:
A fleet management dashboard.

Action:
Static logged-in dashboard overview screen.

Important details:
Left navigation rail with icons, top bar with search and account menu,
main content area with KPI cards, a live map panel on the left, a trips table on the right,
teal accent color on a deep navy interface, legible labels reading "Vehicles," "Trips," "Alerts," and "Fuel Usage,"
clean chart hierarchy, generous spacing, crisp modern sans-serif typography.

Style:
Clean UI screenshot.

Use case:
Marketing screenshot for a software landing page.

Constraints:
No lorem ipsum, no brand theft, no extra modal windows, no watermark.`,
            },
            {
                title: 'Mobile onboarding screen',
                prompt: `Scene:
Vertical mobile app interface.

Subject:
An onboarding screen for a fictional app called NESTING.

Action:
Static welcome screen.

Important details:
Headline "WELCOME TO NESTING," supporting line "A quieter way to gather people around a table,"
buttons "Get started" and "I already have an account," small line illustration of three plates and two wine glasses,
warm cream background, coral primary button, rounded sans-serif typography.

Style:
Clean mobile UI mockup.

Use case:
App concept and marketing screenshot.

Constraints:
Exact readable copy, no watermark, no real app branding.`,
            },
        ],
    },
    {
        slug: 'infographic',
        name: 'Infographics & Educational Visuals',
        icon: 'PieChart',
        summary:
            'Instructional artifact specs rather than generic illustration requests. Denser layouts and labels benefit from higher quality settings.',
        guidance: [
            'Describe the information flow direction — left-to-right, top-down, radial',
            'List every label that must appear, by name',
            'Require consistent icon style across the whole graphic',
            'Ban decorative stock-photo elements and tiny labels',
        ],
        examples: [
            {
                title: 'Solar irrigation explainer',
                prompt: `Scene:
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
No clutter, no tiny labels, no decorative stock-photo elements, no watermark.`,
            },
        ],
    },
    {
        slug: 'technical',
        name: 'Technical Diagrams & Blueprints',
        icon: 'Ruler',
        summary:
            'Diagram type, view angle, label strategy and precision expectations defined up front. Blueprint and isometric approaches constrain the visual language tightly.',
        guidance: [
            'State the projection — orthographic, top-down isometric, exploded view',
            'Name every zone or component label explicitly',
            'Specify a restrained palette to keep linework readable',
            'Ban decorative icons and text artifacts',
        ],
        examples: [
            {
                title: 'Hangar layout diagram',
                prompt: `Scene:
Neutral white background.

Subject:
An aircraft maintenance hangar layout.

Action:
Static technical overview.

Important details:
Top-down isometric view with clearly separated zones labeled "Receiving," "Inspection," "Repair Bays,"
"Parts Storage," and "Quality Control," precise linework, restrained gray-blue-orange palette,
clean vector-like labels and arrows.

Style:
Isometric technical diagram.

Use case:
Operations explainer for training materials.

Constraints:
No decorative icons, no watermark, no text artifacts, no extra zones.`,
            },
        ],
    },
    {
        slug: 'ads',
        name: 'Ads & Poster Concepts',
        icon: 'Megaphone',
        summary:
            'Audience, culture, composition and exact copy included so the model can interpret art direction within clear bounds.',
        guidance: [
            'Name the audience and the cultural register',
            'Specify where the subject sits and where negative space goes',
            'Quote the tagline and state it must render once',
            'Ban unrelated logos and extra text',
        ],
        examples: [
            {
                title: 'Streetwear rooftop campaign',
                prompt: `Scene:
Urban rooftop gathering at twilight.

Subject:
A small group of friends wearing a fictional youth streetwear brand.

Action:
They are laughing together in a candid fashion-campaign moment.

Important details:
Premium fashion-photography feel, clean composition, natural body language,
strong warm-versus-cool color direction, exact tagline "Yours to Create" rendered once,
clear ad hierarchy with subject grouping on the right and negative space on the left.

Style:
Polished contemporary campaign photography.

Use case:
Streetwear ad concept.

Constraints:
No unrelated logos, no extra text, no watermark.`,
            },
            {
                title: 'Photoreal editorial still',
                prompt: `Scene:
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
No commercial styling, no watermark, no logos.`,
            },
        ],
    },
    {
        slug: 'edits',
        name: 'Edit Patterns',
        icon: 'Wand2',
        summary:
            'Concise, surgical, repeatable edits. Change, then preserve list, then realism constraints — one variable per round.',
        guidance: [
            'Change exactly one thing per round',
            'Restate the full preserve list every single time',
            'Describe the physical repair needed — reconstruct the hand, rebuild the reflection',
            'Ban ghosting, drift and added objects',
        ],
        examples: [
            {
                title: 'Object removal',
                prompt: `Change:
Remove the flower from the man's hand.

Preserve:
Face, clothing, pose, camera angle, lighting, background, and all other objects exactly.

Constraints:
Reconstruct the hand naturally, no ghosting, no added objects, no watermark.`,
            },
            {
                title: 'Outfit change',
                prompt: `Change:
Replace only the clothing with a dark olive waxed jacket, charcoal trousers, and brown leather boots.

Preserve:
Face, skin tone, body shape, hands, hair, expression, pose, background, camera angle, framing,
and original lighting exactly.

Constraints:
Fit garments naturally with realistic folds and shadows, no jewelry, no text, no logos.`,
            },
            {
                title: 'Weather transformation',
                prompt: `Change:
Make the scene look like a winter evening with light snowfall.

Preserve:
Identity, geometry, camera angle, object placement, signs, buildings, and composition.

Constraints:
Adjust only weather, ambient light, and surface wetness, no new objects, no watermark.`,
            },
            {
                title: 'Background cleanup',
                prompt: `Change:
Remove every advertising poster from the shop windows.

Preserve:
Awning, brick facade, window mullions, sidewalk reflections, every person, camera framing, and color balance.

Constraints:
Reconstruct glass reflections naturally, no adhesive marks, no logo drift, no watermark.`,
            },
        ],
    },
];

/* ------------------------------------------------------------------ */
/* Reference packs for AI video                                        */
/* ------------------------------------------------------------------ */

export const REFERENCE_PACKS: ReferencePack[] = [
    {
        slug: 'character-pack',
        name: 'Character pack',
        contents: ['Front view', '3/4 view', 'Side view', 'Expression sheet', 'Full-body outfit view'],
        why: 'Locks identity, proportions and wardrobe for later animation.',
    },
    {
        slug: 'environment-pack',
        name: 'Environment pack',
        contents: ['Wide establishing shot', 'Medium framing', 'Detail shot', 'Lighting reference'],
        why: 'Stabilizes world design, atmosphere and light logic.',
    },
    {
        slug: 'prop-pack',
        name: 'Prop pack',
        contents: ['Hero object', 'Close-up material detail', 'Context-in-use shot'],
        why: 'Preserves object design and material behaviour across scenes.',
    },
    {
        slug: 'anchor-keyframe',
        name: 'Anchor keyframe',
        contents: ['A single gold-standard still defining ideal composition, grading and mood'],
        why: 'Serves as the baseline for all later edits and motion translations.',
    },
];

export const REFERENCE_RULES: string[] = [
    'State the role of each input image explicitly.',
    'Separate "change" instructions from "preserve" instructions.',
    'Use a continuity lock list in every prompt round to reduce drift.',
    'Keep one variable changing at a time: identity, then wardrobe, then background, then lighting.',
    'Reuse one master keyframe as the anchor image for all future edits.',
];

export const REFERENCE_EXAMPLE = `Image 1: character identity reference.
Image 2: outfit reference.
Image 3: environment lighting reference.

Instruction:
Create a photorealistic full-body keyframe of the same woman from Image 1 wearing the outfit from Image 2 in the environment mood of Image 3.

Continuity locks:
Preserve exact facial structure, hair silhouette, body proportions, outfit construction, skin tone,
camera height, 50mm lens feel, and soft side-light direction.

Constraints:
No extra accessories, no text, no logos, no watermark.`;

/* ------------------------------------------------------------------ */
/* Model guides                                                        */
/* ------------------------------------------------------------------ */

export const MODEL_GUIDES: ModelGuide[] = [
    {
        slug: 'gpt-image-2',
        name: 'GPT Image 2',
        vendor: 'OpenAI',
        kind: 'image',
        sourced: true,
        summary:
            'OpenAI positions gpt-image-2 as the default image model for new builds: high-fidelity photorealism, reliable text rendering, complex structured visuals, strong style control and robust identity preservation across edits and multi-step workflows.',
        strengths: [
            'Photorealism and realistic material behaviour',
            'Reliable in-image text rendering',
            'Structured visuals — infographics, diagrams, UI',
            'Identity-sensitive edits and compositing',
            'Fewer retries on complex briefs',
        ],
        settings: [
            { label: 'Default model', value: 'gpt-image-2 is the recommended default for new workflows' },
            {
                label: 'Quality',
                value: 'low for speed; medium and high for dense text, close-up portraits, high-resolution output and identity-sensitive edits',
            },
            {
                label: 'Resolution',
                value: 'Outputs must respect edge, ratio and pixel-count constraints. Above 2560×1440 should be treated as variable or experimental.',
            },
            { label: 'Reference images', value: 'Up to 16 reference images supported in edit workflows' },
        ],
        syntax: [
            {
                label: 'Prompt order',
                detail: 'Scene → Subject → Action → Important details → Style → Use case → Constraints. Stable ordering outperforms adjective piles.',
            },
            {
                label: 'Artifact declaration',
                detail: 'Name the thing being made — editorial photo, UI screen, infographic, concept frame, billboard, character sheet.',
            },
            {
                label: 'Text handling',
                detail: 'Treat in-image text as typography, not mood. Quote the exact string, specify placement, font feel, contrast, and that it renders once.',
            },
            {
                label: 'Preserve lists',
                detail: 'Explicit preservation instructions on every edit round: preserve face, preserve layout, change only the background.',
            },
        ],
        doThis: [
            'Put the main subject near the start of the prompt',
            'Use explicit camera and framing language — "eye-level medium shot", "wide establishing frame"',
            'Describe materials, wear, texture and physical realism directly',
            'Quote exact text and specify it must appear once, verbatim, with no extra words',
            'Repeat the preserve list every edit round',
            'Change one variable at a time and keep an anchor keyframe constant',
        ],
        avoidThis: [
            'Praise words — "stunning", "masterpiece", "epic"',
            'Style piles without visual anchors — "minimalist brutalist editorial luxury modern premium"',
            'Multi-change edit prompts asking for better text, better outfit and better background in one pass',
            'Implicit preserve rules — if identity or layout must hold, say so',
        ],
        examples: [
            {
                title: 'Identity-preserving composite',
                continuityAnchor: true,
                prompt: `Image 1: character identity reference.
Image 2: outfit reference.
Image 3: environment lighting reference.

Instruction:
Create a photorealistic full-body keyframe of the same woman from Image 1 wearing the outfit from Image 2 in the environment mood of Image 3.

Continuity locks:
Preserve exact facial structure, hair silhouette, body proportions, outfit construction, skin tone,
camera height, 50mm lens feel, and soft side-light direction.

Constraints:
No extra accessories, no text, no logos, no watermark.`,
            },
        ],
    },
    {
        slug: 'nano-banana-pro',
        name: 'Nano Banana Pro',
        vendor: 'Google',
        kind: 'image',
        sourced: false,
        summary:
            'The current default image model in this pipeline. Strong at photorealistic scenes and character consistency when given explicit reference framing. General practice below — not vendor-verified.',
        strengths: ['Photoreal scenes', 'Character consistency with references', 'Fast iteration'],
        syntax: [
            {
                label: 'Structure',
                detail: 'The universal Scene / Subject / Action / Details / Style structure transfers cleanly. Keep it.',
            },
            {
                label: 'References',
                detail: 'Describe what the reference supplies rather than assuming the model infers it.',
            },
        ],
        doThis: [
            'Reuse the standard template unchanged — structure transfers across image models',
            'Lead with subject and framing',
            'State lighting direction as a physical fact',
        ],
        avoidThis: ['Vendor-specific parameter syntax borrowed from other tools', 'Vague aesthetic stacking'],
        examples: [],
    },
    {
        slug: 'midjourney',
        name: 'Midjourney',
        vendor: 'Midjourney',
        kind: 'image',
        sourced: false,
        summary:
            'Parameter-driven image model with a distinct aesthetic default. General practice below — not vendor-verified.',
        strengths: ['Strong stylistic defaults', 'Aspect and stylization parameters', 'Fast exploration'],
        syntax: [
            { label: 'Aspect ratio', detail: '--ar <w>:<h> controls framing.' },
            { label: 'Stylization', detail: '--s <n> trades prompt adherence against house aesthetic.' },
            { label: 'References', detail: 'Image URLs placed at the start of the prompt act as visual references.' },
        ],
        doThis: [
            'Front-load the subject before parameters',
            'Lower stylization when you need literal prompt adherence',
            'Keep prompts shorter than the GPT Image 2 structure — this model rewards density',
        ],
        avoidThis: ['Long prose blocks', 'Contradictory style terms in one prompt'],
        examples: [],
    },
    {
        slug: 'kling-3',
        name: 'Kling 3',
        vendor: 'Kuaishou',
        kind: 'video',
        sourced: false,
        summary:
            'The current default video model in this pipeline. Image-to-video with camera motion control. General practice below — not vendor-verified.',
        strengths: ['Image-to-video fidelity', 'Camera motion control', 'Coherent short clips'],
        syntax: [
            {
                label: 'Motion description',
                detail: 'Describe camera movement and subject movement separately — "slow dolly in, subject remains still".',
            },
            {
                label: 'Start frame',
                detail: 'The reference still carries identity and grading. Prompt only the motion delta from it.',
            },
        ],
        doThis: [
            'Feed a locked anchor keyframe generated with continuity locks',
            'Describe one clear motion per clip',
            'Say "still" or "no movement" when you want a clean hold for frame extraction',
        ],
        avoidThis: [
            'Re-describing everything already present in the start frame',
            'Multiple simultaneous camera moves in one clip',
        ],
        examples: [],
    },
    {
        slug: 'seedance-2',
        name: 'Seedance 2.0',
        vendor: 'ByteDance',
        kind: 'video',
        sourced: false,
        summary:
            'Video model that responds well to numbered multi-shot prompts — the basis of the multi-shot storyboard extraction skill already in this repo. General practice below.',
        strengths: ['Multi-shot sequences in one generation', 'Consistency across shots', 'Frame-extractable holds'],
        syntax: [
            {
                label: 'Numbered shots',
                detail: 'Bracketed numbers define discrete camera positions within one clip: [1] wide, [2] slight left angle, [3] close-up.',
            },
            {
                label: 'Hold instruction',
                detail: 'Appending "still" to each numbered shot produces clean freeze frames for extraction.',
            },
        ],
        doThis: [
            'Number each camera angle explicitly',
            'Add "still" per shot when extracting storyboard frames',
            'Condition on a single reference image so all shots share grading',
        ],
        avoidThis: ['Unnumbered multi-angle descriptions', 'Motion instructions when you want extractable stills'],
        examples: [
            {
                title: 'Multi-shot coverage from one reference',
                prompt: `[1] Wide living room shot, subject centered on the couch, completely still. [2] Slight left angle, natural sitting posture, still. [3] Slight right angle, relaxed pose with room depth, still. [4] Close-up of face, soft expression and ambient light, still. [5] Extreme close-up of eyes, reflecting the room, still. [6] Hands resting on lap, no movement, still. [7] Low angle from floor level, couch and posture emphasized, still.`,
            },
        ],
    },
    {
        slug: 'suno',
        name: 'Suno',
        vendor: 'Suno',
        kind: 'audio',
        sourced: false,
        summary:
            'Music generation from style prompts and lyrics. General practice below — not vendor-verified.',
        strengths: ['Full-song structure', 'Genre fidelity', 'Lyric-driven generation'],
        syntax: [
            {
                label: 'Style prompt',
                detail: 'Genre, instrumentation, tempo and production era as comma-separated facts.',
            },
            { label: 'Structure tags', detail: '[Verse], [Chorus], [Bridge] and [Outro] shape the arrangement.' },
        ],
        doThis: [
            'Name instrumentation and tempo concretely',
            'Use structure tags to control arrangement length',
            'Specify production era for tonal consistency',
        ],
        avoidThis: ['Mood-only prompts with no instrumentation', 'Over-long style strings'],
        examples: [],
    },
];

/* ------------------------------------------------------------------ */
/* Tips                                                                */
/* ------------------------------------------------------------------ */

export const TIP_GROUPS: TipGroup[] = [
    {
        kind: 'do',
        title: 'What to do',
        items: [
            'Put the main subject near the start of the prompt.',
            'Use explicit camera and framing language such as "eye-level medium shot" or "wide establishing frame."',
            'Describe materials, wear, texture and physical realism directly.',
            'Quote exact text and specify that it must appear once, verbatim, with no extra words.',
            'For edits, repeat the preserve list every round rather than assuming the model remembers what matters.',
            'For video-reference work, change one variable at a time and keep one anchor keyframe constant.',
        ],
    },
    {
        kind: 'avoid',
        title: 'What to avoid',
        items: [
            'Vague praise words such as "stunning," "masterpiece," or "epic."',
            'Style piles without visual anchors, such as "minimalist brutalist editorial luxury modern premium."',
            'Multi-change edit prompts that ask for better text, better outfit, better background and preserved everything in one pass.',
            'Implicit preserve rules — if identity, layout or brand assets must remain stable, state it directly.',
        ],
    },
];

export const CORE_PREMISE =
    'GPT Image 2 performs best when prompts behave like creative briefs rather than vague descriptions. Prompts should not only describe how an image should look, but explicitly define what must remain stable across iterations.';

export const ANTI_SLOP_NOTE =
    'The most common failure mode is not model weakness but prompt vagueness: creators describe taste while omitting structure, geometry and preservation rules.';

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

/** Assemble a filled prompt from the standard template plus an optional style snippet. */
export function assemblePrompt(fields: {
    scene?: string;
    subject?: string;
    action?: string;
    details?: string;
    style?: string;
    useCase?: string;
    constraints?: string;
    continuityLocks?: string;
}): string {
    const blocks: string[] = [];
    const push = (label: string, value?: string) => {
        if (value && value.trim()) blocks.push(`${label}:\n${value.trim()}`);
    };

    push('Scene', fields.scene);
    push('Subject', fields.subject);
    push('Action', fields.action);
    push('Important details', fields.details);
    push('Style', fields.style);
    push('Use case', fields.useCase);
    push('Continuity locks', fields.continuityLocks);
    push('Constraints', fields.constraints);

    return blocks.join('\n\n');
}

export const CONTINUITY_BADGE: Record<ContinuityStrength, { label: string; classes: string }> = {
    strong: { label: 'Strong anchor', classes: 'bg-green-500/15 text-green-400 border-green-500/25' },
    medium: { label: 'Medium anchor', classes: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25' },
    weak: { label: 'Weak anchor', classes: 'bg-orange-500/15 text-orange-400 border-orange-500/25' },
};
