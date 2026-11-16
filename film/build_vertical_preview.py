#!/usr/bin/env python3
"""Rebuild a 180s 9:16 editorial preview from the verified Snapgen history assets.

Original speech stays in Grok/Muse videos; no synthesized narration or TTS.
Editorial title graphics and a quiet original tonal score are constructed locally.
This is a preview, not a human-approved artistic final.
"""
from __future__ import annotations
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import tempfile
import wave
import math
import array
import hashlib

from PIL import Image, ImageDraw, ImageFont

ROOT=Path.cwd()
ASSETS=ROOT/"hotel-room-next-door-assets"/"video"
WORK=ROOT/"hotel-video-export"
CLIPS=WORK/"clips"
GFX=WORK/"graphics"
OUTPUT=WORK/"HOTEL_ROOM_NEXT_DOOR_CINEMATIC_VERTICAL_PREVIEW_480P.mp4"
for x in (WORK,CLIPS,GFX): x.mkdir(parents=True,exist_ok=True)

# Timings are the original edited 180-second (30-beat) scene structure.
SHOTS=[
("S01",3,"MUSE_BROLL_A",0),("S02",3,"MUSE_BROLL_A",5),
("S03",9,"GROK_S03",0),("S04",8,"GROK_S04",0),
("S05",7,"GROK_S05",0),("S06",3,"MUSE_BROLL_B",5),
("S07",8,"GROK_S07",0),("S08",8,"GROK_S08",0),
("S09",7,"GROK_S09",0),("S10",3,"MUSE_BROLL_C",2),
("S11",7,"GROK_S11",0),("S12",6,"GROK_TEST_S12",0),
("S13",8,"GROK_S13",0),("S14",7,"GROK_S14",0),
("S15",7,"GROK_S15",0),("S16",7,"GROK_S16",0),
("S17",9,"GROK_S17",0),("S18",7,"GROK_S18",0),
("S19",8,"GROK_S19",0),("S20",3,"MUSE_BROLL_D",0),
("S21A",6,"GROK_S21A",0),("S21B",5,"GROK_S21B",0),
("S22",4,"MUSE_BROLL_D",5),("S23",8,"GROK_S23",0),
("S24A",5,"GROK_S24A",0),("S24B",5,"GROK_S24B",0),
("S25",4,None,0),("S26",6,"GROK_S26",0),
("S27",5,"GROK_S27",0),("S28",4,None,0)]
assert sum(s[1] for s in SHOTS)==180, sum(s[1] for s in SHOTS)

def run(cmd,timeout=180):
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    if p.returncode:
        raise RuntimeError(f"Command failed ({p.returncode}): "+p.stderr.decode("utf-8","replace")[-900:])
    return p.stdout

def ft(size=27,bold=True,serif=False):
    base="/usr/share/fonts/truetype/dejavu/"
    path=base+("DejaVuSerif.ttf" if serif else "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
    return ImageFont.truetype(path,size)

def center(draw,line,y,size=24,color=(244,241,234),serif=False):
    f=ft(size,serif=serif)
    bb=draw.textbbox((0,0),line,font=f)
    draw.text(((480-bb[2]+bb[0])/2,y),line,font=f,fill=color)

def overlay_card(lines,path,size=22):
    im=Image.new("RGBA",(480,854),(0,0,0,0))
    d=ImageDraw.Draw(im)
    sy=430 if len(lines)>2 else 510
    d.rounded_rectangle((36,sy,444,sy+len(lines)*44+50),radius=13,fill=(6,11,20,212),outline=(152,114,104,245),width=2)
    d.rectangle((59,sy+17,63,sy+len(lines)*44+18),fill=(175,66,66,255))
    for i,line in enumerate(lines):
        d.text((80,sy+15+i*44),line,font=ft(size),fill=(250,244,235))
    im.save(path)

def title_card(page,path):
    im=Image.new("RGB",(480,854),(9,15,25))
    d=ImageDraw.Draw(im)
    d.rectangle((38,65,442,789),outline=(69,69,73),width=2)
    d.line((76,208,404,208),fill=(161,65,68),width=2)
    if page=="S25":
        center(d,"SURVEILLANCE ARCHIVE",145,17,(171,171,170))
        center(d,"FILE 02",245,19,(160,165,169))
        center(d,"THE ORIGINAL",340,33,serif=True)
        center(d,"BETRAYAL",395,44,(208,89,89),True)
        d.rounded_rectangle((135,550,345,612),radius=8,fill=(157,45,58))
        center(d,"PLAY NEXT",567,20)
    else:
        center(d,"THE HOTEL ROOM NEXT DOOR",196,17,(172,169,164))
        if page=="S28A":
            for i,line in enumerate(("FOUR CHEATERS.","TWO BROKEN","MARRIAGES.")):
                center(d,line,333+i*48,28,serif=True)
        elif page=="S28B":
            center(d,"WHO BETRAYED",347,27,serif=True)
            center(d,"EVERYONE FIRST?",396,28,(205,92,92),True)
        else:
            center(d,"TO BE CONTINUED...",375,26,serif=True)
        d.line((136,540,344,540),fill=(153,63,66),width=2)
    im.save(path)

for name,lines in {
    "S01":["THE HOTEL ROOM","NEXT DOOR"],
    "S06":["ROOM 1808.","COME ALONE."],
    "S20":["SINCE EVERYONE IS","FINALLY TOGETHER...","WHO STARTED THIS?"],
    "S23":["SIX MONTHS EARLIER"]
}.items():
    overlay_card(lines,GFX/f"{name}.png",19 if name=="S20" else 22)
for n in ["S25","S28A","S28B","S28C"]:
    title_card(n,GFX/f"{n}.png")

def ffmpeg_card(name,duration,path):
    run(["ffmpeg","-hide_banner","-loglevel","error","-y",
        "-loop","1","-framerate","24","-i",str(GFX/f"{name}.png"),
        "-f","lavfi","-i","anullsrc=r=48000:cl=stereo",
        "-t",str(duration),"-r","24",
        "-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","128k","-shortest",str(path)],120)
    return path

def render_one(s):
    name,duration,src,ss=s
    dst=CLIPS/f"{name}.mp4"
    if src is None:
        if name=="S25": return ffmpeg_card("S25",4,dst)
        subs=[("S28A",1.8),("S28B",1.5),("S28C",0.7)]
        parts=[]
        for sn,seconds in subs:
            p=CLIPS/f"{sn}.mp4"
            ffmpeg_card(sn,seconds,p)
            parts.append(p)
        ct=CLIPS/"ending.txt"
        ct.write_text("".join(f"file '{p.absolute()}'\n" for p in parts))
        run(["ffmpeg","-hide_banner","-loglevel","error","-y",
            "-f","concat","-safe","0","-i",str(ct),"-c","copy",str(dst)],80)
        return dst
    file=ASSETS/f"{src}.mp4"
    if not file.is_file(): raise FileNotFoundError(str(file))
    vf="scale=480:854:force_original_aspect_ratio=increase:flags=lanczos,crop=480:854,fps=24,setsar=1,format=yuv420p"
    if name=="S23": vf+=",eq=saturation=0.55:contrast=1.04"
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(ss),"-i",str(file)]
    af=f"aresample=48000,highpass=f=65,afade=t=in:st=0:d=0.025,afade=t=out:st={max(0,duration-0.06):.3f}:d=0.05"
    if name in ("S01","S06","S20","S23"):
        cmd+=["-loop","1","-i",str(GFX/f"{name}.png"),"-t",str(duration),
              "-filter_complex",f"[0:v]{vf}[base];[1:v]format=rgba[title];[base][title]overlay=0:0:shortest=1,format=yuv420p[outv]",
              "-map","[outv]","-map","0:a:0"]
    else:
        cmd+=["-t",str(duration),"-vf",vf]
    cmd+=["-af",af,"-c:v","libx264","-preset","veryfast","-crf","21","-threads","2",
          "-r","24","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-ar","48000","-ac","2",str(dst)]
    run(cmd,160)
    return dst

print("Building 30 edited beats...",flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
    rendered=list(ex.map(render_one,SHOTS))
for s,p in zip(SHOTS,rendered): print(f"OK {s[0]} {p.stat().st_size}",flush=True)

concat=CLIPS/"concat.txt"
concat.write_text("".join(f"file '{p.absolute()}'\n" for p in rendered))
base=WORK/"original-voices-picture-cut.mp4"
print("Joining native-voice edit...",flush=True)
run(["ffmpeg","-hide_banner","-loglevel","error","-y",
    "-f","concat","-safe","0","-i",str(concat),
    "-vf","fps=24","-r","24","-c:v","libx264","-preset","veryfast","-crf","22",
    "-threads","4","-c:a","aac","-ar","48000","-ac","2","-b:a","192k",str(base)],450)

# Original subtle non-copyright sound texture, intentionally quiet under native dialogue.
score=WORK/"original-quiet-suspense.wav"
sr=48000
with wave.open(str(score),"wb") as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr)
    for start in range(0,180*sr,sr):
        vals=array.array("h")
        for i in range(sr):
            t=(start+i)/sr
            if t>=176: amp=0
            elif t<33:amp=.65
            elif t<66:amp=.75
            elif t<125:amp=1
            elif t<143:amp=1.15
            else:amp=1.3
            fade=min(1,t/2,max(0,(176-t)/2))
            x=amp*.002*fade*(math.sin(2*math.pi*55*t)+.25*math.sin(2*math.pi*82.5*t))
            for onset,level in ((65.8,.03),(124.9,.025),(138.9,.04),(143,.03),(161,.045),(176,.08)):
                dt=t-onset
                if 0<=dt<1.2: x+=level*math.exp(-dt*5)*math.sin(2*math.pi*62*t)
            v=max(-32768,min(32767,round(x*32767)))
            vals.extend((v,v))
        w.writeframes(vals.tobytes())

print("Applying final mix and leveling...",flush=True)
run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(base),"-i",str(score),
    "-filter_complex",
    "[0:a]aresample=48000,acompressor=threshold=-19dB:ratio=1.6:attack=12:release=190[native];"
    "[1:a]volume=0.8[score];"
    "[native][score]amix=inputs=2:duration=first:weights=1 1,loudnorm=I=-16:LRA=11:TP=-1.5[mix]",
    "-map","0:v:0","-map","[mix]","-c:v","copy","-c:a","aac","-b:a","192k",
    "-ar","48000","-ac","2","-movflags","+faststart","-t","180",str(OUTPUT)],180)

p=json.loads(run(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(OUTPUT)]))
v=next(s for s in p["streams"] if s["codec_type"]=="video")
assert v["width"]==480 and v["height"]==854,(v["width"],v["height"])
duration=float(p["format"]["duration"])
assert abs(duration-180)<0.10,duration
run(["ffmpeg","-v","error","-i",str(OUTPUT),"-f","null","-"],240)
sha=hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
report={"status":"editorial_preview_technical_verified_not_artistic_final",
        "file":OUTPUT.name,"bytes":OUTPUT.stat().st_size,"sha256":sha,
        "duration_sec":duration,"video_codec":v["codec_name"],
        "width":v["width"],"height":v["height"],"fps":v["avg_frame_rate"],
        "source_footage":"41 Snapgen history assets",
        "speech":"original native Grok clips, no external TTS",
        "human_lip_sync_review":"not verified"}
(WORK/"PREVIEW_EXPORT_REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
print("FINAL_EXPORT "+json.dumps(report),flush=True)
