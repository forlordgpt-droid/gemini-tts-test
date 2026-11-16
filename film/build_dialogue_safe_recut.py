#!/usr/bin/env python3
"""Rebuild a dialogue-safe 9:16 editorial recut from the verified Snapgen history assets.

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
WORK=ROOT/"hotel-video-recut"
CLIPS=WORK/"clips"
GFX=WORK/"graphics"
OUTPUT=WORK/"HOTEL_ROOM_NEXT_DOOR_DIALOGUE_SAFE_RECUT_480P.mp4"
for x in (WORK,CLIPS,GFX): x.mkdir(parents=True,exist_ok=True)

# Speech-aware trimmed coverage. 29 beats. Removed duplicated confrontation S13.
# S24B uses native Brian audio over TV insert to hide hairstyle continuity error.
SHOTS=[
("S01",4.0,"MUSE_BROLL_A",0),("S02",3.5,"MUSE_BROLL_A",5),
("S03",6.0,"GROK_S03",0),("S04",5.0,"GROK_S04",0),
("S05",8.3,"GROK_S05",0),("S06",3.8,"MUSE_BROLL_B",5),
("S07",6.0,"GROK_S07",0),("S08",5.9,"GROK_S08",0),
("S09",6.8,"GROK_S09",0),("S10",3.2,"MUSE_BROLL_C",2),
("S11",6.6,"GROK_S11",0),("S12",9.9,"GROK_TEST_S12",0),
("S14",8.3,"GROK_S14",0),
("S15",6.0,"GROK_S15",0),("S16",5.8,"GROK_S16",0),
("S17",7.5,"GROK_S17",0),("S18",6.0,"GROK_S18",0),
("S19",7.0,"GROK_S19",0),("S20",3.8,"MUSE_BROLL_D",0),
("S21A",6.3,"GROK_S21A",0),("S21B",6.5,"GROK_S21B",0),
("S22",4.6,"MUSE_BROLL_D",5),("S23",8.8,"GROK_S23",0),
("S24A",5.5,"GROK_S24A",0),
("S24B",3.5,"GROK_S24B",4.55),
("S25",2.0,None,0),("S26",7.5,"GROK_S26",0),
("S27",6.8,"GROK_S27",0),("S28",6.0,None,0)]
TOTAL_SECONDS=sum(x[1] for x in SHOTS)
assert 168<TOTAL_SECONDS<181, TOTAL_SECONDS

# Native dialogue: verified against word-level ASR. Only original soundtrack is used.
# Captions help audibility on phone without synthesizing or replacing voices.
SPEECH={
"S03":[(.05,2.10,"Brian thinks I'm in Philadelphia."),(3.04,4.28,"Chloe thinks I'm in Chicago.")],
"S04":[(.63,1.99,"We're terrible people."),(2.56,3.70,"Then why are you smiling?")],
"S05":[(3.88,4.75,"Your wife?"),(5.32,7.03,"Relax. She never calls twice.")],
"S07":[(.05,2.02,"What if Ethan finds out?"),(2.78,4.08,"Ethan trusts me with his life.")],
"S08":[(.05,2.10,"That's not comforting."),(3.02,4.34,"Forget your husband tonight.")],
"S09":[(.74,2.85,"Jenna was asking questions yesterday."),(4.04,5.62,"She suspects nothing.")],
"S11":[(3.62,5.92,"Wait. I bought Jenna that exact bag.")],
"S12":[(1.72,2.24,"Ethan?"),(3.02,3.55,"Brian?"),(4.66,6.10,"What the hell are you doing with my wife?"),(7.24,9.32,"I could ask you the same about mine.")],
"S14":[(1.62,3.76,"Brian, please. I can explain."),(5.40,6.50,"With my best friend?")],
"S15":[(.48,1.79,"You said you were in Chicago!"),(2.70,4.10,"You said you were visiting your mother!")],
"S16":[(.05,2.60,"You sat at my dinner table!"),(3.64,5.06,"You borrowed my car!")],
"S17":[(.74,4.15,"Stop! All four of us are liars! Nobody here is innocent!")],
"S18":[(.10,1.86,"How long, Ethan?"),(2.72,3.38,"Eight months.")],
"S19":[(.10,2.55,"Eight? You told me three months."),(3.24,5.03,"Three months? With my best friend?")],
"S21A":[(.10,1.85,"Who sent this?"),(3.04,4.61,"I got one this afternoon.")],
"S21B":[(.10,1.20,"Me too."),(2.82,4.69,"Someone booked this room in my name.")],
"S23":[(.10,3.04,"I think Ethan is cheating with someone."),(5.02,7.10,"Then we need to teach him a lesson.")],
"S24A":[(.62,2.04,"Chloe, what did you do?"),(2.86,3.81,"I didn't send that!")],
"S24B":[(4.80-4.55,6.75-4.55,"Six months? You said three.")],
"S26":[(.10,2.01,"Ethan, don't play it!"),(2.62,3.09,"Why?"),(3.80,5.69,"You'll know who destroyed us.")],
"S27":[(.94,2.88,"It was never supposed to go this far."),(4.74,5.56,"Oh, God.")],
}

def mk_srt():
    path=WORK/"dialogue-verified.srt"
    def clock(t):
        ms=round(max(0,t)*1000)
        h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); sec,ms=divmod(ms,1000)
        return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
    entries=[]
    t=0.0
    for name,duration,src,offset in SHOTS:
        for start,end,line in SPEECH.get(name,[]):
            st=t+max(0,start)
            en=t+min(duration,end)
            if en>st+0.04: entries.append((st,en,line))
        t+=duration
    with path.open("w",encoding="utf-8") as f:
        for i,(st,en,line) in enumerate(entries,1):
            f.write(f"{i}\n{clock(st)} --> {clock(en)}\n{line}\n\n")
    # Explicit ASS styling is required. Some FFmpeg/libass builds silently
    # ignore force_style when ingesting SRT, leaving large white subtitles.
    # Here the subtitle style itself is authored and applied natively.
    ass=WORK/"dialogue-small-white-on-red.ass"
    with ass.open("w",encoding="utf-8") as f:
        f.write("""[Script Info]
Title: Hotel Room Next Door - Small Lower Red Subtitles
ScriptType: v4.00+
PlayResX: 480
PlayResY: 854
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,13,&H00FFFFFF,&H00FFFFFF,&H001010C8,&H001010C8,-1,0,0,0,100,100,0,0,3,2,0,2,15,15,22,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
        def ass_time(seconds):
            n=round(max(0.0,seconds)*100)
            hours,n=divmod(n,360000)
            minutes,n=divmod(n,6000)
            sec,centis=divmod(n,100)
            return f"{hours}:{minutes:02d}:{sec:02d}.{centis:02d}"
        for st,en,line in entries:
            clean=line.replace("\n",r"\N").replace("{","(").replace("}",")")
            f.write(f"Dialogue: 0,{ass_time(st)},{ass_time(en)},Default,,0,0,0,,{clean}\n")
    return path

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
    command=["ffmpeg","-hide_banner","-loglevel","error","-y",
        "-loop","1","-framerate","24","-i",str(GFX/f"{name}.png"),
        "-f","lavfi","-i","anullsrc=r=48000:cl=stereo",
        "-t",str(duration),"-r","24"]
    if name=="S25":
        # Subtle editorial push on the surveillance-file title; no new AI assets.
        command+=["-vf",
          "zoompan=z='min(zoom+0.0007,1.065)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=480x854:fps=24,format=yuv420p"]
    command+=["-c:v","libx264","-preset","veryfast","-crf","20",
        "-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-shortest",str(path)]
    run(command,120)
    return path

def render_one(s):
    name,duration,src,ss=s
    dst=CLIPS/f"{name}.mp4"
    if src is None:
        if name=="S25": return ffmpeg_card("S25",duration,dst)
        subs=[("S28A",2.0),("S28B",2.0),("S28C",2.0)]
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
    # Ending: keep the original seven seconds of native dialogue, but cut away
    # BEFORE a visibly different Brian appears in close-up. His final whispered
    # confession plays OFF CAMERA over the ominous television, as in real cinema.
    if name=="S27":
        source=ASSETS/"GROK_S27.mp4"
        tv=ASSETS/"MUSE_BROLL_D.mp4"
        vf0="scale=480:854:force_original_aspect_ratio=increase:flags=lanczos,crop=480:854,setsar=1,format=yuv420p"
        vf1="scale=480:854:force_original_aspect_ratio=increase:flags=lanczos,crop=480:854,setsar=1,eq=saturation=0.62:contrast=1.12,format=yuv420p"
        command=["ffmpeg","-hide_banner","-loglevel","error","-y",
                 "-i",str(source),"-ss","7.0","-i",str(tv),"-t",str(duration),
                 "-filter_complex",
                 f"[0:v]trim=start=0:end=4.375,setpts=PTS-STARTPTS,{vf0}[v0];"
                 f"[1:v]trim=start=0:duration=2.425,setpts=PTS-STARTPTS,{vf1}[v1];"
                 f"[v0][v1]concat=n=2:v=1:a=0,fps=24,fade=t=out:st=6.71:d=0.09[vid];"
                 f"[0:a]atrim=start=0:end={duration},asetpts=PTS-STARTPTS,aresample=48000,highpass=f=65,afade=t=out:st=6.68:d=0.1[aud]",
                 "-map","[vid]","-map","[aud]",
                 "-c:v","libx264","-preset","veryfast","-crf","21","-threads","2",
                 "-r","24","-pix_fmt","yuv420p",
                 "-c:a","aac","-b:a","160k","-ar","48000","-ac","2",str(dst)]
        run(command,160)
        return dst
    # Hide the recast buzz-cut Brian on screen, but KEEP his native words.
    # His off-screen voice is heard while the mystery television remains in frame.
    if name=="S24B":
        visual=ASSETS/"MUSE_BROLL_D.mp4"
        audio=ASSETS/"GROK_S24B.mp4"
        visual_filter="scale=480:854:force_original_aspect_ratio=increase:flags=lanczos,crop=480:854,fps=24,eq=saturation=0.72:contrast=1.11,format=yuv420p"
        cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
             "-ss","6.45","-i",str(visual),"-ss",str(ss),"-i",str(audio),
             "-t",str(duration),
             "-filter_complex",f"[0:v]{visual_filter}[v];[1:a]aresample=48000,highpass=f=65,afade=t=in:st=0:d=0.03,afade=t=out:st=3.39:d=0.10[a]",
             "-map","[v]","-map","[a]","-c:v","libx264","-preset","veryfast",
             "-crf","21","-threads","2","-r","24","-pix_fmt","yuv420p",
             "-c:a","aac","-b:a","160k","-ar","48000","-ac","2",str(dst)]
        run(cmd,160)
        return dst
    file=ASSETS/f"{src}.mp4"
    if not file.is_file(): raise FileNotFoundError(str(file))
    vf="scale=480:854:force_original_aspect_ratio=increase:flags=lanczos,crop=480:854,fps=24,setsar=1,format=yuv420p"
    if name=="S23": vf+=",eq=saturation=0.55:contrast=1.04"
    # S27 uses deliberate cut to television rather than showing recast actor close-up.
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(ss),"-i",str(file)]
    af=f"aresample=48000,highpass=f=65,afade=t=in:st=0:d=0.025,afade=t=out:st={max(0,duration-0.06):.3f}:d=0.05"
    if name in ("S01","S06","S20","S23"):
        cmd+=["-loop","1","-i",str(GFX/f"{name}.png"),"-t",str(duration),
              "-filter_complex",f"[0:v]{vf}[base];[1:v]format=rgba[title];[base][title]overlay=0:0:shortest=1:enable=\'lt(t,2)\',format=yuv420p[outv]",
              "-map","[outv]","-map","0:a:0"]
    else:
        cmd+=["-t",str(duration),"-vf",vf]
    cmd+=["-af",af,"-c:v","libx264","-preset","veryfast","-crf","21","-threads","2",
          "-r","24","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-ar","48000","-ac","2",str(dst)]
    run(cmd,160)
    return dst

print(f"Building {len(SHOTS)} dialogue-safe beats, target {TOTAL_SECONDS:.2f}s...",flush=True)
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
    for start in range(0,math.ceil(TOTAL_SECONDS)*sr,sr):
        vals=array.array("h")
        for i in range(sr):
            t=(start+i)/sr
            if t>=TOTAL_SECONDS: amp=0
            elif t<33:amp=.65
            elif t<66:amp=.75
            elif t<125:amp=1
            elif t<143:amp=1.15
            else:amp=1.3
            fade=min(1,t/1.5,max(0,(TOTAL_SECONDS-t)/0.7))
            x=amp*.013*fade*(math.sin(2*math.pi*55*t)+.25*math.sin(2*math.pi*82.5*t))
            for onset,level in ((60,.025),(92,.018),(114,.025),(137,.027),(151,.032),(TOTAL_SECONDS-10,.045)):
                dt=t-onset
                if 0<=dt<1.2: x+=level*math.exp(-dt*5)*math.sin(2*math.pi*62*t)
            v=max(-32768,min(32767,round(x*32767)))
            vals.extend((v,v))
        w.writeframes(vals.tobytes())

print("Applying speech-first music-ducked mix with burned dialogue captions...",flush=True)
captions=mk_srt()
# Mobile subtitles: very small white lettering on an opaque crimson-red block, centered at the very bottom inside the 9:16 video frame.
ass_path=WORK/"dialogue-small-white-on-red.ass"
run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(base),"-i",str(score),
    "-filter_complex",
    "[0:a]aresample=48000,acompressor=threshold=-21dB:ratio=1.9:attack=10:release=150[native];"
    "[1:a]volume=0.95[score];"
    "[score][native]sidechaincompress=threshold=0.020:ratio=4.5:attack=30:release=350[duck];"
    "[native][duck]amix=inputs=2:duration=first:weights=1 1,loudnorm=I=-16:LRA=10:TP=-1.5[mix]",
    "-map","0:v:0","-map","[mix]",
    "-vf",f"ass={ass_path}",
    "-c:v","libx264","-preset","veryfast","-crf","20","-threads","4","-r","24","-pix_fmt","yuv420p",
    "-c:a","aac","-b:a","192k",
    "-ar","48000","-ac","2","-movflags","+faststart","-t",str(TOTAL_SECONDS),str(OUTPUT)],300)

p=json.loads(run(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(OUTPUT)]))
v=next(s for s in p["streams"] if s["codec_type"]=="video")
assert v["width"]==480 and v["height"]==854,(v["width"],v["height"])
duration=float(p["format"]["duration"])
assert abs(duration-TOTAL_SECONDS)<0.60,(duration,TOTAL_SECONDS)
run(["ffmpeg","-v","error","-i",str(OUTPUT),"-f","null","-"],240)
sha=hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
report={"status":"editorial_preview_technical_verified_not_artistic_final",
        "file":OUTPUT.name,"bytes":OUTPUT.stat().st_size,"sha256":sha,
        "duration_sec":duration,"video_codec":v["codec_name"],
        "width":v["width"],"height":v["height"],"fps":v["avg_frame_rate"],
        "source_footage":"41 Snapgen history assets",
        "speech":"original native Grok clips, no external TTS",
        "human_lip_sync_review":"not verified", "subtitle_style":"verified explicit ASS style: font 13 bold white on opaque red rectangular background, bottom-center", "subtitle_renderer":"libass native ASS file", "card_display_seconds":2.0, "editorial_changes":["removed duplicate S13 confrontation","S12 complete native speech retained","S11 ghosted handbag transition cut before damaged frames","S16 dead-air hold shortened","S24B original audio carried over TV insert to hide hair mismatch","S27 group-to-TV cut avoids mismatched closeup while retaining native words","S25 subtle title motion","word-timed trims and subtitles","audible original score ducked under speech"]}
(WORK/"PREVIEW_EXPORT_REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
print("FINAL_EXPORT "+json.dumps(report),flush=True)
