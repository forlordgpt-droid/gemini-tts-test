#!/usr/bin/env python3
"""Scene-accurate 30s adaptation of one approved 36.16s Kie Flash-Lite WAV.
Cut only measured SILENT GAPS. Stage 30-45 and 45-60 align to original scene boundary.
No words deleted, no new synthetic voice, no changes to original first 30s.
"""
import json,subprocess,wave
from pathlib import Path
import numpy as np
base=Path("film/story5-v3/final-30to60")
m=json.loads((base/"FINAL_30TO60_APPROVED_PRODUCTION_MANIFEST.json").read_text())
audio=Path("narrator/EMMA_STORY5_30TO60_KIE_GEMINI38_FLASH_LITE_CHARON.wav")
audit=Path("narrator/KIE_FINAL_30TO60_CREDIT_AND_TTS_AUDIT.json")
if not audio.is_file() or not audit.is_file():raise RuntimeError("Missing single approved Kie narrator file. STOP NO PAID RETRY.")
a=json.loads(audit.read_text())
assert a["model"]=="google/gemini-3-8-flash-lite-tts" and a["provider"]=="kie.ai" and a["voice"]=="Charon"
assert a["create_task_count"]==1 and a["retry_count"]==0 and a["credits_spent"]<=4
assert a["source_text"]==m["source_narration_30_60"] and a["source_words"]==85
assert m["approve_first30"]["do_not_change"] is True
with wave.open(str(audio)) as w:
 sr,ch,width=w.getframerate(),w.getnchannels(),w.getsampwidth()
 raw=np.frombuffer(w.readframes(w.getnframes()),dtype="<i2").copy()
assert (sr,ch,width)==(24000,1,2)
dur=len(raw)/sr
assert 30<dur<45
# Kie's seven-word sentence pauses are objectively audible-length gaps;
# original scene3-to-scene4 long quiet break is 15.2-16.1 in this exact file.
# Never cut at arbitrary phonemes. Must confirm by local 10ms RMS probe.
step=sr//100
rms=np.sqrt(np.mean(np.pad(raw.astype(np.float32),(0,(-len(raw))%step)).reshape(-1,step)**2,axis=1))
silent=rms<180
beg=np.where(np.diff(np.r_[0,silent.astype(np.int8),0])==1)[0]
end=np.where(np.diff(np.r_[0,silent.astype(np.int8),0])==-1)[0]
gaps=[(x*step/sr,y*step/sr) for x,y in zip(beg,end) if (y-x)*.01>=.6 and x*.01>13.5 and x*.01<17.0]
assert gaps,("No verified scene boundary silence around 15-16s",gaps)
start,endgap=max(gaps,key=lambda z:z[1]-z[0])
split=(start+endgap)/2
assert 14.8<split<16.5,(split,gaps)
def trim_silence_only(voice,keep):
    rms=np.sqrt(np.mean(np.pad(voice.astype(np.float32),(0,(-len(voice))%step)).reshape(-1,step)**2,axis=1))
    silent=rms<180
    starts=np.where(np.diff(np.r_[0,silent.astype(np.int8),0])==1)[0]
    ends=np.where(np.diff(np.r_[0,silent.astype(np.int8),0])==-1)[0]
    keep_samp=int(keep*sr)
    removed=[];parts=[];cursor=0
    for s,e in zip(starts,ends):
        left=s*step;right=min(len(voice),e*step)
        if right-left<.34*sr:continue
        cutleft=left+keep_samp//2;cutright=right-keep_samp//2
        if cutright<=cutleft:continue
        parts.append(voice[cursor:cutleft]);removed.append([round(cutleft/sr,4),round(cutright/sr,4)])
        cursor=cutright
    parts.append(voice[cursor:])
    return np.concatenate(parts),removed
original_parts=[raw[:round(split*sr)],raw[round(split*sr):]]
trimmed=[trim_silence_only(original_parts[0],.16),trim_silence_only(original_parts[1],.09)]
first,firstcuts=trimmed[0];second,secondcuts=trimmed[1]
# The first scene is slower by design, preserving ~1.5s of true relief/silence before monitor wakes.
assert 12.2<len(first)/sr<14.6,(len(first)/sr,firstcuts)
target_second=14.76
tempo=max(1.0,len(second)/sr/target_second)
assert 1.0<=tempo<1.18,("Unnatural temporal acceleration; refuse",tempo)
out=Path("delivery");out.mkdir(exist_ok=True)
def save(filename,signal):
    with wave.open(str(filename),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(signal.astype("<i2").tobytes())
input2=out/"SCENE4_UNACCELERATED_PAUSE_TRIMMED.wav"
save(input2,second)
part2=out/"SCENE4_45TO60_CLEAN_CHARON.wav"
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(input2),"-af",f"atempo={tempo:.6f}","-ac","1","-ar","24000","-c:a","pcm_s16le",str(part2)],check=True)
with wave.open(str(part2),"rb") as w:
 after=np.frombuffer(w.readframes(w.getnframes()),dtype="<i2").copy();after_seconds=len(after)/sr
assert 14.1<after_seconds<14.86,after_seconds
part1=out/"SCENE3_30TO45_CLEAN_CHARON.wav";save(part1,first)
n=15*sr
full=np.zeros(30*sr,dtype="<i2")
full[:len(first)]=first
full[n:n+len(after)]=after
final=out/"STORY5_30TO60_VERBATIM_SCENE_ALIGNED_30S.wav"
save(final,full)
with wave.open(str(final),"rb") as w:assert w.getnframes()==30*sr
qa={
 "status":"TECHNICAL_PASS_SCENE_ALIGNED_30S_ALL_85_WORDS_SOURCE_REQUESTED_HUMAN_LISTENING_REVIEW_STILL_REQUIRED",
 "source_voice_model":a["model"],"voice":a["voice"],"original_duration_seconds":round(dur,5),
 "scene_boundary_verified_silence_start_seconds":round(start,4),
 "scene_boundary_verified_silence_end_seconds":round(endgap,4),
 "scene_boundary_cut_inside_silence_seconds":round(split,4),
 "original_scene3_words":37,"original_scene4_words":48,
 "first_scene_original_seconds":round(len(original_parts[0])/sr,4),
 "second_scene_original_seconds":round(len(original_parts[1])/sr,4),
 "first_scene_gap_trimmed_seconds":round(len(first)/sr,4),
 "second_scene_gap_trimmed_before_atempo_seconds":round(len(second)/sr,4),
 "second_scene_final_seconds":round(after_seconds,4),
 "final_30s_pcm_samples":len(full),"final_audio_seconds":30.0,"sample_rate":sr,
 "first_scene_silence_cuts":firstcuts,"second_scene_silence_cuts":secondcuts,
 "second_scene_atempo_factor":round(tempo,5),
 "no_source_word_removal":True,"only_reduced_long_silent_gaps":True,
 "source_text":a["source_text"],"exact_source_words":85,"paid_jobs_for_audio_preparation":0,
 "kie_actual_credits":a["credits_spent"],"first30_unmodified":True,
 "independently_transcribed":False
}
(out/"STORY5_30TO60_NARRATION_PACING_AND_SCENE_QA.json").write_text(json.dumps(qa,indent=2))
print("FINAL_SCENE_ALIGNED_NARRATION_QA",json.dumps({k:v for k,v in qa.items() if k not in ("first_scene_silence_cuts","second_scene_silence_cuts","source_text")}),flush=True)
