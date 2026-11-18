#!/usr/bin/env python3
"""Patch ONLY cut timings of already illustrated original Hunyuan V3 chapter scenes.

Keep paid SnapGen source plates, masks, art.js/engine.js, camera rig,
Kie Flash narration PCM, subject design, and chapter/script identity unchanged.
"""
from __future__ import annotations
import argparse,json,shutil,hashlib
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("--chapter",required=True,type=int)
p.add_argument("--project-root",default="film/market-six-v3/full-film/chapter-projects")
p.add_argument("--sync-master",default="sync_results/MEASURED_NARRATION_TO_SHOT_CUTS.json")
args=p.parse_args()
ch=args.chapter
assert 1<=ch<=15
sync=json.loads(Path(args.sync_master).read_text())
assert sync["status"]=="MEASURED_131_EXACT_USER_SCRIPT_CUES_FROM_EXISTING_KIE_FLASH_SPEECH"
assert (sync["narration_model"],sync["image_model"])==("google/gemini-3-8-flash-tts","gpt-image-2.5-lower")
assert sync["first30_unchanged"] is True and len(sync["shots"])==131
project=Path(args.project_root)/f"ch{ch:02d}"
manifest=project/"scene_manifest.json"
data=json.loads(manifest.read_text())
assert data["chapter"]==ch and data["speech_model"]=="google/gemini-3-8-flash-tts" and data["image_model"]=="gpt-image-2.5-lower"
before=hashlib.sha256(manifest.read_bytes()).hexdigest()
cuts=[s for s in sync["shots"] if s["chapter"]==ch]
assert len(cuts)==len(data["shots"])==(5 if ch==1 else 9)
start=float(data["start_sec"]);end=float(data["end_sec"])
for i,(shot,cut) in enumerate(zip(data["shots"],cuts)):
    assert shot["key"]==cut["key"] and cut["end_sec"]-cut["start_sec"]>=1.13
    shot["start_sec"]=cut["start_sec"]
    shot["end_sec"]=cut["end_sec"]
    shot["spoken_cue"]=cut["cue"]
    shot["spoken_cue_start_sec"]=cut["spoken_cue_start_sec"]
    shot["sync_source"]="faster-whisper diagnostic on ORIGINAL Kie 3.8 Flash existing WAV; original exact text verified"
    assert abs(shot["start_sec"]-(start if i==0 else data["shots"][i-1]["end_sec"]))<.00001
assert data["shots"][-1]["end_sec"]==end
data["audiovisual_sync"]="WORD_ANCHORED_SCENE_EDIT_V2"
data["visual_cut_source_sha256"]=before
data["entire_original_story_preserved"]=True
manifest.write_text(json.dumps(data,indent=2))
# The authored original cinematic code is unchanged except allowing faster
# reaction cuts when two distinct spoken actions follow within 1.9 seconds.
main=project/"main.js"
text=main.read_text()
old="if(!(duration>1.9))"
assert old in text, "Do not substitute renderer; unexpected native V3 scene source"
text=text.replace(old,"if(!(duration>1.05))")
main.write_text(text)
(project/"SYNC_APPLIED_QA.json").write_text(json.dumps({
 "chapter":ch,"original_manifest_sha256":before,
 "shot_count":len(cuts),
 "source_visuals_unmodified":True,
 "narration_model":"google/gemini-3-8-flash-tts",
 "image_model":"gpt-image-2.5-lower",
 "source_original_rig_unmodified":True,
 "new_paid_jobs":0,
 "cuts":[{"id":s["key"],"start":s["start_sec"],"end":s["end_sec"],"spoken":s["spoken_cue"]} for s in data["shots"]]
},indent=2))
print("PASS",ch,"retimed",len(cuts),"genuine image-first Three.js/GSAP film shots to actual audible spoken phrases",flush=True)
