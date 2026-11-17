# ASSET GENERATION SPENDING POLICY — HUNYUAN VIDEO PROJECT
Effective: 2026-11-17
Source: explicit owner feedback after 6 SnapGen Nano Banana 2 concept images.

## Mandatory rule: NO PAID GENERATION WITHOUT EXPLICIT APPROVAL

- All future calls to paid image, video, speech, music, enhancement, upscaling, and other credit-consuming APIs are **BLOCKED by default**, including SnapGen.
- Before ANY paid call, obtain the owner's explicit affirmative authorization naming: the provider, exact model, quantity of jobs, estimated credits per job and total estimated maximum. Approval of a *look*, design, storyboard, or project is **NOT** permission to incur a cost.
- Reuse already-produced artwork, approved Hunyuan 2D assets and verified narration rather than purchasing duplicates. Free/local authored vectors, licensed assets already held, and authorized GitHub Actions CPU-based rendering are preferred.
- If a paid call is later authorized, present the available cheaper compatible options first. The owner pointed out that GPT Image 2.5 Lower cost about 1 credit per image versus the Nano Banana 2 3-credit model used for the 6 proof-of-concept frames. Cheapest does not override the quality/identity constraints: describe tradeoffs and let the owner decide.
- Never silently substitute a different paid model after approval; any provider/model/quantity change requires fresh approval.
- If a step cannot be finished with existing resources or free compute, STOP and report the blocker and priced options; never auto-spend.

## Incident record (no attempt to erase original work)

2026-11-17: Six style-frame generations were initiated via SnapGen Nano Banana 2 with a quoted estimate of 3 credits each, approximately 18 total, without prior explicit owner permission to spend. A potential 1-credit alternative (GPT Image 2.5 Lower) was not selected. This was unauthorized; the approved style frames may be reused without any additional paid generations. Credits should be verified from SnapGen billing if exact charges are needed; estimated cost is not proof of actual billing.

## Authorized next phase
The owner APPROVED the 6-image style direction. Implement the FIRST 30-SECOND ANIMATED PREVIEW using previously generated reference frames, the original Hunyuan 2D rig, existing KIE narration, and GitHub Actions as available. Before paid generation, pause for owner authorization. The style reference JPG/PNG is not a substitute for independent clean parallax planes: separate and paint clean background layers locally where viable; otherwise report the limitation. Keep the first 30-second preview separate from the full two-minute production until reviewed.

## Enforcement notes for developers and automated assistants
Treat this file as a REQUIRED_PREP_FLIGHT check. Automated workflows should contain no SnapGen generation or paid API calls by default. Do not invoke the existing KIE generation workflow to remake voice when supplied audio is usable. Only the explicit owner approval can override these constraints.
