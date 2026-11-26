#!/usr/bin/env python3
import os, subprocess, urllib.request, pathlib, json
P=pathlib.Path("output"); P.mkdir(exist_ok=True)
urls=[
"https://7a4964de26acd06ff740870066a92ff8.r2.cloudflarestorage.com/geminigen-prd-upload-bucket/4899352/generated_result/video/1ac64336-e99b-11f1-ae6a-0e06b81f46da/20261126_131417_UTC_0.mp4?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ac21101432ac699ee432dddd257a928b%2F20261126%2Fauto%2Fs3%2Faws4_request&X-Amz-Date=20261126T131431Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=60eec690efaa8452dc0559f039092c0bab4066d48637c342ec295081a798c966",
"https://7a4964de26acd06ff740870066a92ff8.r2.cloudflarestorage.com/geminigen-prd-upload-bucket/4899352/generated_result/video/29ce6520-e99b-11f1-8674-aea2bba863f5/20261126_131442_UTC_0.mp4?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ac21101432ac699ee432dddd257a928b%2F20261126%2Fauto%2Fs3%2Faws4_request&X-Amz-Date=20261126T131456Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=c4b68943793a740ff5c03e880202aa8280c6911f6900490462046f8ac122475c",
"https://7a4964de26acd06ff740870066a92ff8.r2.cloudflarestorage.com/geminigen-prd-upload-bucket/4899352/generated_result/video/311b3966-e99b-11f1-a0de-f6f134494ab3/20261126_131450_UTC_0.mp4?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ac21101432ac699ee432dddd257a928b%2F20261126%2Fauto%2Fs3%2Faws4_request&X-Amz-Date=20261126T131457Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=f49855402dccbc739664212f7cbf0a7a1c6c1b5314fab61f75e161923bc00b33"
]
def run(cmd):
 print("RUN",cmd[:6],flush=True);subprocess.run(cmd,check=True)
for i,u in enumerate(urls):
 f=P/f"raw{i+1}.mp4"
 urllib.request.urlretrieve(u,f)
 run(["ffmpeg","-y","-i",str(f),"-vf","scale=480:854:force_original_aspect_ratio=increase,crop=480:854,fps=24,setsar=1","-af","aresample=async=1:first_pts=0","-t","15","-c:v","libx264","-preset","fast","-crf","21","-pix_fmt","yuv420p","-c:a","aac","-ar","48000","-ac","2",str(P/f"scene{i+1}.mp4")])
with open(P/"concat.txt","w") as fp:
 for i in range(1,4):fp.write(f"file 'scene{i}.mp4'\n")
run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(P/"concat.txt"),"-c","copy",str(P/"joined.mp4")])
events=[
(0.00,3.70,"YOU SOLD MOM'S HOUSE?"),(4.00,5.90,"Emma, please."),
(6.00,10.90,"THAT WAS ALL WE HAD LEFT OF HER."),(11.00,14.80,"I know. I loved that house, too."),
(15.00,18.90,"You had no right to sell it."),(19.00,22.80,"It paid for Sophie's surgery."),
(23.00,25.90,"What?"),(26.00,29.70,"The insurance never paid. I told you it did."),
(30.00,33.80,"You sold Mom's house to save my daughter?"),(34.00,37.70,"I would've sold anything."),
(38.00,40.80,"Dad... why didn't you tell me?"),(41.00,43.00,"You already had enough to carry.")
]
def ts(t):
 h=int(t//3600);m=int(t//60)%60;s=int(t)%60;cs=int((t%1)*100)
 return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
with open(P/"captions.ass","w") as f:
 f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 480\nPlayResY: 854\nWrapStyle: 2\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Main,DejaVu Sans,25,&H00FFFFFF,&H00FFFFFF,&H00201B1A,&H82000000,1,0,0,0,100,100,0,0,1,2.8,1.5,2,22,22,160,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
 for a,b,t in events:f.write(f"Dialogue: 0,{ts(a)},{ts(b)},Main,,0,0,0,,{t}\n")
run(["ffmpeg","-y","-i",str(P/"joined.mp4"),"-vf","ass="+str(P/"captions.ass"),"-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",str(P/"He_Sold_Moms_House_45s_Captioned.mp4")])
run(["ffmpeg","-y","-i",str(P/"joined.mp4"),"-c","copy","-movflags","+faststart",str(P/"He_Sold_Moms_House_45s_Clean.mp4")])
run(["ffmpeg","-y","-ss","00:00:01.2","-i",str(P/"He_Sold_Moms_House_45s_Captioned.mp4"),"-frames:v","1",str(P/"cover.jpg")])
print("FINISHED", [(x.name,x.stat().st_size) for x in P.glob("*.mp4")])
