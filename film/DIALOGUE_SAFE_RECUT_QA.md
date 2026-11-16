# The Hotel Room Next Door — Dialogue-Safe Recut QA
**Status:** Rendered and technically verified; artistic/lip-sync approval remains user review.  
**GitHub Actions run:** https://github.com/forlordgpt-droid/gemini-tts-test/actions/runs/43942666128  
**Download artifact:** https://github.com/forlordgpt-droid/gemini-tts-test/actions/runs/43942666128/artifacts/14265135362

## No-regeneration guarantee
No new image or video model generations were submitted. The edit used exactly the existing archive of 41 Snapgen history assets (15 still references, 22 Grok clips including test, 4 Muse atmospheric clips). Dialogue comes from original Grok clip soundtracks; no synthesized or external TTS was introduced. New text overlays, subtitles and an original understated tonal sound bed are editorial assets only.

## Identified problems and repairs
- **S12 versus S13 repeated confrontation:** S12 was cut to 6s even though "I could ask you the same about mine" ends at approximately 9.24s of its 10.04s source. The new edit includes approximately 9.9s of S12, delivering Chloe's "Ethan?", Ethan's "What the hell are you doing with my wife?", and Brian's full reply. S13's duplicate confrontation was removed.
- **S24B line missing:** The old trim stopped at 5.0s while Brian's "Six months? You said three." begins near 4.8s and ends near 6.7s. The new edit preserves the original audio from ~4.55 to 8.05s, placing the line over moving TV imagery because the generated close-up shows a visibly inconsistent haircut.
- **S27 cliffhanger:** Restored the complete original offscreen male line and Brian's "Oh, God." ending near 5.5s. A motivated group-to-television cut replaces Brian's visually inconsistent later close-up.
- **S11 hallway / handbag:** Retimed to end before the original generated morph/ghost transition near 6.7s, while retaining the full handbag recognition dialogue that ends near 5.88s.
- **Long dead-air holds:** Shortened pauses, including S16; removed the need for an artificial 180-second runtime. B-roll, reaction beats and final titles remain where they serve the drama.
- **Audibility:** Added mobile-safe, burned-in captions for the 42 transcribed dialogue subtitle blocks, a modest tonal suspense bed with voice-sidechain ducking, and a mastered stereo mix.

## Final technical acceptance
- **File:** HOTEL_ROOM_NEXT_DOOR_DIALOGUE_SAFE_RECUT_480P.mp4
- **Duration:** 171.833333 seconds (2:51.83)
- **Resolution:** 480 x 854, portrait 9:16
- **Frame rate:** 24 fps CFR, 4,124 frames
- **Codecs:** H.264 video, AAC audio
- **File bytes:** 22,429,020
- **SHA-256:** d667eb3d21ac244310f26885cc883fd4f78ec902af1dc61d775d2bf7ed8853de
- **Frame-by-frame decoding:** PASS, every output frame decoded without error
- **Black sections longer than 0.3s:** 0 detected
- **Silent stretches longer than 1.5s at -42 dB:** 0 detected
- **Subtitles:** 42 spoken-text blocks, with accompanying SRT in the GitHub artifact

## Limitations
Word alignment is automated speech recognition and not a human-transcribed guarantee. Native AI-generated acting and lip-sync may contain imperfections that cannot be solved completely without asset regeneration. The export is an improved cinematic editorial cut, not independently human-certified as final picture lock. No assertions are made that remediating cuts can restore dialogue absent from source footage.
