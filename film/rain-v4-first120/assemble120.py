#!/usr/bin/env python3
"""Canonical 3600-frame V4 assembly with deterministic source-only outputs.

Uses approved first30 MP4, 18 rendered absolute-time shards, five existing approved
Fola WAVs, and one deterministic 90s OfflineAudioContext sound bed. Never makes
any paid model call, changes sources, or falls back to another renderer.
"""
from __future__ import annotations
import hashlib,io,json,math,pathlib,subprocess,sys,wave
from PIL import Image,ImageOps,ImageDraw
ROOT=pathlib.Path.cwd()
DELIVERY=ROOT/'delivery';DELIVERY.mkdir(parents=True,exist_ok=True)
PROJECT=ROOT/'film/rain-v4-first120'
M=json.loads((PROJECT/'continuation_manifest_120.json').read_text())
FIRST=ROOT/'first30/RAIN_V4_FIRST30_COMPLETE.mp4'
VOICE_ROOT=ROOT/'voices'
PARTS_ROOT=ROOT/'parts'
SFX=PARTS_ROOT/'RAIN_V4_FIRST120_SHARD_900/RAIN_V4_30TO120_ORIGINAL_SFX.wav'
OUT=DELIVERY/'RAIN_V4_FIRST120_COMPLETE.mp4'

def run(cmd,timeout=1600):
    print('RUN',cmd[0], 'argv_count',len(cmd), flush=True)
    subprocess.run(cmd,check=True,timeout=timeout)

def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames,sample_rate:format=duration,size','-of','json',str(path)],text=True))

def verify():
    if not FIRST.is_file(): raise RuntimeError('Missing approved first30')
    if hashlib.sha256(FIRST.read_bytes()).hexdigest()!=M['approved_first30_sha256']:raise RuntimeError('Original approved first30 changed')
    a=probe(FIRST)
    v=next(s for s in a['streams'] if s['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==('h264',1920,1080,'30/1',900),v
    assert abs(float(a['format']['duration'])-30)<.08,a
    shorts=[]
    for n in M['shard_plan']['start_frames']:
        folder=PARTS_ROOT/f'RAIN_V4_FIRST120_SHARD_{n}'
        p=folder/f'part_{n}_150.mp4'
        if not p.is_file():raise RuntimeError(f'Missing shard {n}')
        report=json.loads((folder/'shard_qc.json').read_text())
        assert report['pass'] and report['start_frame']==n and report['frame_count']==150,report
        assert hashlib.sha256(p.read_bytes()).hexdigest()==report['sha256'],p
        q=probe(p);v=next(s for s in q['streams'] if s['codec_type']=='video')
        assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==('h264',1920,1080,'30/1',150),v
        assert abs(float(q['format']['duration'])-5)<.08,q
        shorts.append(p)
    assert len(shorts)==18
    paths=[]
    for part in M['tts']['segments']:
        i=int(part['id'][1:]);q=VOICE_ROOT/f'RAIN_V4_30TO120_FOLA_S{i}'/part['filename']
        if not q.is_file():raise RuntimeError('Missing exact original Fola audio '+str(q))
        if hashlib.sha256(q.read_bytes()).hexdigest()!=part['sha256']:raise RuntimeError('Changed approved narration')
        with wave.open(str(q),'rb') as wav:
            assert wav.getframerate()==24000 and wav.getnchannels()==1 and wav.getsampwidth()==2
            assert abs(wav.getnframes()/wav.getframerate()-part['duration_seconds'])<1/24000
        paths.append(q)
    with wave.open(str(SFX),'rb') as wav:assert wav.getframerate()==24000 and wav.getnframes()==2160000 and wav.getnchannels()==1
    print('SOURCE_PASS first30, 18 x 150-frame, five hash-checked Fola WAVs, exact 90s Web Audio WAV',flush=True)
    return shorts,paths

def video(shorts):
    video_path=DELIVERY/'VIDEO_ONLY_CANONICAL_3600.mp4'
    inputs=[FIRST,*shorts]
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y']
    for q in inputs:cmd.extend(['-i',str(q)])
    filters=[];labels=[]
    for i,_ in enumerate(inputs):
        label=f'v{i}';filters.append(f'[{i}:v]settb=AVTB,setpts=N/(30*TB),format=yuv420p[{label}]');labels.append(f'[{label}]')
    filters.append(''.join(labels)+f'concat=n={len(inputs)}:v=1:a=0,fps=30,format=yuv420p[out]')
    cmd.extend(['-filter_complex',';'.join(filters),'-map','[out]','-an','-frames:v','3600','-r','30','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-threads','4','-movflags','+faststart',str(video_path)])
    run(cmd,timeout=2400)
    q=probe(video_path);v=q['streams'][0]
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==('h264',1920,1080,'30/1',3600),q
    assert abs(float(q['format']['duration'])-120)<.06,q
    return video_path

def audio(video_path,voices):
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y']
    for p in [video_path,FIRST,*voices,SFX]:cmd.extend(['-i',str(p)])
    f=['[1:a]atrim=0:30,asetpts=PTS-STARTPTS,aresample=48000[approved]']
    labels=['[approved]']
    for i,v in enumerate(M['tts']['segments']):
        ms=round(v['global_onset_seconds']*1000)
        f.append(f'[{i+2}:a]aresample=48000,volume=1.0,adelay={ms}:all=1[s{i}]')
        labels.append(f'[s{i}]')
    sfx_idx=len(voices)+2
    f.append(f'[{sfx_idx}:a]aresample=48000,volume=0.31,afade=t=in:st=0:d=0.4,afade=t=out:st=89.25:d=0.75,adelay=30000:all=1[amb]')
    labels.append('[amb]')
    f.append(''.join(labels)+f'amix=inputs={len(labels)}:duration=longest:dropout_transition=0,alimiter=limit=0.95,atrim=0:120,asetpts=N/SR/TB[mix]')
    cmd.extend(['-filter_complex',';'.join(f),'-map','0:v:0','-map','[mix]','-c:v','copy','-c:a','aac','-b:a','192k','-t','120','-movflags','+faststart',str(OUT)])
    run(cmd,timeout=600)

def post_qa():
    p=OUT;q=probe(p)
    v=next(s for s in q['streams'] if s['codec_type']=='video')
    a=next(s for s in q['streams'] if s['codec_type']=='audio')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==('h264',1920,1080,'30/1',3600),v
    assert a['codec_name']=='aac' and abs(float(q['format']['duration'])-120)<.10,q
    raw=subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','packet=dts_time','-of','csv=p=0',str(p)],text=True)
    dts=[float(line.strip()) for line in raw.splitlines() if line.strip() not in ('N/A','')]
    assert len(dts)==3600 and all(b>a for a,b in zip(dts,dts[1:])),('Nonmonotonic DTS',len(dts))
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-i',str(p),'-f','null','-'],check=True,timeout=900)
    decoded=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames','-of','json',str(p)],text=True))
    assert int(decoded['streams'][0]['nb_read_frames'])==3600
    stamps=[.6,9.2,19.2,29.5,31.4,35.3,39.0,43.8,47.2,53.0,59.6,62.4,66.0,70.1,76.2,80.7,84.1,88.0,92.4,97.0,102.0,106.5,110.2,114.8,119.1]
    contact=Image.new('RGB',(1920,5*265),'#0d1b2a');d=ImageDraw.Draw(contact)
    for i,t in enumerate(stamps):
        b=subprocess.check_output(['ffmpeg','-hide_banner','-loglevel','error','-ss',str(t),'-i',str(p),'-frames:v','1','-f','image2pipe','-vcodec','mjpeg','-'],timeout=60)
        assert len(b)>1000 and b[:2]==b'\xff\xd8',(t,len(b))
        im=ImageOps.fit(Image.open(io.BytesIO(b)).convert('RGB'),(384,216))
        x=(i%5)*384;y=(i//5)*265
        contact.paste(im,(x,y+27));d.text((x+10,y+5),f'{t:.1f} seconds',fill='white')
    contact.save(DELIVERY/'RAIN_V4_FIRST120_CONTACT_SHEET.jpg',quality=90)
    report={
     'status':'TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED','title':M['project'],'duration_seconds':float(q['format']['duration']),
     'frames':3600,'fps':30,'width':1920,'height':1080,'video_codec':'h264','audio_codec':'aac',
     'strict_video_dts_monotonic':True,'decoded_video_frames':3600,'frame_seek_contact_sheet':'PASS 25 distinct expected points',
     'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_first30_sha256':M['approved_first30_sha256'],
     'first30_visually_reused_from_original':True,'first30_reencoded_to_normalize_timestamp_base':True,
     'continuation_shards':18,'new_frames':2700,'voice_segments':5,'voice_source_seconds':sum(x['duration_seconds'] for x in M['tts']['segments']),
     'voice_last_phrase_end_sec':M['tts']['segments'][-1]['global_end_seconds'],'new_spent_credits':M['spending']['new_tts_credits'],
     'previous_spent_credits':M['spending']['preexisting_0to30_credits'],
     'known_total_project_tts_credits':M['spending']['new_tts_credits']+M['spending']['preexisting_0to30_credits'],
     'paid_image_generation_credits_this_continuation':0,'model_substitutions':0,'paid_retries':0,
     'still_character_rule':'V4 scene definition; excluded animation not automatically proven by metadata',
     'narration_word_alignment':'USING_MEASURED_SEGMENT_DURATIONS; detailed word-level alignment NOT independently verified',
     'normal_speed_creative_review':'REQUIRED_USER_APPROVAL','sound_mix_listening_review':'UNVERIFIED'
    }
    (DELIVERY/'RAIN_V4_FIRST120_QA.json').write_text(json.dumps(report,indent=2)+'\n')
    (DELIVERY/'RAIN_V4_FIRST120_TIMELINE.json').write_text(json.dumps(M,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)
    return report

def main():
    shorts,voices=verify()
    v=video(shorts)
    audio(v,voices)
    post_qa()
    # Intermediate silent master is not a delivery artifact; save storage and transfer.
    v.unlink(missing_ok=True)

if __name__=='__main__':main()
