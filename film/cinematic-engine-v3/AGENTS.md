# AGENTS.md — REQUIRED READING FOR ALL LLMS
## Hunyuan Cinematic Production Engine V3 — DO NOT DOWNGRADE THE ARTISTIC METHOD

This file is a routing/integration guide. **It is not a replacement for either original user instruction file.**

**HIGHEST PRIORITY: Read these files IN FULL and keep them BYTE-FOR-BYTE UNCHANGED:**
1. `authoritative/MANDATORY_CINEMATIC_ANIMATION_INSTRUCTIONS.txt`
2. `authoritative/HUNYUAN_30S_CINEMATIC_REPLICATION_BLUEPRINT.txt`
3. `config/LOCKED_MODELS_AND_GATES.json`
4. The actual `HUNYUAN_FIRST_30S_PARALLAX_PREVIEW.mp4`, not only still frames or a prompt.
5. The original `HUNYUAN_30S_PARALLAX_SOURCE.zip` and `HUNYUAN_2D_CHARACTER_PACKAGE.zip`, including `HUNYUAN_2D/art.js` and `HUNYUAN_2D/engine.js`.

The original film that established the look is GitHub Actions run [#44029412483](https://github.com/forlordgpt-droid/gemini-tts-test/actions/runs/44029412483), commit `716740ba4fb50b2d0c1ff3f033973d34a0209b34`. It has 6 illustrated compositions, 12 independent layer assets, carefully choreographed Three.js+GSAP camera movement, contextual animated motion graphics, Hunyuan's authored 2D rig and sound. **Preserve the METHOD, not the bedroom/phone story content.** Different stories must have appropriate original imagery.

### Unchangeable aesthetic requirements

- **Premium illustrated, painterly 2D environments and illustrated characters.** No photorealistic footage, flat geometry-only scenes, 3D rendered character models or generic AI cutouts.
- **Image FIRST, motion second.** Images must tell each story beat and feature detailed locations, attractive lighting, foreground props, depth, visual action, expressive figures and atmospheric color.
- **True 2.5D:** original illustrator-designed foreground/midground/background and character planes at different Three.js `PerspectiveCamera` depths; independently moving foreground reveals; clean masks and inpainted overscan (Pillow + OpenCV). A uniform zoom or a static poster is a FAILURE.
- **Meaningful visible cinematography:** deliberate lateral dollies, trucks, push-ins, countertracks, tilts and foreground wipes. GSAP absolute-time determinism `t=frame/fps`; transitions timed to story and sound.
- **Living environments:** practical light, particles, steam/gas/rain where narratively appropriate, shadow movement, prop reactions, expressive character performance, and modern kinetic SVG/Canvas2D typography. Graphics communicate plot, not gratuitous decoration.
- **Editorial quality:** shot scales, color script, sound design and shot count respond to each beat, generally about 6–8 distinct shots per 30 seconds if story density warrants. Small temporary captions; do not obscure eyes/subjects.
- **The original Hunyuan rig is only for Hunyuan.** DO NOT use Hunyuan as a replacement for Emma or other unrelated characters. If Hunyuan appears, prefer original `art.js`/`engine.js` native 2D poses and animations. Do not substitute a 3D rig.
- **Real normal-speed visual QA** of actual exported video mandatory. FFprobe passing metadata alone is NOT proof of visible motion. Reject visually weak output and repair using the same exact tools.

### EXACT model and tool locks (no substitution)

- Images: **SnapGen `gpt-image-2.5-lower`** (not Nano Banana or another cost tier).
- Narration/dialogue: **Kie.ai `google/gemini-3-8-flash-tts`**, as explicitly specified in the latest mandatory instruction. Historical mentions of Flash-*Lite* in the original blueprint describe the OLD Hunyuan demonstration's existing audio, and are not permission to substitute the current production TTS model.
- Three.js PerspectiveCamera; GSAP; native Hunyuan art.js+engine.js; SVG+Canvas2D; Pillow+OpenCV; WebAudio OfflineAudioContext; WebCodecs+Mediabunny; FFmpeg+FFprobe; Playwright; parallel GitHub Actions CPUs; Google Drive for file exchange.
- A 3D character engine ZIP, if present in older project files, is **archival only** and NOT an approved 2D model replacement. No performance optimization can compromise these locks.

### User approval / spending safeguards

- The environment is completely **NO-PAID-CALL by default**.
- Before ANY image/voice/video/music/other credit-consuming request: explicit user approval of provider, exact model, quantity, estimated cost EACH, and maximum total. Existing approvals for previous stories do NOT carry over automatically.
- If an exact tool or model fails, attempt to fix it without substitution. If unfixable, STOP and disclose it; never silently use an alternative.
- Preserve existing approved art and audio. Cache completed results. Never regenerate a completed paid asset merely to fix the camera or render.

### 10 seconds, 30 seconds, then longer films

For ANY new story, including future 15-minute films:
1. Read the FULL story and all original instructions; create a detailed visual style bible and shot/audio plan.
2. Prepare an image-first **UNCORRECTED first 10-second draft** and show it for visual approval, before aesthetic retouch or further story rendering.
3. After approval, render first **COMPLETE 30-second cinematic sequence**, show actual footage for separate visual approval.
4. Only after the requested approvals produce the rest (including a 15-minute film). Reuse approved first segments EXACTLY unless the user asks for edits.
5. Keep 1920×1080, 16:9, 30fps (900 frames for 30s; **27,000 frames for 15 minutes**), H.264/AAC MP4, accurate sound, real changing frames, no frozen image sections.

These two gates are both mandatory: the latest user instruction requests the first 10s preview, and the original master instruction requires approval of the first complete 30s before the remainder.

### Production scaling / reproducibility

- Use the prebuilt GHCR image from `../.github/workflows/hunyuan-v3-environment.yml` at its SHA256 digest; never `npm install`, `pip install` or `playwright install` in each render shard.
- No 15-minute task should be run as a single 27,000-frame browser job. Create deterministic absolute-frame scene/shard manifests; plan roughly 10-second shards (90 for 15 minutes), limit active GitHub runners to actual quota, resume only failed/changed shards, and assemble normalized frame timestamps with FFmpeg.
- Store reference/master images, per-scene geometry, masks, shot metadata, all audio segments, and exact rendered chunks with content-addressed checksums and GitHub Actions artifacts plus durable Google Drive/archive storage.
- **Visual QA cannot be reduced to metadata:** test layer displacement, clipping, actual motion between timestamped samples, continuity between shards, dialogue timing, and intended camera movement at full-res NORMAL SPEED.
- Never skip visual art review for the sake of a speed target.

### If the user says "make the next film"

Do NOT ask them to reinstall anything. Read both original documents, launch `scripts/doctor.py`, verify the image and voice cost gates, and build/run a scene-specific manifest through the approved GitHub Actions workflows. Report REAL run/artifact/Drive status. Do not claim success until the required image/audio/video and QC are verified.

**ENGINEERING RULE:** Speed improvements must change installation caching, scheduling and fault recovery—not the artistic blueprint.
