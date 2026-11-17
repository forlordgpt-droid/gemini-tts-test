# THE LAST SAFE ROOM — Remaining 20 Seconds | Locked Creative Plan
## Source and approved opening
- Original screenplay: user-supplied story4.txt, first 30 seconds only.
- Locked approved 0.000–10.000s master: Google Drive file ID `1QrXAUlrgQFwdtuHKo8N1k7JcIDJpr-Lp`, GitHub Actions successful render #44104478064, artifact `LSR_10S_RAW_APPROVAL_VIDEO_AND_SOURCE`.
- Do not regenerate, revise, or regrade this opening. Join existing H264 frames with next 600 frames using FFmpeg, preserving approved picture and sound.
- Original reference: `HUNYUAN_30S_PARALLAX_SOURCE.zip`, `HUNYUAN_2D_CHARACTER_PACKAGE.zip` original `art.js`/`engine.js`, loaded and validated; do NOT depict Hunyuan as female Emma or use 3D humans.

## Mandatory visual continuation
Exactly 4 extra SnapGen `gpt-image-2.5-lower` 16:9 2D hand-illustrated story images, no different model and maximum 4 additional image credits. Match Emma's existing coral/rust-red jacket, dark brown low ponytail and hazel eyes, clean cel-brush inks, indigo/petrol-blue architecture, rich sulfur-yellow gas, emergency vermilion interiors, and premium art direction. Split each generated image into actual alpha foreground + actor midplane + repaired environment backplate via **Pillow + OpenCV**. Implement real Three.js PerspectiveCamera and GSAP deterministic timelines (not Ken Burns). Different visible parallax at distinct Z coordinates and motivated camera movement in EVERY shot. Midplanes may contain Emma as illustrated pose; original Hunyuan rig is retained/tested but not substituted.

## 10–30s beats, rhythmic edit
| Sec | Visual composition | Camera & layers | Sound/dialogue |
|---|---|---|---|
| 10.00–13.15 | City street meets old wrought-iron subway entrance; Emma races toward stairs; a man collapses behind in poisonous haze | low wide dolly/dramatic right truck past foreground car/barrier, wide street behind | Noah (phone): "Emma! The gas is moving faster. Get underground!" begins at ~10s, urgent |
| 13.15–15.00 | Powerful snap/foreground iron-railing wipe into descending subway doorway; gas overtakes a parked car | forward/dolly down, sign post independent, separate near/between/deep planes | footsteps accelerate, breath, faint gas hiss |
| 15.00–19.25 | Emma plunges down station stairs, emergency scarlet lamps flash over tiling; stairs have clear disappearing geometry | tracking camera from above left, railing near front, Emma middle, station ceiling/tunnel deep; light sweep | running footfalls, reverb changes outdoor to enclosed, humming hazard LEDs |
| 19.25–22.65 | Emma grasps and pulls locked iron security gate, alarm red; phone held near ear | purposeful fast push to locking mechanism then hold reaction, bars foreground, face & hands midplane, vast station behind | gate rattling; Emma: "Noah! It's locked!" |
| 22.65–26.35 | Emma pivots, revealing the long dark service tunnel behind her under red emergency strip lights | motivated truck & over-shoulder reveal through near gate, far perspective recedes slowly | Noah (phone): "There's an emergency tunnel behind you!" |
| 26.35–30.00 | Menacing corridor vanishing point and Emma turning to stare; black depth, warning light pulses | low creep toward obscured dark door; near dangling wires/pipes rush by, dark arch far, camera settles on terrifying void | heavy metallic banging in increasingly fast/near pulses; no extra invented dialogue |

No arbitrary repeated flat zooms. Meaningful SVG/Canvas2D kinetic overlays for incoming call, emergency lights, metal impact ripples, depth-specific yellow gas; brief editorial labels only. The last beat ends with encroaching metallic bangs on a visual cliffhanger exactly at 30.00s.

## Dialogue TTS / cost barrier
User approved the additional four images (~4 SnapGen credits) and authorized TTS in principle, but requires exact cost confirmation separately. Kie.ai **Gemini 3.8 Flash TTS** is `google/gemini-3-8-flash-tts` (NOT Flash-Lite); as checked 2026-11-17, published price is 70 credits / 1M input tokens and 1,260 credits / 1M audio output tokens. Actual output tokens/total credits unknown until rendering. Do **not** generate or substitute any TTS until user explicitly approves provider, model, number of tasks and maximum billable credits. Preserve script for 3 lines, two speakers; no replacement synthetic voice model.

## Exact technical system
- 1920x1080 30fps, 900 frames total; 0–10 master reused, four 5-second 150-frame shards for 10–30; GitHub Actions parallel public CPU runners.
- Three.js PerspectiveCamera; GSAP paused absolute-time; original Hunyuan art.js/engine.js; SVG/Canvas2D; Pillow/OpenCV; Web Audio OfflineAudioContext; WebCodecs/Mediabunny; Playwright; FFmpeg/FFprobe.
- Maintain correct dialogue timing and mono phone EQ only after Kie TTS approval; render all authored SFX via OfflineAudioContext, split bands by action.
- Verify each shard 150 frames, 1080p H.264, decoded MP4 frame contact sheets and visual QA; final 30s 900 frames H264+AAC, no frozen parallax/overlays; Drive video/source/QC delivery.

**Never claim completion until final output exists and inspected.**