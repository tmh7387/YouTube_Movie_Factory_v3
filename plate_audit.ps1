$root='C:\Users\Admin\Dropbox\YTMF\Amara_2026\Press_On\Clip_Package_v2'
$out='D:\App development\YouTube_Movie_Factory_v3\plate_audit_20260921'
New-Item -ItemType Directory -Path $out -Force | Out-Null
$envIds=@(23,28,29,31,32,36,41,43,46,47,49,50,53,54,71,72,74)
$stageIds=@(33,35,51,55,57,60,62)
$reuseIds=@(16,19,22,27,40,42,58,63)
$rows=@(Get-ChildItem $root -Directory | Where-Object Name -Match '^\d' | ForEach-Object {Get-ChildItem $_.FullName -Directory} | ForEach-Object {
 $d=$_; $m=Get-Content (Join-Path $d.FullName 'clip_manifest.json') -Raw | ConvertFrom-Json
 $n=[int]([regex]::Match($d.Name,'^seg(\d+)').Groups[1].Value)
 $images=@(Get-ChildItem $d.FullName -File -Recurse | Where-Object Extension -Match '^\.(png|jpeg|jpg|webp)$')
 $status='NOT FILED'; $next='Select/create shot-specific photographic plate; check existing project assets before generating.'
 if($envIds -contains $n){$status='ENVIRONMENT ONLY';$next='Existing photographic environment visually checked; add Amara/action and required shot framing.'}
 if($stageIds -contains $n){$status='USER HAS REFERENCE';$next='User said stage references exist and will be added. Import/select; do not regenerate by default.'}
 if($reuseIds -contains $n){$status='DERIVE / REUSE';$next='No local plate. Derive from approved boarding/train coverage or suitable finished frame; confirm shot-specific continuity.'}
 switch($n){
 15 {$status='TEST PLATES';$next='Existing photographic boarding test plates/takes; verify current wardrobe and geometry before promoting.'}
 17 {$status='APPROVED IN CHAT';$next='candidate_2_masked_face_v1.png approved in conversation; promote to canonical scene reference and record approval.'}
 20 {$status='SELECTED PLATE';$next='scene_ref.png present with Amara; selected in manifest. Reconcile against latest approved Higgsfield element if needed.'}
 30 {$status='APPROVED IN CHAT';$next='Latest bedroom_low_angle_base_face_v2.png accepted with Good in conversation; stored in _production/old_me_reference_review, not scene folder.'}
 48 {$status='DERIVE / REUSE';$next='Create closed-suitcase state from approved seg30 scene or its finished video end frame.'}
 61 {$status='CANDIDATE / EDIT CHOICE';$next='Dining-table candidates exist in Downloads; current manifest says seated on bed. Decide replacement versus original before assigning.'}
 64 {$status='ENVIRONMENT CANDIDATES';$next='Three photographic coastal train views present; select intended overlook view and resolve character requirement.'}
 69 {$status='SHOT MISMATCH';$next='scene_ref shows seated dark-outfit coastal overlook, while manifest calls for cream-outfit dawn performance. Confirm intended edit or create matching plate.'}
 }
 if(@(34,52,65) -contains $n){$status='BUILD NEXT';$next='Street Piazza: existing 3D layout and wardrobe source; no photographic plate found in scene folder. Build master then alternate coverage.'}
 if(@(56,77) -contains $n){$next='Old Me apartment exit plate not filed; bedroom and dining images do not cover departure.'}
 if($n -eq 10){$next='Legacy Platform 9 folder name conflicts with prior no-platform-number-sign instruction. Resolve intended insert before producing.'}
 if($n -eq 19){$next='Legacy right_turn folder name; user corrected route to LEFT and planned a cut to corridor. Confirm shot retained; do not create right-turn coverage.'}
 [pscustomobject]@{Segment=('seg{0:D2}' -f $n);Section=$m.section;Scene=$m.source_name;Setup=$m.setup_group;FilmStart=$m.film_start_tc;FilmEnd=$m.film_end_tc;Status=$status;NextAction=$next;Folder=$d.FullName;ImageCount=$images.Count;SelectedReference=$m.selected_scene_reference;ImageFiles=($images.FullName -join ' | ')}
} | Sort-Object Segment)
$rows | Export-Csv (Join-Path $out 'SCENE_PLATE_INVENTORY.csv') -NoTypeInformation -Encoding utf8
$lines=@('# Press On - photographic plate inventory','', 'Audit: 21 September 2026. Scope: all 81 Clip_Package_v2 scene folders, recursive image files, clip manifests, reference manifests sampled, recent conversation approvals and known external reference locations. Canonical scene images visually reviewed as a contact sheet. This is a plate inventory, not a video-render completion audit. Empty folders do not prove artwork is absent from Higgsfield or elsewhere. No scene manifests changed.','', '## Key findings','', '- Street Piazza is the recommended next new setup: seg34, seg52 and seg65 have no local photographic plate. Existing 19_Street_Piazza_Asset contains 3D layout, camera/blocking and street-wardrobe.png. Reuse those design decisions.','- Most scene_ref images are empty train environments. They are not finished character-in-scene plates.','- seg17 boarding and seg30 Old Me have approval in chat but are not filed as canonical scene references.','- Stage references were reported by the user as already available; import rather than rebuild.','- seg69 currently contains a dark-outfit seated coastal image, inconsistent with its cream-outfit dawn-performance manifest.','- seg19 retains the obsolete right-turn name; continuity is LEFT. seg10 retains Platform 9 naming; resolve against the no-number-sign instruction.','', '## Status counts','')
$rows | Group-Object Status | Sort-Object Name | ForEach-Object {$lines += ('- {0}: {1}' -f $_.Name,$_.Count)}
$lines+=@('','## Piazza coverage','', '| Scene | Film timecode (30 fps) | Edit duration | Required coverage |','|---|---|---|---|','| seg34 | 01:22:03-01:24:04 | 2.03s | Chorus 1 stepping motif |','| seg52 | 02:20:25-02:23:02 | 2.23s | Chorus 2 alternate stepping coverage |','| seg65 | 02:42:00-02:44:10 | 2.33s | Bridge traveling steps/turn/open arms |','', 'These are editorial durations, not generation settings. Build a full-body photographic master with feet and floor visible; derive alternate framing only after approval. Preserve the existing 3D piazza layout and street wardrobe.','', '## All scenes','', '| Segment | Setup | Plate status | Next action |','|---|---|---|---|')
foreach($r in $rows){$lines += ('| {0} | {1} | {2} | {3} |' -f $r.Segment,$r.Setup,$r.Status,$r.NextAction)}
$lines | Set-Content (Join-Path $out 'PLATE_INVENTORY.md') -Encoding utf8
$rows | Group-Object Status | Select-Object Name,Count
'TOTAL: '+$rows.Count
