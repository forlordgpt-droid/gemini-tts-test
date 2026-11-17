#!/usr/bin/env python3
"""Fail-closed film QA on REAL decoded 1080p footage, not code screenshots only.
Pillow + OpenCV + FFprobe/FFmpeg. No model substitution, no paid calls.
This cannot replace artistic review at NORMAL playback speed.
"""
import argparse,cv2,json,os,subprocess,sys,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
cv2.setNumThreads(2)

def call(args):
    return subprocess.run(args,check=True,text=True,capture_output=True).stdout
def metadata(movie):
    return json.loads(call(['ffprobe','-v','error','-show_entries',
       'stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames:format=duration',
       '-of','json',str(movie)]))
def check(movie,expected_frames,out,seconds=None,sample_every=1.0):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    doc=metadata(movie)
    v=next((s for s in doc['streams'] if s['codec_type']=='video'),None)
    a=next((s for s in doc['streams'] if s['codec_type']=='audio'),None)
    if not v or not a:raise ValueError('Missing full H264/AAC final MP4')
    if (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))!=('h264',1920,1080,'30/1',expected_frames):
        raise ValueError('Wrong codec/resolution/framecount: '+str(v))
    if a['codec_name']!='aac':raise ValueError('Audio codec is not AAC')
    length=float(doc['format']['duration'])
    if abs(length-expected_frames/30)>.12:raise ValueError('Unexpected duration '+str(length))
    if seconds is not None and abs(length-seconds)>.12:raise ValueError('Duration requested mismatch')
    # Full decoder check: broken or damaged frames make the deliverable invalid.
    subprocess.run(['ffmpeg','-hide_banner','-v','error','-xerror','-i',str(movie),'-f','null','-'],check=True)
    cap=cv2.VideoCapture(str(movie))
    if not cap.isOpened():raise ValueError('Cannot decode actual movie')
    times=np.arange(.5,max(1,length-.25),sample_every)
    views=[];metrics=[];prev=None
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC,float(t)*1000)
        ok,frame=cap.read()
        if not ok:raise ValueError('Missing decoded frame at '+str(t))
        small=cv2.resize(frame,(240,135),interpolation=cv2.INTER_AREA)
        if prev is not None:
            diff=np.abs(small.astype(np.int16)-prev.astype(np.int16))
            metrics.append({'from_s':round(float(t-sample_every),2),'to_s':round(float(t),2),'mean_absolute_difference':round(float(diff.mean()),3)})
        prev=small
        if len(views)<100:views.append((round(float(t),2),cv2.cvtColor(small,cv2.COLOR_BGR2RGB)))
    cap.release()
    # No success from FFprobe alone! Fail on several consecutive near-identical frames.
    frozen=[x for x in metrics if x['mean_absolute_difference']<.8]
    streak=0;longest=0
    for x in metrics:
        streak=streak+1 if x['mean_absolute_difference']<.8 else 0
        longest=max(longest,streak)
    if longest>=3:
        raise ValueError('Frozen/slideshow/incorrect timestamp sequence >=3s: '+json.dumps(frozen[:15]))
    if metrics and sum(x['mean_absolute_difference']>2 for x in metrics)<len(metrics)*.40:
        raise ValueError('Video lacks sufficient actual visible change, inspect camera and depth assets')
    width=5;tile=(320,180);rows=min(20,(len(views)+width-1)//width)
    sheet=Image.new('RGB',(tile[0]*width,tile[1]*rows),(5,13,27))
    d=ImageDraw.Draw(sheet)
    stride=max(1,len(views)//(width*rows))
    selected=views[::stride][:width*rows]
    for k,(t,frame) in enumerate(selected):
        im=Image.fromarray(frame).resize(tile,Image.Resampling.BILINEAR)
        x=k%width*tile[0];y=k//width*tile[1]
        sheet.paste(im,(x,y))
        d.rectangle((x+4,y+4,x+100,y+23),fill=(9,20,35))
        d.text((x+11,y+8),f'{t:.2f} sec',fill=(240,234,210))
    sheet.save(out/'ACTUAL_VIDEO_CONTACT_SHEET.jpg',quality=88)
    qa={'status':'TECHNICAL_PASS_ARTISTIC_NORMAL_SPEED_REVIEW_STILL_REQUIRED','frames':expected_frames,
     'duration_s':length,'width':1920,'height':1080,'fps':30,'video':'h264','audio':'aac',
     'decoded_every_frame':True,'time_samples':len(times),'max_near_frozen_second_streak':longest,
     'mean_frame_change':round(float(np.mean([x['mean_absolute_difference'] for x in metrics])),3) if metrics else None,
     'camera_parallax_and_story_must_be_reviewed_by_human':True,
     'paid_generation_requests':0}
    (out/'ACTUAL_VIDEO_QA.json').write_text(json.dumps(qa,indent=2))
    print(json.dumps(qa,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--video',type=Path,required=True)
    p.add_argument('--frames',type=int,required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--seconds',type=float)
    p.add_argument('--sample-every',type=float,default=1.0)
    a=p.parse_args()
    try:check(a.video,a.frames,a.out,a.seconds,a.sample_every)
    except Exception as e:print('HUNYUAN_V3_VIDEO_QA_FAILURE',str(e),file=sys.stderr);sys.exit(1)
