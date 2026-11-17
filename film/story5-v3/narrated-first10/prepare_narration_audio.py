#!/usr/bin/env python3
"""Quality-gated trim/resample of single *already generated* user-selected Kie Flash-Lite narrator WAV.
No speech generation, no substitutions, no removal of spoken words.
"""
import json,subprocess,sys,wave
from pathlib import Path
import numpy as np

src=Path("narrator/EMMA_STORY5_FIRST10_KIE_GEMINI38_FLASH_LITE_NARRATOR.wav")
audit_file=Path("narrator/KIE_ONE_FLASH_LITE_NARRATOR_COST_AND_AUDIO_AUDIT.json")
out=Path("delivery/VOICE_CLEAN_NARRATOR_10S.wav")
if not (src.is_file() and audit_file.is_file()):raise RuntimeError("Missing exact Kie WAV and credit audit: STOP, do not request new paid audio")
a=json.loads(audit_file.read_text())
assert a["status"]=="SUCCESS_ONE_PAID_JOB" and a["jobs_created"]==1 and a["retry_count"]==0,a
assert a["provider"]=="kie.ai" and a["model"]=="google/gemini-3-8-flash-lite-tts",a
assert a["credits_spent_from_balance"]<=5,a
spoken="The entire city had been evacuated. A deadly yellow gas was spreading through the streets, killing anyone who breathed it. But Emma was still trapped."
assert a["exact_narration_text"]==spoken
with wave.open(str(src),"rb") as w:
    sr=w.getframerate()
    channels=w.getnchannels()
    sampwidth=w.getsampwidth()
    frames=w.getnframes()
    pcm=np.frombuffer(w.readframes(frames),dtype="<i2").astype(np.float32)
assert (sr,channels,sampwidth)==(24000,1,2),(sr,channels,sampwidth)
duration=frames/sr
if duration<4 or duration>16:raise RuntimeError("Narrator voice duration implausible: "+str(duration))
peak=float(np.max(abs(pcm))) if len(pcm) else 0
if peak<200:raise RuntimeError("Nearly silent voice WAV; do not substitute")
# Trim only objectively quiet *outer margins*; retain >=125 ms before and >=200 ms after active voice.
block=int(sr*.01)
rms=np.sqrt(np.mean(np.pad(pcm,(0,(-len(pcm))%block)).reshape(-1,block)**2,axis=1))
threshold=max(65.0,peak*.008)
active=np.flatnonzero(rms>threshold)
if len(active)<50:raise RuntimeError("Too little audible narration in Kie output")
begin=max(0,(int(active[0])*.01)-.16)
end=min(duration,(int(active[-1]+1)*.01)+.22)
visible=end-begin
if visible>10.59:raise RuntimeError("Entire 25-word audio cannot fit in 10s without unnatural acceleration. STOP and report exact duration "+str(visible))
target=9.77
tempo=max(1.0,visible/target)
if tempo>1.085:raise RuntimeError("Refuse >8.5% narration speed change; no speech can be cut")
out.parent.mkdir(exist_ok=True,parents=True)
filters=[f"atrim=start={begin:.5f}:end={end:.5f}","asetpts=PTS-STARTPTS"]
if tempo>1.001:filters.append(f"atempo={tempo:.6f}")
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(src),"-af",",".join(filters),"-ac","1","-ar","24000","-c:a","pcm_s16le",str(out)],check=True)
with wave.open(str(out),"rb") as w:
    sec=w.getnframes()/w.getframerate()
assert sec>4 and sec<=9.84,("Voice cannot fit into first ten seconds",sec)
o={
 "status":"AUDIO_TIMING_TECHNICAL_PASS; ACTUAL WORDS REQUIRE LISTENING REVIEW",
 "provider":"kie.ai","model":"google/gemini-3-8-flash-tts",
 "original_wave_duration_seconds":round(duration,3),
 "trimmed_outer_silence_start_seconds":round(begin,4),
 "trimmed_outer_silence_end_seconds":round(duration-end,4),
 "preserved_speech_window_seconds":round(visible,3),
 "applied_tempo_factor":round(tempo,5),
 "output_voice_seconds":round(sec,3),
 "maximum_allowed_seconds":10,
 "narration_request_text":spoken,"narration_not_independently_transcribed":True,
 "paid_jobs":1,
 "credits_charged":a["credits_spent_from_balance"],
 "no_extra_paid_calls":True,"no_cut_spoken_words_requested":True
}
Path("delivery/VOICE_TIMING_QA.json").write_text(json.dumps(o,indent=2))
print("STORY5_KIE_AUDIO_QA",json.dumps(o),flush=True)
