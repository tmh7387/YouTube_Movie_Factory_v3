# Asset Locking Techniques

Added 2026-07-15. Sourced from two Higgsfield AI Cinema Studio production tutorials:
- "3-Step Workflow To Make Ultra-Realistic AI Ads" (2026-06-23) + `higgsfield.ai/blog/cinematic_headphones`
- "How to Make Ultra Realistic AI Short Films Using Seedance 2.0 in 4K" (2026-07-07) + `higgsfield.ai/blog/Santiago-breakdown`

Full ingest detail lives in the Content_Intelligence wiki page `Technique_Cinema_Studio_Director_Techniques.md`.

---

## Named-asset convention (Elements-style)

Give every locked reference (character, prop, location) the exact same name as the
`@tag` used to call it in prompts. If the generation platform has a saved-asset
library — Higgsfield's **Elements** panel is the observed example — save the asset
under that exact name. Matching names let the platform auto-attach the correct
reference image at generation time instead of manually re-uploading per shot/panel.

## Face-erase trick

If a character reference sheet's full-body panel accidentally shows a second or
duplicate face (a common artifact when generating multi-view sheets), run a quick
edit pass: "erase the face from the full-body shot on the [left/right] panel." This
leaves exactly one face for the video model to lock onto. Run the same fix on every
character sheet that shows more than one figure or angle in frame — not just the
hero.

## Wet/dry (state) variant sheets

When a character's appearance changes partway through a project — dry to
sweat-soaked after exertion, clean to dirty after a fight, uninjured to injured —
generate a **second, separately locked** reference sheet for that state rather than
describing the change in the action/panel text. Keeps identity from drifting when
the state changes on camera; the model has an actual reference for the "after" look
instead of having to infer it.

## Ghost-mannequin garment sheets

Generate wardrobe/kit props as garment-only, invisible-mannequin shots: no body, no
face, no skin visible — just the clothing holding a natural worn silhouette, as if
on an implied form. This lets the same garment asset be recombined onto any
character sheet later (via an image-edit step, e.g. "put this character in this
uniform") without smuggling an unwanted face or body into the reference.

## Schematic / top-down prop-position lock

When a prop's exact position and scale in a location matters and needs to hold
across every panel or shot, generate a plain top-down schematic image and describe
the placement relative to a fixed landmark: "lock the [prop] to the [landmark]'s
right, roughly twice a person's height, on the same line." Text position
descriptions alone drift across generations; a diagram reference doesn't.

## Empty-location generation

Generate crowd- or clutter-heavy locations (stadiums, busy streets) **empty** as
the base asset. Add crowds, extras, and clutter later from the scene/panel prompt
text rather than baking them into the reusable location reference — keeps the
location asset clean and reusable across scenes with different crowd states.

## Single-appearance characters don't need a sheet

A character who appears only once across the whole project (a background extra, a
one-line walk-on) can be described directly in the panel/scene prompt with no
dedicated reference sheet. Reserve full asset-locking for anyone who recurs.
