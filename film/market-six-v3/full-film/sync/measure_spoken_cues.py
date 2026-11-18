#!/usr/bin/env python3
"""Measure actual spoken-word onsets from existing approved Gemini 3.8 Flash audio.

faster-whisper is diagnostic only (the same ASR family already used in film/asr_diagnose_original_dialogue.py).
It is NOT a substitute TTS or image-generation model. Audio bytes are never regenerated.
All shots are tied to exact user-script phrases, not fixed 6.67-second intervals.
"""
from __future__ import annotations
import json, re, sys, wave, math, unicodedata, difflib, hashlib
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel

ROOT=Path("film/market-six-v3/full-film")
SYNC=ROOT/"sync"
OUT=Path("sync_results");OUT.mkdir(exist_ok=True)
source=json.loads((ROOT/"ORIGINAL_STORY_SPOKEN_TURNS.json").read_text())
blue=json.loads((ROOT/"SHOT_IMAGE_BLUEPRINT.json").read_text())
manual=json.loads((SYNC/"NARRATION_SHOT_CUES.json").read_text())
assert source["exact_model"]=="google/gemini-3-8-flash-tts"
assert blue["image_model"]=="gpt-image-2.5-lower"
assert len(blue["shots"])==131 and len(source["chapters"])==15
audio=Path("narration/MARKET_SIX_KIE_FLASH_VERBATIM_CONTINUATION_30TO900.wav")
with wave.open(str(audio),"rb") as f:
    assert (f.getframerate(),f.getnchannels(),f.getsampwidth(),f.getnframes())==(24000,1,2,870*24000)
    pcm=np.frombuffer(f.readframes(f.getnframes()),dtype="<i2").copy()
print("EXISTING_ORIGINAL_VOICE",len(pcm)/24000,"sec, NO PAID API",flush=True)

def tok(s):
    s=unicodedata.normalize("NFKD",s).lower().replace("’","'").replace("—"," ")
    return re.findall(r"[a-z0-9]+",s)

def locate(words,cue):
    c=tok(cue)
    if not c:raise RuntimeError("Empty exact narration cue")
    ix=[i for i in range(len(words)-len(c)+1) if words[i:i+len(c)]==c]
    if len(ix)!=1:raise RuntimeError("Cue must occur exactly once in original user speech: "+repr(cue)+" matches="+repr(ix))
    return ix[0]

def audio16(frame):
    arr=frame.astype(np.float32)*(1/32768)
    # Strict deterministic linear PCM interpolation (no extra media or codec model).
    points=np.linspace(0,len(arr)-1,round(len(arr)*2/3),dtype=np.float64)
    return np.interp(points,np.arange(len(arr)),arr).astype("float32")

def interpolate_word(onsets,ix):
    if ix in onsets:return onsets[ix],True
    keys=sorted(onsets)
    pre=max((k for k in keys if k<ix),default=None)
    nxt=min((k for k in keys if k>ix),default=None)
    if pre is not None and nxt is not None and nxt>pre:
        return onsets[pre]+(onsets[nxt]-onsets[pre])*(ix-pre)/(nxt-pre),False
    if pre is not None:return onsets[pre]+(ix-pre)*.38,False
    if nxt is not None:return max(0,onsets[nxt]-(nxt-ix)*.38),False
    raise RuntimeError("No recognized word onsets")

def quant(t):
    return round(round(t*30)/30,6)

def place_cuts(start,end,targets,minlen=1.20):
    n=len(targets)
    assert n>=2 and end-start>minlen*n
    cuts=[float(start)]+[float(t) for t in targets[1:]]+[float(end)]
    # Bound each text cue start within true chapter clock; do not move words from later chapters.
    for j in range(1,n):
        cuts[j]=max(start+minlen*j,min(end-minlen*(n-j),cuts[j]))
    # Forward and backward minimum duration projection ensures no lost scene/blank gaps.
    for _ in range(4):
        for j in range(1,n):
            cuts[j]=max(cuts[j],cuts[j-1]+minlen)
        for j in range(n-1,0,-1):
            cuts[j]=min(cuts[j],cuts[j+1]-minlen)
    return [quant(v) for v in cuts]

asr=WhisperModel("base.en",device="cpu",compute_type="int8",cpu_threads=4,num_workers=1)
reports=[];cuts=[];shot_count=0;aligned_misses=0
for ch in source["chapters"]:
    chnum=ch["chapter"];start=float(ch["start_sec"]);end=float(ch["end_sec"]);duration=end-start
    offset=int(round((start-30)*24000));samples=int(round(duration*24000))
    data=audio16(pcm[offset:offset+samples])
    segments,info=asr.transcribe(data,language="en",beam_size=5,
        word_timestamps=True,condition_on_previous_text=False,
        temperature=0.0,vad_filter=False)
    detected=[]
    for seg in segments:
        for word in seg.words or []:
            ww=tok(word.word)
            for fragment in ww:
                detected.append(dict(t=round(float(word.start),4),end=round(float(word.end),4),
                                    word=fragment,p=float(word.probability or 0)))
    expected=tok(" ".join(turn["text"] for turn in ch["turns"]))
    recognized=[w["word"] for w in detected]
    matcher=difflib.SequenceMatcher(a=expected,b=recognized,autojunk=False)
    pairs=[]
    for a,b,size in matcher.get_matching_blocks():
        for k in range(size):pairs.append((a+k,b+k))
    cover=len(set(i for i,j in pairs))/len(expected)
    if cover<.60:
        raise RuntimeError(f"ASR original-word matching coverage too low in chapter {chnum}: {cover:.3f} ({len(expected)} expected, {len(recognized)} ASR); STOP without guessed sync")
    mapped={i:detected[j]["t"] for i,j in pairs}
    original=manual["chapters"][str(chnum)]
    assert len(original)==(5 if chnum==1 else 9)
    targets=[];audit=[];last_word_index=-1
    for i,item in enumerate(original):
        cue=item["cue"]
        if cue.startswith("@end-"):
            t=duration-float(cue.split("-")[-1]);match=True;word_ix=len(expected)
        else:
            word_ix=locate(expected,cue)
            if word_ix<=last_word_index:raise RuntimeError("Out-of-order user-script cue "+cue)
            t,match=interpolate_word(mapped,word_ix)
            t=max(0.,min(duration-.10,t-.13))
            last_word_index=word_ix
        if i==0:t=0.
        if not match:aligned_misses+=1
        targets.append(start+t)
        audit.append({"shot_key":item["shot_key"],"cue":cue,"expected_word_index":word_ix,
                      "raw_audible_cue_absolute_time":round(start+t,3),"asr_direct_match":bool(match)})
    grid=place_cuts(start,end,targets,manual.get("min_shot_seconds",1.2))
    chapter_shots=sorted((s for s in blue["shots"] if s["chapter"]==chnum),key=lambda s:s["ordinal"])
    assert len(chapter_shots)==len(original)
    for i,(shot,entry) in enumerate(zip(chapter_shots,audit)):
        assert entry["shot_key"]==shot["key"]
        old=float(shot["global_start"]);new=grid[i];out=grid[i+1]
        if out-new<1.14:raise RuntimeError(f"Shot too short after 30fps grid {chnum}-{i}: {out-new:.3f}")
        cuts.append({"chapter":chnum,"key":shot["key"],"description":shot["description"],
            "old_start":round(old,4),"start_sec":new,"end_sec":out,
            "cue":entry["cue"],"spoken_cue_start_sec":entry["raw_audible_cue_absolute_time"],
            "cut_vs_speech_lag_seconds":round(new-entry["raw_audible_cue_absolute_time"],3),
            "cut_adjustment_seconds":round(new-old,3),
            "asr_direct_match":entry["asr_direct_match"]})
    report={"chapter":chnum,"expected_tokens":len(expected),"whisper_tokens":len(recognized),
      "matched_expected_fraction":round(cover,3),"measured_cues":audit,
      "mean_absolute_cut_adjustment":round(float(np.mean([abs(grid[i]-chapter_shots[i]["global_start"]) for i in range(len(grid)-1)])),3),
      "longest_resulting_shot_s":round(max(grid[i+1]-grid[i] for i in range(len(grid)-1)),2),
      "first_ASR_words":detected[:8],"last_ASR_words":detected[-8:]}
    reports.append(report)
    shot_count+=len(chapter_shots)
    print("CHAPTER_SYNC",chnum,"word coverage",report["matched_expected_fraction"],
          "cut shift mean",report["mean_absolute_cut_adjustment"],"s",
          "longest shot",report["longest_resulting_shot_s"],"s",flush=True)
assert shot_count==131 and len(cuts)==131
assert cuts[0]["start_sec"]==30 and abs(cuts[-1]["end_sec"]-900)<1e-5
assert sum(abs(x["cut_adjustment_seconds"])>.8 for x in cuts)>=40,"No meaningful audiovisual repair measured"
result={"project":"MARKET_SIX_ALL_15_CHAPTERS_ACTUAL_SPOKEN_WORD_SYNC",
 "status":"MEASURED_131_EXACT_USER_SCRIPT_CUES_FROM_EXISTING_KIE_FLASH_SPEECH",
 "narration_model":"google/gemini-3-8-flash-tts","narration_source":"EXISTING_APPROVED_870S_TRACK_NO_NEW_TTS",
 "image_model":"gpt-image-2.5-lower","image_sources":"EXISTING_APPROVED_131_SNAPGEN_ASSETS",
 "asr_tool":"faster-whisper/base.en DIAGNOSTIC ONLY, not TTS or video tool",
 "duration_seconds":900,"first30_unchanged":True,
 "cue_count":shot_count,"missed_exact_asr_onsets_interpolated":aligned_misses,
 "chapters":reports,"shots":cuts}
(OUT/"MEASURED_NARRATION_TO_SHOT_CUTS.json").write_text(json.dumps(result,indent=2))
(OUT/"SYNC_COMPARISON_SUMMARY.json").write_text(json.dumps({
    "status":result["status"],"chapter_coverage":[{"chapter":x["chapter"],"coverage":x["matched_expected_fraction"],"avg_cut_shift_s":x["mean_absolute_cut_adjustment"]} for x in reports],
    "corrected_illustrations":shot_count,"over_1s_cuts":sum(abs(x["cut_adjustment_seconds"])>1 for x in cuts),
    "measured_exact_model":"google/gemini-3-8-flash-tts","new_paid_media_generation":0},indent=2))
print("PASS SYNC SPEECH ANCHORS",shot_count,"full_original_movie_seconds",900,"moved >1s",sum(abs(x["cut_adjustment_seconds"])>1 for x in cuts),flush=True)
