# HUNYUAN CINEMATIC PRODUCTION ENGINE V3 — START HERE

**This is a reusable production environment, not a new art style.** The original, user-approved Hunyuan 30-second illustrated movie is the artistic baseline. The latest mandatory instructions and original audited blueprint have been copied into `authoritative/` byte-for-byte unchanged (SHA256-locked). Read both **before** making ANY video.

## Mandatory sources and hierarchy

1. [MANDATORY_CINEMATIC_ANIMATION_INSTRUCTIONS.txt](authoritative/MANDATORY_CINEMATIC_ANIMATION_INSTRUCTIONS.txt) — exact uploaded user directive, **unchanged**.
2. [HUNYUAN_30S_CINEMATIC_REPLICATION_BLUEPRINT.txt](authoritative/HUNYUAN_30S_CINEMATIC_REPLICATION_BLUEPRINT.txt) — original verified Hunyuan 30s production method, **unchanged**.
3. [AGENTS.md](AGENTS.md) — how other LLMs must use these two instructions.
4. [LOCKED_MODELS_AND_GATES.json](config/LOCKED_MODELS_AND_GATES.json) — machine-checkable models/tools, spending approval and creative review gates.
5. Reference source from commit `716740ba4fb50b2d0c1ff3f033973d34a0209b34`:
   - `film/hunyuan-2m/HUNYUAN_30S_PARALLAX_SOURCE.zip`
   - `film/hunyuan-2m/HUNYUAN_2D_CHARACTER_PACKAGE.zip`
   - THE ORIGINAL 30s `HUNYUAN_FIRST_30S_PARALLAX_PREVIEW.mp4` obtained from successful [GitHub Actions #44029412483](https://github.com/forlordgpt-droid/gemini-tts-test/actions/runs/44029412483) and **embedded inside the published Docker image**.
6. [APPROVED_ORIGINAL_30S_REFERENCE_STORY.json](examples/APPROVED_ORIGINAL_30S_REFERENCE_STORY.json) — original six-shot camera and film style mapping, as a REFERENCE ONLY, not reusable generic bedroom scenes.

### Model lock

**SnapGen `gpt-image-2.5-lower`** for approved paid artwork. **Kie.ai `google/gemini-3-8-flash-tts`** for approved paid speech. Hunyuan animation must use ORIGINAL `art.js` + `engine.js` native 2D rig selectively. PerspectiveCamera uses geometric depth only; human characters remain 2D illustrated. No vendor/model/library substitutions. No paid API call from the environment or its automatic tests.

The historical Hunyuan blueprint mentions *Flash-Lite* because it records which existing voice track was reused in that original 30s demonstration. That is NOT permission to change the current user-mandated *Flash* model.

## Prebuilt runner (no installation on each video shard)

Image: `ghcr.io/forlordgpt-droid/hunyuan-cinematic-engine:v3.0.0-locked`

Built by [GitHub Actions environment workflow](../../.github/workflows/hunyuan-v3-environment.yml) from a Node 22 base, with:
- Three.js **0.187.0**, GSAP **3.15.1**, Mediabunny **1.66.0**, Playwright **1.65.1**, esbuild **0.25.12**;
- matching preinstalled Chromium + WebCodecs + WebGL2 + OfflineAudioContext browser APIs;
- Pillow, OpenCV and NumPy, FFmpeg/FFprobe, modern font fallback packages;
- the actual original 30s MP4, six illustrated scene compositions, 12 independent depth layers and original native 2D Hunyuan character rig; and
- precompiled, **local-timestamp WebCodecs video exporter**, preventing frozen footage across shard joins.

Run the prebuilt image (GitHub Actions use `container:` with package auth; locally `docker login ghcr.io` if private):

```bash
docker pull ghcr.io/forlordgpt-droid/hunyuan-cinematic-engine:v3.0.0-locked
docker run --rm --ipc=host ghcr.io/forlordgpt-droid/hunyuan-cinematic-engine:v3.0.0-locked
```

This executes the mandatory reference/model/rig checks. The version can also be pinned by the exact container digest from the successful `IMAGE_DIGEST.txt` GitHub Actions artifact.

**Caching advantage:** No `pip install`, `npm install`, `npx playwright install` or `apt-get` in individual render shards. Each new GitHub-hosted runner still downloads the container image if not cached; we measure cold-pull cost rather than promising instant startup.

## New story workflow, including 15-minute films

The automation is explicitly designed to retain the beautiful image-first, deeply illustrated cinematography.

1. Give the LLM your *complete real story*. The LLM must read `AGENTS.md`, both original locked instruction files, and watch the actual approved MP4.
2. Create a new narrative-specific visual style bible, reference character sheets, shot-by-shot storyboarding, rich color script, camera map, dialogue timing, sound score and contextual graphics. The approved Hunyuan bedroom is NOT a template to reuse for unrelated stories.
3. Before requesting any paid SnapGen/Kie generation, show the user exact model, number of tasks, expected cost EACH and hard maximum. Obtain explicit approval. **All spending is disabled by default.**
4. Create illustration-first 2D images, author real foreground/actor/mid/background planes with Pillow+OpenCV, and preserve all completed source assets. Never simply duplicate one flattened PNG as three planes.
5. Author a project-specific `main.js` and `index.html` derived from the proven original `preview_30s/main.js`. Keep `window.renderFrame(absoluteStorySeconds)` deterministic and expose `window.ready=true`. Do not replace it with a generic slide renderer.
6. Make a project manifest following `examples/APPROVED_ORIGINAL_30S_REFERENCE_STORY.json`. Use `examples/UNFINISHED_15MIN_STORY_STARTER.json` as a NOT-READY planning skeleton, never as publishable film footage.
7. `scripts/orchestrator.py validate --manifest path/to/story.json --phase first10`; then `plan` creates absolute-frame non-overlapping shard jobs. A 15-minute film at 30fps has 27,000 frames; 10-second chunks yield **90 chunks**, with only as many active public GitHub CPUs as concurrency permits.
8. **FIRST GATE:** Make 10 seconds of uncorrected draft actual video and get explicit visual approval, then **SECOND GATE:** first 30 seconds for approval. Only then render remaining minutes. Both gates remain mandatory.
9. `scripts/render_shard.cjs` uses the pinned image, actual Three.js/GSAP scene code and `temporal_export.js`. Three.js samples ABSOLUTE story time; WebCodecs `CanvasSource.add()` uses LOCAL `f/30` time for each shard. This is the **fix** for the frozen-film problem.
10. `scripts/assemble_shards.py` checks every source chunk's 0-based PTS and codec, uses FFmpeg to concat and mix already-authorized synchronized SFX and narration. `scripts/qa_video.py` decodes actual output and checks for frozen frames.
11. Watch the final actual MP4 at normal speed (not only code or screenshots), correct any imperfect layers and artistic mismatches with the same exact tools, then save the final video, source, QC, checksum ledger and art to Google Drive.

### Exact commands inside the prebuilt container

```bash
python3 /opt/cinematic/engine/scripts/doctor.py --check
python3 /opt/cinematic/engine/scripts/orchestrator.py validate --manifest /project/story.json --phase first10
python3 /opt/cinematic/engine/scripts/orchestrator.py plan --manifest /project/story.json --phase first10 --shard-seconds 10 --max-parallel 8 --out /project/build/first10_plan.json
node /opt/cinematic/engine/scripts/render_shard.cjs --project /project/scenes --start-frame 0 --frame-count 300 --out /project/build/chunks
python3 /opt/cinematic/engine/scripts/assemble_shards.py --plan /project/build/first10_plan.json --chunks-dir /project/build/chunks --approved-audio /project/audio/preapproved_mix.wav --out /project/build/FIRST_10S.mp4 --qc-dir /project/build/qc
```

In GitHub Actions the driver workflow applies this across multiple independent CPU runners automatically. The project-specific `main.js` still must meet every visual requirement of the original instructions, and approved real artwork/dialogue must be provided before rendering.

### Reference integrity (SHA256)

| Original file | SHA256 |
|---|---|
| User cinematic blueprint TXT | `5a00372da9b55f29123c452ad17299471163ee71a6940cd704e76750b577465e` |
| User mandatory cinematic directive TXT | `3567254c70db3a7fef7c2f6406cd3b96dba862c75c1c484f8d41060487255da2` |
| Original approved MP4 | `f1aa6abf0c89b972ba842f7398561830d12b4e12599cd2fbde82dd11ace7f1e0` |
| Original Hunyuan 2D rig ZIP | `f75c7d8fefc6fb1885acc16e8513380a891e0d59c32471e5f9458eda04767630` |
| Original 2.5D source ZIP | `2c507e35a989ab373a4ba343ff9aa5308eb02b5aaa500ddba61c11d92c803ae1` |

The build fails if any byte of these references changes. It cannot silently accept a flattened/photorealistic/3D version in place of the original.

## Important: visual standards are not a package-installation feature

A prebuilt container speeds up repeated startup, but cannot generate visually excellent story-specific art by itself. Your LLM is still responsible for original visual storytelling, actor staging, sound, camera choreography and strict human review. A passing Docker test is **technical**, not creative approval.

Never substitute a cheaper tool or a 3D human to accelerate rendering. **The film must look like a professional illustrated cinematic movie, not a basic 2D character animation.**
