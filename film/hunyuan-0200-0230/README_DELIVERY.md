# Hunyuan — Bunker Survival, source excerpt 02:00–02:30

## Locked scope and delivered result
- Source story time: **02:00 inclusive to 02:30 exclusive**, no material after 02:30.
- Actual duration: **30.000s**, **900 frames**, **1920 × 1080**, **30 fps**, **16:9**.
- Codec: H.264 AVC video + 24kHz mono AAC voice/foley.
- Verified Google Drive MP4: https://drive.google.com/file/d/1A5dCoY6XcQNbPDjIoTgiwMgbGBi32EIv/view?usp=drivesdk
- Original user-provided 2D Hunyuan character package and native engine preserved. No GLB or photorealistic character replacement.

## What is inside the delivered source ZIP
- Original `HUNYUAN_2D_CHARACTER_PACKAGE.zip`, plus `public/rig/art.js` and `public/rig/engine.js` extracted *unchanged* for the browser.
- Four approved premium SnapGen GPT Image 2.5 Lower 16:9 countryside illustrations in `public/assets`, with provenance in `IMAGE_ASSET_MANIFEST.json`.
- Real deterministic Three.js 2.5D perspective planes, original-rig SVG actor performance, GSAP camera tracks and Canvas2D story graphics: `movie.js`.
- `package.json`, `index.html`, `playwright-render.cjs` and project config, art direction and shot plans.
- Both original KIE.ai `google/gemini-3-8-flash-lite-tts` / Fola WAVs, their zero-charge existing task IDs, validated 30s speech master and original OfflineAudioContext foley.
- Final playable MP4, quality evidence and contact sheets.
- `prepare_audio_repaired.py` for fitting the approved recording into precisely 30 seconds using *only removal of measured low-amplitude silence*. No words are cut or tempo/pitch changed.

## Reproducible development
Use Node.js 22 and Ubuntu 24.04 with Playwright Chromium. Inside this folder, `npm install --no-audit --no-fund` installs the exactly pinned Three.js, GSAP, Mediabunny, Playwright and licensed Fontsource packages; `npx playwright install --with-deps chromium` installs the browser; `npm run build` builds the movie app. The movie's existing Playwright browser test renders a deterministic 10s video shard when `SHARD_INDEX` is 0, 1, or 2. FFmpeg / FFprobe join and validate the completed shards.

Fonts are package-managed; font binaries are not redistributed as standalone files in this source ZIP. The finished video contains rasterized typesetting.

## Mandatory stack and paid generation history
- Hunyuan `art.js`/`engine.js`; Three.js PerspectiveCamera; paused GSAP; SVG/Canvas2D; WebAudio OfflineAudioContext; WebCodecs/Mediabunny; FFmpeg/FFprobe; Playwright. No renderer or paid-model substitution.
- 4 SnapGen `gpt-image-2.5-lower` illustrations consumed 4 image credits, as previously authorized.
- Exactly 2 KIE Fola TTS tasks were previously created: `73a3af873fb9eeb935d7335e6bb5a1ad`, `be36a266dd54291568fc8717ee66ff73`. Every recovery used existing task IDs; **do not submit another paid generation**.
- The original GH video run generated all 900 frames on 3 GitHub public CPU runners, 300 frames each; corrected finishing uses only the original KIE WAVs and FFmpeg mux/join.

## QA and limitations
- Vite, Chromium, original rig tests, WebCodecs/Mediabunny and 5s full-resolution engineer gate passed; three 300-frame video shards passed FFprobe independently.
- Full MP4 passed whole-file decode, exact 900-frame H.264/30fps/1080p verification, AAC audio track, 30.000 second duration, and non-clipping audio peak analysis.
- Normal-speed artistic movement, proper glove-over-eyes gesture and typography were sampled visually; an independent subjective listening review is not certified by those tests. Review that by playing the delivered MP4.
- Source art is an authored 2D illustration backdrop (not photorealistic) with composited near/mid/far camera-depth layers.

This folder is for review/continuation; no paid keys are embedded in any project file.
