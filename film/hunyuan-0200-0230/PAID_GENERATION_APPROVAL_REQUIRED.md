# Required owner authorization — paid generation gate

**No paid generation executed.** The V2.1 master instructions require explicit provider/model/output count/unit price/maximum authorization; merely listing a provider/model in the work request is not blanket consent to spend.

## Proposed fixed no-retry batch
- **SnapGen** exact model: `gpt-image-2.5-lower`; **4 distinct 16:9 premium field/flash scene art images** (an extra shot reuses the wide field image). SnapGen's model descriptor says **approximately 1 credit per image**, **720p output**. Estimate **4 credits**, stop before any charge beyond the approved image cap. Reuse past approved illustration frames as look references where compatible, not as final scenery for this new location.
- **KIE.ai** exact model: `google/gemini-3-8-flash-lite-tts`; **2 narration outputs** (two controlled ~15s passages) using existing **Fola** voice if supported. Estimated around **0.7 credits combined** from published time/token pricing; allocate **up to 1 credit** for both and stop if actual pricing would exceed this limit. Preserve audio; no additional regeneration or retries without new consent.
- **Total estimated** ~4.7 credits; proposed **absolute cap: 5 credits** for the 4 images + 2 narration outputs only, **zero automatic retries**.

**Cheaper choices considered:** reuse already approved first-30s imagery and 0–120s narration where relevant (zero new credits, but they do not contain this later field/flash story); use the user's chosen ~1-credit GPT Image 2.5 Lower rather than prior ~3-credit Nano Banana 2. Do not switch the specified paid models or render stack. If cost or quality cannot fit the cap, pause and report rather than substituting tools.

Confirm explicit authorization for this exact batch/cap before generating or dispatching a workflow that invokes the keys. KIE and SnapGen keys remain GitHub Secrets only. Confirmed runnable artifacts must later be stored in connected Google Drive, not solely expiring GitHub artifacts.

## Current state
- Library story located, source excerpt transcribed through 02:30.
- Original Hunyuan ZIP found both in ChatGPT Library and existing GitHub repo.
- Original `engine.test.cjs` passed locally; no project render executed.
- GitHub Actions rendering not started; 1920×1080/30fps, 900 frames, three ten-second public-CPU shards planned after approved assets.
