#!/usr/bin/env python3
"""Assemble exact 0-based WebCodecs shards using REQUIRED FFmpeg/FFprobe.
Reject bad PTS, missing shots, silent audio, wrong dimensions or frozen frames.
Never requests external media services.
"""
import argparse,json,pathlib,subprocess,tempfile,sys,hashlib
from pathlib import Path
def call(args):
    return subprocess.run(args,check=True,text=True,capture_output=True).stdout
def info(p):
    return json.loads(call(['ffprobe','-v','error','-show_entries',
       'stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames:format=duration',
       '-of','json',str(p)]))
def times(p):
    raw=call(['ffprobe','-v','error','-select_streams','v:0',
       '-show_entries','frame=best_effort_timestamp_time','-of','csv=p=0',str(p)])
    return [float(v.strip().split(',')[0]) for v in raw.splitlines() if v.strip() and v.strip().split(',')[0].replace('.','',1).replace('-','',1).isdigit()]
def main():
    a=argparse.ArgumentParser()
    a.add_argument('--plan',required=True)
    a.add_argument('--chunks-dir',required=True)
    a.add_argument('--approved-audio',required=True,help='Preapproved/synced real narration+original SFX; no synthetic stand-ins')
    a.add_argument('--out',required=True)
    a.add_argument('--qc-dir',required=True)
    x=a.parse_args()
    plan=json.loads(Path(x.plan).read_text())
    assert plan.get('visual_review_required') is True
    shards=plan['matrix']['include'];assert len(shards)>0
    chunks=Path(x.chunks_dir)
    outputs=[]
    for shard in shards:
        start,count=shard['start_frame'],shard['duration_frames']
        p=chunks/f'part_{start}_{count}.mp4'
        if not p.is_file():raise RuntimeError(f'Missing shard frames {start}–{start+count}: {p}')
        info_doc=info(p)
        v=next((i for i in info_doc['streams'] if i['codec_type']=='video'),None)
        assert v is not None and (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==('h264',1920,1080,'30/1',count),p
        if abs(float(info_doc['format']['duration'])-count/30)>.08:raise RuntimeError('Wrong shard length: '+str(p))
        pts=times(p)
        if len(pts)!=count:raise RuntimeError('Frame timestamps omitted/corrupt '+str(p))
        if abs(pts[0])>.04:raise RuntimeError('WebCodecs shard begins with ABSOLUTE PTS; frozen movie risk: '+str(p))
        if any(b-a<1/90 for a,b in zip(pts,pts[1:])):raise RuntimeError('Nonmonotonic shard PTS: '+str(p))
        if abs(pts[-1]-(count-1)/30)>.08:raise RuntimeError('Bad last frame timestamp: '+str(p))
        outputs.append(p.resolve())
    audio=Path(x.approved_audio).resolve()
    if not audio.is_file() or audio.stat().st_size<10000:
        raise RuntimeError('No preapproved narration/SFX mix: DO NOT substitute generated sound')
    total=sum(i['duration_frames'] for i in shards)
    out=Path(x.out);out.parent.mkdir(parents=True,exist_ok=True)
    q=Path(x.qc_dir);q.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        temp=Path(temp)
        manifest=temp/'concat.txt'
        manifest.write_text(''.join("file '"+str(p).replace("'","'\\''")+"'\n" for p in outputs))
        joined=temp/'video_only.mp4'
        subprocess.run(['ffmpeg','-hide_banner','-v','error','-y','-f','concat','-safe','0','-i',str(manifest),'-c:v','copy','-an',str(joined)],check=True)
        subprocess.run(['ffmpeg','-hide_banner','-v','error','-y','-i',str(joined),'-i',str(audio),'-map','0:v:0','-map','1:a:0',
          '-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t',str(total/30),'-movflags','+faststart',str(out)],check=True)
    final=info(out)
    video=next(i for i in final['streams'] if i['codec_type']=='video')
    aud=next(i for i in final['streams'] if i['codec_type']=='audio')
    if (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],int(video['nb_frames']))!=('h264',1920,1080,'30/1',total):
        raise RuntimeError('Merged video frames/timing mismatch; refuse frozen output')
    if aud['codec_name']!='aac' or abs(float(final['format']['duration'])-total/30)>.12:
        raise RuntimeError('Final AAC or duration mismatch')
    movie_pts=times(out)
    if len(movie_pts)!=total or any(b-a<1/90 for a,b in zip(movie_pts,movie_pts[1:])):
        raise RuntimeError('Merged movie has duplicate/frozen presentation timestamps')
    qa={'status':'TECHNICAL_PASS_ARTISTIC_REVIEW_STILL_REQUIRED','shards':len(shards),
     'frames':total,'seconds':total/30,'fps':30,'resolution':'1920x1080',
     'sequence_has_continuous_monotonic_pts':True,'no_paid_api_calls':True,
     'final_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
     'artistic_quality_approval_status':'USER_REVIEW_REQUIRED'}
    (q/'ASSEMBLY_QA.json').write_text(json.dumps(qa,indent=2))
    subprocess.run(['python3',str(Path(__file__).parent/'qa_video.py'),'--video',str(out),'--frames',str(total),'--out',str(q),'--seconds',str(total/30)],check=True)
    print(json.dumps(qa,indent=2))
if __name__=='__main__':
    try:main()
    except Exception as exc:print('HUNYUAN_V3_ASSEMBLY_FAILED:',str(exc),file=sys.stderr);sys.exit(1)
