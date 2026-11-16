#!/usr/bin/env python3
"""Technical validation of recovered Snapgen .mp4 clips; no new generations.
Report video/audio stream presence, dimensions, runtime, fps, and short preview strips.
This checks decoding and formats but never claims artistic or lip-sync quality.
"""
from __future__ import annotations
import json, subprocess
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw

ROOT=Path("hotel-room-next-door-assets")
out=[]
thumbnails=ROOT/"previews"
thumbnails.mkdir(parents=True, exist_ok=True)
for video in sorted((ROOT/"video").glob("*.mp4")):
    obj=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(video)],text=True))
    vs=[s for s in obj.get("streams",[]) if s.get("codec_type")=="video"]
    a=[s for s in obj.get("streams",[]) if s.get("codec_type")=="audio"]
    if not vs:
        raise RuntimeError("Video stream missing: "+video.name)
    s=vs[0]
    duration=float(obj.get("format",{}).get("duration") or s.get("duration") or 0)
    rec={"name":video.name,"duration_seconds":duration,"width":s.get("width"),"height":s.get("height"),"frame_rate":s.get("avg_frame_rate"),"video_codec":s.get("codec_name"),"audio_present":bool(a),"audio_codec":a[0].get("codec_name") if a else None,"audio_channels":a[0].get("channels") if a else None}
    out.append(rec)
    print(f"{video.name}: {rec['width']}x{rec['height']}, {duration:.2f}s, audio={rec['audio_present']}")
    if duration>1:
        samples=[min(duration-0.1,x) for x in [0.3,duration*0.25,duration*0.5,duration*0.75]]
        tile=[]
        for i,t in enumerate(samples):
            jpg=thumbnails/f"{video.stem}_frame{i:02d}.jpg"
            subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-ss",str(t),"-i",str(video),"-frames:v","1","-q:v","3","-y",str(jpg)],check=True,timeout=35)
            im=Image.open(jpg).convert("RGB")
            target=ImageOps.contain(im,(240,300))
            tile.append(target)
        w=sum(x.width for x in tile)
        h=max(x.height for x in tile)+40
        canvas=Image.new("RGB",(w,h),(22,22,22))
        x=0
        for i,im in enumerate(tile):
            canvas.paste(im,(x,30))
            x+=im.width
        ImageDraw.Draw(canvas).text((8,8),video.stem,fill=(255,255,255))
        canvas.save(thumbnails/f"{video.stem}_contact.jpg",quality=88)
(ROOT/"video-technical-qa.json").write_text(json.dumps({"videos":out},indent=2)+"\n",encoding="utf-8")
