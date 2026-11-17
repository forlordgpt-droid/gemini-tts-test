# Bunker Survival — Hunyuan 2D, first 120 seconds

**State:** original-rig 8-second illustrated scene and voiced preview verified on GitHub Actions; the full 120-second film remains unrendered.

## Locked output
- 1920 × 1080; 30fps; 16:9; exactly 3,600 frames covering [0,120) seconds.
- Original Hunyuan native vector rig. No photorealism, static cutout actor substitution or volumetric 3D.
- Three.js PerspectiveCamera + GSAP absolute-time camera tracks + original art.js/engine.js actor animation.
- Browser WebCodecs + Mediabunny, backed by FFmpeg/FFprobe QA, Playwright browser QA.
- KIE.ai `google/gemini-3-8-flash-lite-tts` exclusively for newly generated narration; key through Actions secret `KIE_API_KEY`.
- Multi-runner GitHub Actions can parallelize background work, audio generation, tests and sharded export, conditional on verified available codecs.
- Strict stop on required-tool failure. No fallback toolchain without user approval.

## Available source files
- `PROJECT_CONFIG.json`: strict project constraints
- `STORY_BEATS.json`: ordered initial edit beats

## Original source and narration transfers completed
- Original user-provided 1,005,362-byte `HUNYUAN_2D_CHARACTER_PACKAGE.zip` committed unchanged from the connected private Google Drive, as a Git blob.
- Original package integrity and all native engine tests passed: [Rig validation #43974412127](https://github.com/forlordgpt-droid/gemini-tts-test/actions/runs/43974412127).
- Six authentic KIE.ai Gemini 3.8 Flash-Lite narration jobs succeeded: [Voice run #43974639785](https://github.com/forlordgpt-droid/gemini-tts-test/actions/runs/43974639785).
- The six WAV files totaled 129.00 seconds. A 120.00-second AAC master was made by reducing silence stretches, preserving voiced samples, and validated with FFprobe. The audio master is committed at `audio/BUNKER_FIRST_120S_NARRATION.m4a`.
- Eight-second artwork/rig/Three.js/GSAP/Mediabunny representative scene source is committed as `HUNYUAN_SCENE_TEST_SOURCE.zip`; the first visual validation run must pass before the 120-second film proceeds.

## Existing validation
[GitHub Actions required-stack preflight #43971438743](https://github.com/forlordgpt-droid/gemini-tts-test/actions/runs/43971438743) passed all four jobs, including WebCodecs H.264 encoding at 1920×1080 in a secure local Chromium context.

**Production is not yet finished.** The 8-second technical scene gate passed on [run #44017410107](https://github.com/forlordgpt-droid/gemini-tts-test/actions/runs/44017410107): 1920x1080/30, 240 frames, native rig, Three.js/GSAP, Mediabunny, FFmpeg/FFprobe and AAC. A verified voiced preview was uploaded to [Google Drive](https://drive.google.com/file/d/11ZQieloeImGWpeVEzw2Gxh6ebmM-YVMv/view). This is a technical representative scene, **not** the final story-accurate or visually approved 120-second film; full-scene production and export remain pending.
