# Log — new entries from the 2026-08-19 ingest

Append these to the vault's `wiki/log.md`.

## [2026-08-19] ingest | the cheat codes to prompting for true realism with Seedance 2.5 (free claude skills)
- Source: https://www.youtube.com/watch?v=5dWgZDka3Ww
- Channel: JOEY (CTRL / noisygroup)
- Pages created: 10 — YT_JOEY_Seedance_25_Realism_Cheat_Codes, Technique_Scene_Plate_First,
  Technique_Spatial_Geometry_Lock, Technique_Prompt_Top_Loading,
  Technique_Extend_Video_Continuation, BP_Anti_Plastic_Realism, Tool_Seedance_2_5,
  Tool_Seedream_5_0_Pro, Tool_Nano_Banana_Pro, Tool_Joey_Cinema_Director_Skills
- Pages updated: 0 (de-duplication against the vault was not possible — see README.md)
- Key topics: Seedance 2.5 capabilities and prompt structure; scene-plate-first workflow;
  spatial geometry consistency without pinning a start frame; the "plastic look" and its
  causes; extend-video continuation driven by LLM frame analysis; real credit costs
  (~800 credits ≈ $32 for a one-minute project); the Cinema Director v3 / banana-pro-director /
  character-builder skill set.

## [2026-08-19] ingest | How I Made a 1-Minute AI Film With Only 2 Prompts (Full Workflow + Prompts)
- Source: https://www.youtube.com/watch?v=OFD9blyx204
- Channel: GenAI with Keera
- Pages created: 4 — YT_GenAIwithKeera_1min_AI_Film_2_Prompts,
  Technique_Build_A_Prompting_Skill_From_Vendor_Docs,
  Technique_Storyboard_Before_Video_Credits, BP_Working_Around_Model_Content_Filters
- Pages updated: 1 — Tool_Seedance_2_5 (added as second source)
- Key topics: building a Seedance 2.5 prompting skill by analysing the vendor's worked
  examples rather than summarising the guide; storyboard image as a cheap direction gate
  before spending video credits; two 30-second generations assembled into a one-minute
  film; working around reference-image copyright moderation by moving wardrobe into the
  text channel.

### Ingest exceptions
- `raw/youtube/*.json` written to this staging folder, not the vault.
- `wiki/ingest_manifest.json` not updated — requires the vault's current contents.
- Transcripts came from YouTube auto-captions via a server-side scrape, not the `/watch`
  Whisper pass; proper nouns were normalised by hand.
