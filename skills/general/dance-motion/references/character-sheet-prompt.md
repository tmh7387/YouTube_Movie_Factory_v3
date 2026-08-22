# Character Sheet Prompt

Use this exact prompt when generating the character reference sheet in
Step 1. Pass it as the `prompt` parameter to `Higgs:generate_image`
with model `gpt_image_2`.

## Prompt Text

```
Create a professional character reference sheet based strictly on the
uploaded reference image, preserving and exactly matching its existing
visual style. Do not change the realism level or rendering approach;
keep the same type of image as the reference (for example, if the
reference is 3D stylized, keep it 3D stylized; if it is photographic,
keep it photographic; if it is painterly, keep it painterly), with the
same shading, texture, color treatment, and overall aesthetic. Use a
clean, neutral plain background so the character is clear.

Arrange the sheet so that the left side contains two large full-body
panels of the character in a relaxed A-pose with accurate anatomy or
proportions and a clear silhouette: one full-body front view and one
full-body back view, with consistent scale and alignment between them.

On the right side, create four portrait panels arranged in two rows:
a front portrait with the face looking straight at the camera, a
left-side portrait (profile or three-quarter view facing left), a
right-side portrait (profile or three-quarter view facing right), and
an extreme close-up face crop that clearly shows fine facial details
such as eyes, eyelids or eyelashes, eyebrows (if present), nose,
mouth, skin or surface texture, and hair or head details.

Maintain perfect identity consistency across every panel so the
character always looks like the same individual from the reference
image. Keep the facial scale consistent across the three standard
portraits, and use even spacing and clean visual separation between
all panels. Lighting should remain consistent across the entire sheet
(same direction, intensity, and softness as in the original style),
with controlled shadows that preserve detail without dramatic mood
shifts, producing a crisp, print-ready reference sheet with sharp
details.
```

## Generation Parameters

| Parameter      | Value           |
|----------------|-----------------|
| Model          | `gpt_image_2`   |
| Aspect Ratio   | `16:9`          |
| Media Role     | `image` (attach the user's uploaded reference) |

## Quality Checks

After generation, verify:
- [ ] All 6 panels present (2 full-body + 4 portrait)
- [ ] Art style matches the source image exactly
- [ ] Identity consistent across all panels (same face, same outfit)
- [ ] Full body visible in both body panels (head to toe)
- [ ] Clean neutral background throughout
- [ ] No invented details — everything matches the reference
