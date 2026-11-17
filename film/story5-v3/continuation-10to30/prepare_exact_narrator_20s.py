#!/usr/bin/env python3
"""Trim only OUTER silence of existing exact Kie Gemini 3.8 Flash-Lite Charon voice.
Never remove speech, exceed approved duration, or substitute a provider/tool.
"""
import json,subprocess,sys,wave
from pathlib import Path
import numpy as np
root=Path("film/story5-v3/continuation-10to30")
m=json.loads((root/"APPROVED_10TO30_MANIFEST.json").read_text())
src=Path("narrator/STORY5_10TO30_KIE38_FLASH_LITE_CHARON.wav")
audit=Path("narrator/KIE_EXACT_SPEND_AND_VOICE_AUDIT.json")
out=Path("delivery/STORY5_10TO30_CLEAN_CHARON_20S.wav")
if not src.is_file() or not audit.is_file():raise RuntimeError("Missing completed EXACT Kie voice or audit. Do NOT regenerate")
a=json.loads(audit.read_text())
assert a["status"]=="SUCCESS_ONE_PAID_JOB" and a["created_jobs"]==1 and a["retry_count"]==0
assert a["provider"]=="kie.ai" and a["model"]=="google/gemini-3-8-flash-lite-tts"
assert a["voice"]=="Charon" and a["source_text"]==m["narration"]["text"]
assert a["credits_spent"]<=m["user_authorization"]["tts_credits_max"]==5
with wave.open(str(src),"rb") as w:
    rate=w.getframerate();ch=w.getnchannels();width=w.getsampwidth();count=w.getnframes()
    pcm=np.frombuffer(w.readframes(count),dtype="<i2").astype(np.float32)
assert (rate,ch,width)==(24000,1,2)
duration=count/rate
if not 9.0<duration<30:raise RuntimeError("Narrator WAV duration out of range "+str(duration))
peak=float(np.max(abs(pcm))) if len(pcm) else 0
if peak<200:raise RuntimeError("Narrator inaudible")
blk=int(rate*.01)
rms=np.sqrt(np.mean(np.pad(pcm,(0,(-len(pcm))%blk)).reshape(-1,blk)**2,axis=1))
threshold=max(65.0,peak*.008)
active=np.flatnonzero(rms>threshold)
if len(active)<200:raise RuntimeError("Narration seems too silent/short")
begin=max(0,float(int(active[0])*.01-.14))
end=min(duration,float(int(active[-1]+1)*.01+.23))
speech=end-begin
if speech>21.45:raise RuntimeError("Full narration too long; refuse to cut or over-speed: "+str(speech))
target=19.73
tempo=max(1.0,speech/target)
if tempo>1.085:raise RuntimeError("No >8.5% narration speed change: "+str(tempo))
out.parent.mkdir(exist_ok=True,parents=True)
filters=[f"atrim=start={begin:.5f}:end={end:.5f}","asetpts=PTS-STARTPTS"]
if tempo>1.001:filters.append(f"atempo={tempo:.6f}")
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(src),"-af",",".join(filters),"-ar","24000","-ac","1","-c:a","pcm_s16le",str(out)],check=True)
with wave.open(str(out),"rb") as w:placed=w.getnframes()/w.getframerate()
if not 15.0<placed<=19.82:raise RuntimeError("Placing all speech in 20 seconds failed "+str(placed))
qa={"status":"TECHNICAL_PASS_NARRATION_VERBATIM_REQUESTED; HUMAN_LISTENING_APPROVAL_REQUIRED","model":"google/gemini-3-8-flash-lite-tts","voice":"Charon","original_audio_seconds":round(duration,4),"trimmed_outer_start_seconds":round(begin,4),"trimmed_outer_end_seconds":round(duration-end,4),"retained_window_seconds":round(speech,4),"tempo_factor":round(tempo,6),"placed_voice_seconds":round(placed,4),"exact_source_text":a["source_text"],"tts_credits_spent":a["credits_spent"],"new_paid_jobs":0,"no_words_intentionally_cut":True,"independently_transcribed":False}
Path("delivery/STORY5_NARRATION_TIMING_QA.json").write_text(json.dumps(qa,indent=2))
print("STORY5_10TO30_NARRATOR_QA",json.dumps(qa),flush=True)
