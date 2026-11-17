> **USER-SELECTED MODEL OVERRIDE FOR STORY5 — KIE GEMINI 3.8 FLASH-LITE TTS (2026-11-17).**
> The user explicitly named `kie gemini 3.8 tts flash lite`, selecting Kie.ai model `google/gemini-3-8-flash-lite-tts` for the Emma story5 narration ONLY. This supersedes the previous story5 choice of `google/gemini-3-8-flash-tts`, which failed twice (task IDs remain in the history below). Do **not** rewrite any immutable original Hunyuan engine files or alter camera/illustration requirements.
> Pricing verified from Kie.ai: **70 credits / 1 million text input tokens, 840 credits / 1 million audio output tokens** (limited-time offer at 2026-11-17). Proposed **one new Lite TTS job**, estimated roughly **0.2–0.4 credits** for about 10 seconds; proposed maximum **5 credits**, but Kie.ai does not provide a verified per-request hard cap.
> **SPENDING IS STILL DISABLED:** naming/selecting Lite does not authorize a new chargeable request; both earlier task authorizations were consumed. Await explicit approval of the **new 1-job / up-to-5-credit proposal with nonenforceable provider hard cap** before calling `/createTask`. No automatic retries. Preserve story narration text verbatim and use only the approved visual assets. This story-specific model override is recorded in [`narrated-first10/FLASH_LITE_MODEL_SELECTION_NO_SPEND.json`](narrated-first10/FLASH_LITE_MODEL_SELECTION_NO_SPEND.json).
> **UPDATE — SECOND USER-APPROVED KIE TASK CONSUMED, NO CREDIT DEBIT.**
> A new explicit authorization covered exactly one retry of the same Kie.ai `google/gemini-3-8-flash-tts` single-narrator job. GitHub run [44150369902](https://github.com/forlordgpt-droid/gemini-tts-test/actions/runs/44150369902) successfully passed engine/model/secret preflight, submitted task `e023925f74d68ac373714f1ee9b78074`, but Kie returned `fail: generate task timeout.`
> Read-only audit [44150684304](https://github.com/forlordgpt-droid/gemini-tts-test/actions/runs/44150684304) confirms account balance 109.32 before and after, **0 credits debited**, and no audio recoverable from the failed task. The original and second authorization are both CONSUMED. **NO further paid TTS requests are authorized; no 10-second narrated MP4 was rendered.** Do not rerun a paid workflow, change models, or reuse story4 dialogue.
# STORY5 — NARRATION-LOCKED MASTER (AUTHORITATIVE CORRECTION)
Production: Hunyuan Cinematic Engine V3
Status: BLOCKED AFTER EXACT KIE TTS PROVIDER TIMEOUT; 1 authorized paid request consumed, ZERO credits debited according to independent read-only balance check. NO paid retries authorized. Corrected 2.5D art/camera preflight passed, narrated MP4 NOT rendered.
Kie task: `50214fd411ae5bd5c280faf60a3f809d` (failed with `generate task timeout.`). Paid run: https://github.com/forlordgpt-droid/gemini-tts-test/actions/runs/44149119360 ; read-only audit: https://github.com/forlordgpt-droid/gemini-tts-test/actions/runs/44149522287 .
Authorization consumed: a separate explicit approval is required for another paid submission. Do not create a new request from existing manifest or rerun the workflow.
Date: 2026-11-17
Original source: attached `story5.txt`
Source genre: **narrated cinematic thriller**, NOT a dialogue screenplay.

## Critical correction
The prior GitHub-run first-10-second review `44145422302`, Drive video `1s_Re7827hfz4nhVWC2bBpjGYgA9pEuRv`, is **SUPERSEDED / NOT APPROVABLE**:
- It used the earlier "Last Safe Room" screenplay beat structure.
- It contains a premature incoming-call shot at 09.15s even though the call happens near the end of scene 1 (00–15s).
- It contains NO narrative voiceover.
- Its approved image style may be reused when story-appropriate, but its sound/scene timing and previous dialogue must NOT be reused as story5 narration.
- Do not label it successfully delivered for owner approval; technical H264 success is NOT narrative compliance.

### Strict narrative mode
1. Read the actual narration text verbatim in chronological order. SCENE headings and time stamps are metadata, not spoken audio.
2. Single off-screen narrator throughout. No protagonist dialogue, no named caller dialogue, and no invented quotes. The story reports that a mysterious caller warns Emma, that a recorded message warns the safe room is a trap, and that someone whispers her name — **these are narrator-described events**, not source-provided spoken lines.
3. If diegetic whispered "Emma" is added as an optional creative effect, do not cut, replace, or overlap so heavily that the original narrator's words become unintelligible. Seek approval for any added paid speaking voice. A literal recorded message's dialogue does not exist in the source and must not be fabricated.
4. Keep all relevant atmospheric sounds and visual action under continuous narration (low enough not to mask the voice). Avoid long silent intervals except a deliberate sound moment while narration remains complete.
5. Exact model for narrator: Kie.ai `google/gemini-3-8-flash-tts`. Generate **no paid speech** unless the user first authorizes provider, model, job count, expected cost/job, maximum total, and any limits on cap enforcement.
6. No new images authorized. Reuse existing SnapGen `gpt-image-2.5-lower` story-compatible Emma source illustrations when possible; any new artwork requires separate spending approval.

## Source narration — VERBATIM, all scenes

### Scene 1 (00:00–00:15), Abandoned Street
The entire city had been evacuated. A deadly yellow gas was spreading through the streets, killing anyone who breathed it.

But Emma was still trapped.

She ran past abandoned cars, desperately searching for somewhere safe.

Then her phone rang.

### Scene 2 (00:15–00:30), Subway Station
A mysterious caller warned her to hide underground.

Emma rushed into an empty subway station, but the main gate was locked.

Suddenly, she heard heavy footsteps approaching from the darkness.

With no time to think, she escaped through a maintenance tunnel.

### Scene 3 (00:30–00:45), Underground Tunnel
Deep underground, Emma discovered a steel door marked SAFE ROOM.

She rushed inside and locked it behind her.

Something immediately slammed against the door.

Then everything went silent.

For the first time, she thought she was safe.

### Scene 4 (00:45–01:00), Emergency Bunker
But a security monitor suddenly switched on.

It showed the mysterious caller standing outside the subway.

Then a recorded message began playing.

The voice warned that the safe room was actually a trap.

Before Emma could escape, another door behind her slowly opened.

And someone whispered her name.

CUT TO BLACK.

## Time-aligned illustrated direction
Timing is a **target storyboard**, not permission to shorten, invent, or speed-cut spoken narration. Check actual TTS waveform timing and preserve every phrase before locking shot edits. If narration cannot fit comfortably, flag for user approval rather than cut sentences or change the story.

| Time | Voiceover content and visual coverage | Mandatory camera / parallax |
|---|---|---|
| 00–03.5 | "The entire city had been evacuated." — aerial/low establishing city evacuation aftermath, truly deserted streets | PerspectiveCamera lateral dolly, independently moving nearest bumper, midground abandoned cars, highly detailed far architecture |
| 03.5–07.5 | "A deadly yellow gas was spreading through the streets, killing anyone who breathed it." — toxic yellow atmospheric front advances around detailed facades and vehicles | Motivated push through segmented atmospheric front, depth-specific illuminated vapor, meaningful occlusion; no human death inserted unless source demands a visual |
| 07.5–10 | "But Emma was still trapped." — reveal Emma looking for an exit and starting to run | Low-angle fore-to-mid reveal then countertrack; foreground details, expressive Emma animation, deep parallax; NO PHONE SHOT OR RING |
| 10–15 | "She ran past abandoned cars, desperately searching for somewhere safe. Then her phone rang." — action then phone vibration at end | Fast dynamic street truck past detailed parked cars then phone close-up only on "Then her phone rang." |
| 15–30 | Source narration about unknown caller, subway, locked gate, approaching footsteps, maintenance tunnel | Narrative-driven dolly through entry, latch close-up, gate-shadow shifts, deep tunnel threatening reveal, fleeing Emma |
| 30–45 | Source narration about SAFE ROOM door, locking, impact, silence, brief relief | Foreground pipe wipes, depth-separated steel-door mechanics, controlled impact shake, stillness as contrast |
| 45–60 | Source narration about security monitor, caller, trap warning, opening door, whispered name, CUT TO BLACK | Monitor flicker/glitch as visual cue only, shock reaction, final rear doorway crack with parallax and black cut |

## Correct first 10-second approval-stage voiceover
"The entire city had been evacuated. A deadly yellow gas was spreading through the streets, killing anyone who breathed it. But Emma was still trapped."

No dialogue, no phone ringing, no story4 character Noah, no invented caller, no narration omissions.

New first-10 draft requires narration from Kie.ai Gemini 3.8 Flash TTS **after explicit paid approval**. Record all required text for this milestone without truncation. Set picture timing from observed TTS duration; if these words cannot be read coherently within 10 seconds, report the pace conflict and propose boundary adjustments for approval rather than speeding narration unnaturally.

## Technical, quality and approval locks
- Original immutable V3 reference package and 30-second video remain unchanged.
- Three.js PerspectiveCamera, GSAP absolute-time, Pillow/OpenCV alpha/masks, SVG/Canvas2D motion graphics, OfflineAudioContext for atmospheres, WebCodecs/Mediabunny, FFmpeg/FFprobe, Playwright, multi-CPU GitHub Actions using pinned V3 GHCR digest.
- 1920x1080, 16:9, 30fps, actual H264/AAC MP4. Audit narration with listening, word alignment, no clipped or missing phrases, correct story sequence, visual parallax at normal playback, visual QA and frame decode. Reuse paid assets; do not regenerate for render-only corrections.
- Next milestone: REPLACE superseded first 10 seconds and show for explicit approval. Do NOT produce 10–30 until approval; do NOT produce beyond 30 until second approval.
- Google Drive is delivery target; verify upload before claiming completion.
