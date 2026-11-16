#!/usr/bin/env python3
"""Existing movie clip speech audit using word-level Whisper timestamps.
ASR is diagnostic only; NEVER replaces or regenerates any source voice.
"""
from __future__ import annotations
from pathlib import Path
from faster_whisper import WhisperModel
import json, csv, subprocess, os
import numpy as np
ROOT=Path("hotel-room-next-door-assets/video")
OUT=Path("hotel-asr-report")
OUT.mkdir(exist_ok=True)
model=WhisperModel("base.en",device="cpu",compute_type="int8",cpu_threads=4,num_workers=1)
results=[]
order=sorted(ROOT.glob("GROK*.mp4"))
for i,p in enumerate(order):
    audio=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-of","json",str(p)],text=True))
    duration=float(audio.get("format",{}).get("duration") or 0)
    # Decode with FFmpeg directly, avoiding PyAV version incompatibility.
    raw_pcm=subprocess.check_output(["ffmpeg","-hide_banner","-loglevel","error","-i",str(p),"-vn","-ac","1","-ar","16000","-f","f32le","pipe:1"])
    waveform=np.frombuffer(raw_pcm,dtype="<f4").copy()
    segments,info=model.transcribe(waveform,beam_size=5,language="en",word_timestamps=True,condition_on_previous_text=False,
        vad_filter=False,temperature=0.0, no_speech_threshold=0.45)
    secs=[]
    words=[]
    for seg in segments:
        entry={"start":round(seg.start,2),"end":round(seg.end,2),"text":seg.text.strip(),
        "avg_logprob":round(seg.avg_logprob,3),"no_speech_prob":round(seg.no_speech_prob,3)}
        secs.append(entry)
        for w in seg.words or []:
            words.append({"start":round(w.start,2),"end":round(w.end,2),"text":w.word.strip(),"probability":round(w.probability,3)})
    ends=words[-1]["end"] if words else None
    result={"id":p.stem,"duration":duration,"transcript":" ".join(s["text"] for s in secs),"segments":secs,
        "words":words,"last_word_end":ends}
    results.append(result)
    print(f"[{i+1}/{len(order)}] {p.stem}: last_word={ends}, {result['transcript']}",flush=True)
(OUT/"ASR_ALL_GROK_CLIPS.json").write_text(json.dumps({"model":"faster-whisper/base.en","diagnostic_only":True,"clips":results},indent=2)+"\n")
with (OUT/"ASR_SUMMARY.csv").open("w",newline="") as f:
    w=csv.writer(f)
    w.writerow(["clip","duration","last_word_end","transcript"])
    for r in results:w.writerow([r["id"],r["duration"],r["last_word_end"],r["transcript"]])
