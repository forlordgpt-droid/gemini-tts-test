# Automatic Recovery Policy — Owner's Latest Instruction (17 November 2026)

The user has explicitly superseded the earlier instruction to halt on every technical failure: **from now on, diagnose and fix recoverable failures automatically instead of stopping after each one.**

For this Hunyuan 02:00–02:30 production, automatically:
1. Inspect actual GitHub Actions job failures and logs; identify the failing operation and root cause.
2. Repair GitHub Actions configuration, dependency versions, exact-framework integration bugs, file layouts, browser/codec flags, scene timing, actual animation, QA and audio muxing **using only the originally specified tool families**.
3. Commit small reproducible patches on the existing working branch, re-run the affected validation checks, and inspect the results. Reuse all previously generated approved image and narration assets, avoiding credit-consuming duplicate calls.
4. Preserve the original Hunyuan 2D art.js and engine.js, Three.js PerspectiveCamera, GSAP, SVG/Canvas2D, OfflineAudioContext, WebCodecs/Mediabunny, FFmpeg/FFprobe and Playwright; no silent substitution.
5. Verify actual 1920×1080, 30fps, 30-second 900-frame output corresponding only to story time 02:00–02:30, plus visible depth motion, character performance, layered scenic art and sound. Store finished verified MP4 and sources in connected Google Drive.

**Non-negotiable safety and spending controls:** The previously authorized production contains *exactly four* existing SnapGen `gpt-image-2.5-lower` 16:9 images (4 credits already spent) and *at most two* KIE `google/gemini-3-8-flash-lite-tts` narration jobs (Fola), with a maximum total of 5 credits across both services. No automatic paid retries, regeneration of usable narration, model substitution, or payment beyond the cap. Pause only when a fix requires owner authorization, unsupported access, unsafe action, or a fundamentally unavailable mandated tool despite valid attempts. Technical fixes themselves do not require repeated approval.

**Avoid duplicate KIE charges on multiple GitHub workflow reruns:** Only trigger a workflow containing paid TTS after verifying that the authorized two paid jobs have not already run. If prior paid voice jobs succeeded, reuse the existing KIE WAV artifacts. If only one paid job succeeded, never regenerate that job; preserve its output and run at most the one not-yet-generated clip. The GitHub `voice` job must always depend on successful native rig, browser encode and all three 10-second sharded video tests.

Current implementation workflow: `.github/workflows/hunyuan-0200-0230.yml` on branch `hunyuan-0200-0230-v21-preproduction`. Keep failures and fixes auditable through commit messages and the GitHub Actions run history.
