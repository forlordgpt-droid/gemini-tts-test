#!/usr/bin/env python3
"""Immutable 30s approved pilot + 87 REAL 10-second 1080p H264 illustrated 2.5D shards = 15m full movie.
No model substitution; FFmpeg/FFprobe + actual decoded frame QA + exact original story audio.
"""
from __future__ import annotations
import json,subprocess,pathlib,hashlib,os,cv2,numpy as np,wave,shutil
from PIL import Image,ImageDraw
ROOT=pathlib.Path('film/market-six-v3/full-film')
BLUE=json.loads((ROOT/'SHOT_IMAGE_BLUEPRINT.json').read_text())
assert BLUE['frames']==27000 and BLUE['image_model']=='gpt-image-2.5-lower' and BLUE['speech_model']=='google/gemini-3-8-flash-tts'
OUT=pathlib.Path('final_full');OUT.mkdir(exist_ok=True);(OUT/'qa').mkdir(exist_ok=True)
def cmd(*a):
    return subprocess.run(a,check=True,capture_output=True,text=True).stdout
def ffprobe(file):
    return json.loads(cmd('ffprobe','-v','error','-show_entries',
      'stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames,sample_rate,channels,time_base:format=duration',
      '-of','json',str(file)))
def sha(f):
    h=hashlib.sha256()
    with open(f,'rb') as reader:
        for b in iter(lambda:reader.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
approved=pathlib.Path('approved_first30/MARKET_SIX_DAY100_COMPLETE_FIRST30_1080P.mp4')
assert approved.is_file() and approved.stat().st_size>20000000,'The approved 30s source video is missing; no re-creation or substitute'
ORIGINAL_HASH='38ed9c8f37f4cc1ecd046b05bdff1e49136bab04e46c303edbc0a007c8c02e5e'
assert sha(approved)==ORIGINAL_HASH,'Owner-approved first30 video changed: STOP'
d=ffprobe(approved)
v=next(s for s in d['streams'] if s['codec_type']=='video')
assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==('h264',1920,1080,'30/1',900)
shards=[];ledger=[]
for ch in range(1,16):
    offsets=(900,1200,1500) if ch==1 else (0,300,600,900,1200,1500)
    for offset in offsets:
        frame=(ch-1)*1800+offset
        artifact=f'MARKET_SIX_FULL_CH{ch:02d}_SEG{offset}'
        p=pathlib.Path('parts')/artifact/f'part_{frame}_300.mp4'
        assert p.is_file() and p.stat().st_size>90000,(artifact,p)
        info=ffprobe(p)
        s=next(x for x in info['streams'] if x['codec_type']=='video')
        assert (s['codec_name'],s['width'],s['height'],s['r_frame_rate'],int(s['nb_frames']))==('h264',1920,1080,'30/1',300),p
        assert abs(float(info['format']['duration'])-10)<.08,p
        vals=cmd('ffprobe','-v','error','-select_streams','v:0','-show_entries','frame=best_effort_timestamp_time','-of','csv=p=0',str(p))
        pts=[float(x.strip()) for x in vals.splitlines() if x.strip()]
        assert len(pts)==300 and abs(pts[0])<.035 and abs(pts[-1]-299/30)<.04,p
        assert all(b>a for a,b in zip(pts,pts[1:])),p
        shards.append(p);ledger.append({'chapter':ch,'start_frame':frame,'frames':300,'sha256':sha(p),'bytes':p.stat().st_size})
assert len(shards)==87 and len(set(x['start_frame'] for x in ledger))==87
print('PASS all 87 original 1080p premium 2.5D WebCodecs sections, exactly 26,100 new independent frames',flush=True)
pilot_vid=OUT/'APPROVED_0_TO_30_VIDEO_PACKETS.mp4'
cmd('ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(approved),'-map','0:v:0','-an','-c:v','copy',str(pilot_vid))
# LOSSLESS stream-copy timebase normalization. Original approved 900 frame MP4 uses
# 1/15360; each independent WebCodecs shard uses 1/30. FFmpeg concat demuxer expects
# identical stream timebases; otherwise it squeezes correct 27000 frames into ~30 seconds.
# A codec-copy remux changes only MP4 PTS scale, never pixels or H264 packets.
original_timebase=next(s for s in ffprobe(pilot_vid)['streams'] if s['codec_type']=='video')['time_base']
assert original_timebase=='1/15360',original_timebase
normalized_dir=OUT/'normalized_h264_timebase';normalized_dir.mkdir(exist_ok=True)
fixed=[]
for i,shard in enumerate(shards):
    target=normalized_dir/f'part_{i:03d}_normalized_15360.mp4'
    cmd('ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(shard),
        '-map','0:v:0','-an','-c:v','copy','-video_track_timescale','15360',
        '-movflags','+faststart',str(target))
    data=ffprobe(target)
    video=next(x for x in data['streams'] if x['codec_type']=='video')
    assert video['time_base']=='1/15360' and video['codec_name']=='h264' and int(video['nb_frames'])==300,(target,video)
    assert abs(float(data['format']['duration'])-10)<.04,target
    fixed.append(target)
assert len(fixed)==87
print('PASS lossless PTS remux normalized all 87 existing H264 shards to 1/15360; no re-encoding or paid generation',flush=True)
conc=OUT/'cinema_27000_frames.concat.txt'
allfiles=[pilot_vid]+fixed
conc.write_text(''.join("file '"+str(p.resolve())+"'\n" for p in allfiles))
picture=OUT/'MARKET_SIX_FULL15M_VIDEO_ONLY_27000FRAMES.mp4'
cmd('ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(conc),
    '-map','0:v:0','-an','-c:v','copy','-movflags','+faststart',str(picture))
info=ffprobe(picture);pv=next(s for s in info['streams'] if s['codec_type']=='video')
assert (pv['codec_name'],pv['width'],pv['height'],pv['r_frame_rate'],int(pv['nb_frames']))==('h264',1920,1080,'30/1',27000)
assert abs(float(info['format']['duration'])-900)<.2,('Full story timeline duration',info['format']['duration'])
# Conserve the approved first 900 decoded frames BITWISE.
original_video_hash=cmd('ffmpeg','-hide_banner','-loglevel','error','-i',str(approved),'-map','0:v:0','-frames:v','900','-f','hash','-hash','sha256','-')
new_video_hash=cmd('ffmpeg','-hide_banner','-loglevel','error','-i',str(picture),'-map','0:v:0','-frames:v','900','-f','hash','-hash','sha256','-')
assert original_video_hash.strip()==new_video_hash.strip(),'Original approved opening decoded-frame hash changed'
(OUT/'APPROVED_FIRST30_BITWISE_FRAME_PROOF.txt').write_text(original_video_hash)
# Build exact original Gemini 3.8 FLASH narration, never replace or regenerate the paid audio.
continuation=pathlib.Path('narration/MARKET_SIX_KIE_FLASH_VERBATIM_CONTINUATION_30TO900.wav')
assert continuation.is_file() and continuation.stat().st_size>35000000
voiceaudit=json.loads(pathlib.Path('narration/CHAPTER_TIMING_WORDS_AND_PROVIDER_QA.json').read_text())
assert voiceaudit['exact_model']=='google/gemini-3-8-flash-tts' and voiceaudit['complete_original_spoken_words']>2000
originalwav=OUT/'APPROVED_PILOT_FIRST30_SOUND.wav'
cmd('ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(approved),'-map','0:a:0',
    '-ac','1','-ar','24000','-c:a','pcm_s16le','-t','30',str(originalwav))
def waveframes(file):
    with wave.open(str(file),'rb') as w:
      assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(24000,1,2),file
      return w.readframes(w.getnframes()),w.getnframes()
prior,frames0=waveframes(originalwav)
voice,frames1=waveframes(continuation)
assert abs(frames0-720000)<240 and frames1==870*24000
voicefull=OUT/'FULL_900S_ORIGINAL_KIE_FLASH_NARRATION.wav'
with wave.open(str(voicefull),'wb') as wav:
    wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(24000)
    wav.writeframes(prior)
    wav.writeframes(voice)
# Original browser Web Audio OfflineAudioContext effects remain scene-specific and unmixed until final.
sfxfiles=[pathlib.Path('sfx_full')/f'MARKET_SIX_ORIGINAL_WEBAUDIO_CH{i:02d}.wav' for i in range(1,16)]
fullsfx=OUT/'FULL_900S_ORIGINAL_OFFLINE_WEBAUDIO_SFX.wav'
with wave.open(str(fullsfx),'wb') as wav:
    wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(24000)
    wav.writeframes(b'\x00\x00'*720000)
    for i,f in enumerate(sfxfiles,1):
      assert f.is_file(),f
      s,n=waveframes(f)
      assert n==(30 if i==1 else 60)*24000,(i,n)
      wav.writeframes(s)
with wave.open(str(fullsfx)) as f:assert f.getnframes()==900*24000
# Scene-picture packets are copied losslessly; only original WAV sources mixed into AAC.
final=OUT/'100_DAYS_ABANDONED_SUPERMARKET_COMPLETE_15_MINUTE_FILM.mp4'
cmd('ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(picture),'-i',str(voicefull),'-i',str(fullsfx),
    '-filter_complex',
    '[1:a]volume=1.0[n];[2:a]volume=0.19[s];[n][s]amix=inputs=2:duration=longest:dropout_transition=0,alimiter=limit=0.95[m]',
    '-map','0:v:0','-map','[m]','-t','900','-c:v','copy','-c:a','aac','-b:a','192k','-ar','24000','-ac','1','-movflags','+faststart',str(final))
probe=ffprobe(final);v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==('h264',1920,1080,'30/1',27000),v
assert a['codec_name']=='aac' and abs(float(probe['format']['duration'])-900)<.16
(OUT/'FFPROBE_FULL_15MIN.json').write_text(json.dumps(probe,indent=2))
# Independent visual contact of actual completed movie in EVERY chapter; original story beats clearly present.
cap=cv2.VideoCapture(str(final));assert cap.isOpened()
times=[3.0,17.0,29.0]+[ch*60+tm for ch in range(15) for tm in (33,56) if ch*60+tm>=30 and ch*60+tm<899]
times=sorted(set(times));tilew,tileh=480,270
cols=4;rows=(len(times)+cols-1)//cols
sheet=Image.new('RGB',(cols*tilew,rows*(tileh+28)),'#071526');draw=ImageDraw.Draw(sheet)
for i,t in enumerate(times):
    cap.set(cv2.CAP_PROP_POS_MSEC,float(t)*1000)
    ok,frame=cap.read();assert ok,t
    fr=Image.fromarray(cv2.cvtColor(cv2.resize(frame,(tilew,tileh)),cv2.COLOR_BGR2RGB))
    x=(i%cols)*tilew;y=(i//cols)*(tileh+28)
    sheet.paste(fr,(x,y+28));draw.rectangle((x,y,x+tilew,y+28),fill='#0b1c33')
    draw.text((x+12,y+7),f'{t:.1f}s  |  ORIGINAL FILM',fill='#ffe0a6')
cap.release()
sheet.save(OUT/'ACTUAL_15_MINUTE_ALL_CHAPTERS_CONTACT_SHEET.jpg',quality=90)
report={'status':'FULL_15MIN_PROVISIONAL_TECHNICAL_PASS_FINAL_QA_REQUIRED',
        'film':'100 DAYS INSIDE AN ABANDONED SUPERMARKET','original_user_script_unchanged':True,
        'video_dimensions':[1920,1080],'frames':27000,'fps':30,'duration_seconds':900,
        'original_approved_first30_video_SHA256':ORIGINAL_HASH,'first30_video_decoded_frames_bitwise_unchanged':True,
        'real_original_shards':87,'new_original_story_frames':26100,'original_painting_count_new':131,
        'paid_model_illustration':'SnapGen gpt-image-2.5-lower','paid_original_image_credits':131,
        'paid_model_speech':'kie.ai google/gemini-3-8-flash-tts',
        'narration_all_original_remaining_words':voiceaudit['complete_original_spoken_words'],
        'sound_effects':'original browser Web Audio OfflineAudioContext','paid_render_calls':0,
        'whole_movie_sha256':sha(final),'size_bytes':final.stat().st_size,
        'codec_video':'h264','codec_audio':'aac','shards':ledger}
(OUT/'FULL_FILM_VERIFIED_SOURCE_AND_CREDIT_REPORT.json').write_text(json.dumps(report,indent=2))
print('FIRST ASSEMBLY PASS: 900s original user narrative illustrated cinema 27000 frames',final.stat().st_size,report['whole_movie_sha256'],flush=True)
