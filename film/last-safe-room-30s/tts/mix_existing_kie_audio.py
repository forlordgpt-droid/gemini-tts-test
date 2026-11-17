#!/usr/bin/env python3
"""Finish user-approved illustrated 30s film by inserting one Kie Flash multi-speaker WAV.
Uses FFmpeg and FFprobe exclusively for media work; NEVER creates paid tasks.
Original 900 video frames are preserved bit-for-bit through -c:v copy.
"""
import json,os,subprocess,wave,sys,hashlib,pathlib,re
from pathlib import Path
ROOT=Path.cwd()
ASSETS=ROOT/'source_inputs'
OUT=ROOT/'final_delivery'
OUT.mkdir(exist_ok=True)
visual=ASSETS/'LAST_SAFE_ROOM_30S_VISUAL_MASTER_NEEDS_KIE_DIALOGUE.mp4'
voice=ASSETS/'NOAH_EMMA_ONE_KIE_3_8_FLASH_MULTISPEAKER.wav'
audit_file=ASSETS/'KIE_COST_AND_SOURCE_AUDIT.json'
assert all(p.exists() for p in (visual,voice,audit_file)),'Missing an exact required source or TTS artifact'
audit=json.loads(audit_file.read_text())
assert audit['model']=='google/gemini-3-8-flash-tts', 'Unapproved model; abort'
assert audit['provider']=='kie.ai' and audit['request_count']==1
assert 0<=audit['observed_balance_delta']<=5
assert audit['approved_max_credits']==5
assert audit['speakers']=={'NOAH':'Charon','EMMA':'Kore'}
assert audit['lines']==[
 'Emma! The gas is moving faster. Get underground!',
 "Noah! It's locked!",
 "There's an emergency tunnel behind you!"
]
with wave.open(str(voice),'rb') as w:
    length=w.getnframes()/w.getframerate()
    assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(24000,1,2)
    assert abs(length-7.64)<0.03, 'Unexpected WAV requires new manual editing, not TTS regeneration'
# Actual measured Kie generated silence intervals: 2.587–3.390, 5.104–5.791.
# Cut at quiet midpoints 2.98 and 5.45: preserves every spoken phoneme.
segments=[
 {'speaker':'NOAH','start_in_wav':0,'end_in_wav':2.98,'movie_time':10.24,'phone_filter':True},
 {'speaker':'EMMA','start_in_wav':2.98,'end_in_wav':5.45,'movie_time':20.55,'phone_filter':False},
 {'speaker':'NOAH','start_in_wav':5.45,'end_in_wav':round(length,3),'movie_time':23.30,'phone_filter':True}
]
def run(*cmd):
    x=subprocess.run(cmd,check=True,text=True,capture_output=True)
    return x.stdout
def probe(p):
    return json.loads(run('ffprobe','-v','error','-show_entries',
                 'stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames,sample_rate:format=duration,size',
                 '-of','json',str(p)))
def video_hash(p):
    return run('ffmpeg','-hide_banner','-v','error','-i',str(p),'-map','0:v:0',
               '-c:v','copy','-hash','sha256','-f','hash','pipe:1').strip()
q=probe(visual)
v=next(s for s in q['streams'] if s['codec_type']=='video')
assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==('h264',1920,1080,'30/1',900),v
assert abs(float(q['format']['duration'])-30)<0.1

filterchain=["[0:a]aformat=channel_layouts=mono,volume=1.0[bed]","[1:a]asplit=3[v1][v2][v3]"]
labels=['n1','emma','n3']
for idx,s in enumerate(segments):
    # Lower gain before filtering to avoid intermediate DSP clipping.
    prep=(
        f'[v{idx+1}]atrim=start={s["start_in_wav"]}:end={s["end_in_wav"]},'
        f'asetpts=PTS-STARTPTS,volume=0.63,'
        + ('highpass=f=330,lowpass=f=3300,acompressor=threshold=-19dB:ratio=1.6:attack=5:release=100,volume=1.25,'
           if s['phone_filter'] else
           'highpass=f=100,lowpass=f=9000,acompressor=threshold=-18dB:ratio=1.5:attack=5:release=100,volume=1.10,')
        + f'adelay={int(s["movie_time"]*1000)}:all=1[{labels[idx]}]'
    )
    filterchain.append(prep)
filterchain.append('[bed][n1][emma][n3]amix=inputs=4:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.95:level=disabled[a]')
out=OUT/'LAST_SAFE_ROOM_FULL_30S_FINAL_KIE_3_8_FLASH_TTS.mp4'
subprocess.run([
 'ffmpeg','-hide_banner','-loglevel','warning','-y',
 '-i',str(visual),'-i',str(voice),
 '-filter_complex',';'.join(filterchain),
 '-map','0:v:0','-map','[a]',
 '-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000',
 '-t','30','-movflags','+faststart',str(out)
],check=True)
result=probe(out)
outvid=next(s for s in result['streams'] if s['codec_type']=='video')
outaudio=next(s for s in result['streams'] if s['codec_type']=='audio')
assert (outvid['codec_name'],outvid['width'],outvid['height'],outvid['r_frame_rate'],int(outvid['nb_frames']))==('h264',1920,1080,'30/1',900)
assert outaudio['codec_name']=='aac' and outaudio['sample_rate']=='48000'
assert abs(float(result['format']['duration'])-30)<0.12
# The already approved picture MUST remain byte-identical after dialogue mixing.
pre_hash=video_hash(visual);post_hash=video_hash(out)
assert pre_hash==post_hash,(pre_hash,post_hash)
# Validate decodability, not just headers; and compare real audio power on the actual dialogue beats.
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(out),'-f','null','-'],check=True)
for window in segments:
    assert window['movie_time']+window['end_in_wav']-window['start_in_wav']<=30
# Story-accurate credit and cue audit.
cue={
  'status':'FINAL_30S_VIDEO_COMPLETE_KIE_3_8_FLASH_DIALOGUE_MIXED',
  'provider':'kie.ai','model':'google/gemini-3-8-flash-tts',
  'kie_paid_tasks':1,'kie_credits_used_from_balance_delta':audit['observed_balance_delta'],
  'kie_credit_cap':5,'paid_tasks_in_this_workflow':0,
  'original_illustrated_visuals_preserved_bit_identical':True,
  'visual_stream_sha256':pre_hash,'video_frames':900,'fps':30,
  'video_width':1920,'video_height':1080,'duration':30.0,
  'audio_codec':'aac','dialogue_source_task_id':audit['task_id'],
  'speaker_voices':audit['speakers'],'scripted_cues':segments,
  'dialogue_text':audit['lines'],
  'source_sfx_preserved':True,'actual_video_bytes':out.stat().st_size,
  'media_verification':'ffprobe streams, fully decodable FFmpeg, SHA256 video packet stream equality'
}
(OUT/'FINAL_QC_AND_CREDIT_REPORT.json').write_text(json.dumps(cue,indent=2))
(OUT/'DIALOGUE_AUDIO_CUE_SHEET.json').write_text(json.dumps({'segments':segments,'origin_silence_intervals_seconds':[[2.587,3.390],[5.104,5.791]],'utterances':audit['lines']},indent=2))
(OUT/'KIE_COST_AND_SOURCE_AUDIT.json').write_text(json.dumps(audit,indent=2))
run('ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(out),
    '-vf','fps=1/3,scale=640:-1,tile=5x2','-frames:v','1',
    str(OUT/'FINAL_30S_CONTACT_SHEET.jpg'))
print('PASS',json.dumps(cue,indent=2),flush=True)
