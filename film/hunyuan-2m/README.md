# Bunker Survival — Hunyuan 2D, first 120 seconds

**State:** production manifests authored; **not yet renderable on GitHub**.

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

## Required missing input on runners
The original file `HUNYUAN_2D_CHARACTER_PACKAGE.zip` exists in ChatGPT Library, **not in this GitHub repository**. ChatGPT Library paths cannot be fetched by GitHub-hosted Actions. The connector's text file/Blob APIs don't accept a local container path or `file_id` as content; source bytes must be explicitly transferred to the repository or another runner-accessible authorized location. Do not replace the original rig.

The source zip is available in the current working environment. Its verified engine includes `README.md`, `API.md`, `art.js`, `engine.js`, `assets/RIG.json`, six directional SVGs and existing tests. Once the exact original archive is made runner-accessible, implement the production adapter and assets and run the 5–10s internal gate before the 120s render.

## Existing validation
[GitHub Actions required-stack preflight #43971438743](https://github.com/forlordgpt-droid/gemini-tts-test/actions/runs/43971438743) passed all four jobs, including WebCodecs H.264 encoding at 1920×1080 in a secure local Chromium context.

**Do not represent the storyboard as a finished film or spend voice-generation credits before the source rig is accessible to runners.**
