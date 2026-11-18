#!/usr/bin/env python3
"""Prepare 30–900s ORIGINAL Kie Gemini 3.8 Flash narration without source-word alteration.
All original 15 chapter WAVs are already generated and audited; this script uses only
FFmpeg atempo, loudness normalization, FFprobe, and Python's PCM wave concatenation.
"""
from __future__ import annotations
import json,pathlib,subprocess,wave,math,hashlib,struct
ROOT=pathlib.Path('film/market-six-v3/full-film')
m=json.loads((ROOT/'ORIGINAL_STORY_SPOKEN_TURNS.json').read_text())
assert m['exact_model']=='google/gemini-3-8-flash-tts' and len(m['chapters'])==15
OUT=pathlib.Path('narration');OUT.mkdir(parents=True,exist_ok=True)
def cmd(*args):
    p=subprocess.run(args,check=True,capture_output=True,text=True)
    return p.stdout
def probe(f):
    return json.loads(cmd('ffprobe','-v','error','-show_entries',
         'stream=codec_name,codec_type,sample_rate,channels:format=duration','-of','json',str(f)))
reports=[];parts=[];framecount=0
for c in m['chapters']:
    i=c['chapter'];ch=f'ch{i:02d}'
    inf=pathlib.Path('voice')/ch/f'chapter_{i:02d}_EXACT_KIE_GEMINI38_FLASH.wav'
    auditf=pathlib.Path('voice')/ch/'CHAPTER_TTS_QA_AND_CREDITS.json'
    if not inf.is_file() or not auditf.is_file():raise FileNotFoundError(f'Missing original paid provider audio for {ch}; STOP no paid retry')
    a=json.loads(auditf.read_text())
    assert a['status']=='SUCCESS_ONCE' and a['model']=='google/gemini-3-8-flash-tts'
    assert a['provider']=='kie.ai' and a['create_task_attempts']==1 and a['paid_auto_retries']==0
    assert a['source_words']==c['total_source_words'] and a['chapter']==i
    assert hashlib.sha256(inf.read_bytes()).hexdigest()==a['audio_sha256']
    orig=float(probe(inf)['format']['duration'])
    target=float(c['target_duration_sec'])
    desired=target-1.0 if i==1 else target-1.4
    # Preserve all articulated sentences in their order; speed just enough to hit scene clock.
    # A mild slow-down only when source output is slightly short; otherwise leave natural pace.
    tempo=max(.88,orig/desired)
    if tempo>1.62:raise RuntimeError(f'Generated Kie narration for chapter {i} too long for faithful 60sec time without overly rushed tempo: {orig:.2f}s, speed {tempo:.3f}; STOP and diagnose')
    out=OUT/f'ch{i:02d}_exact_original_synced.wav'
    # resample/filter/trim ONLY trailing padding; never split or delete actual source text.
    filter=f'aresample=24000,atempo={tempo:.6f},loudnorm=I=-18:TP=-2:LRA=9,apad=whole_dur={target:.3f},atrim=duration={target:.3f},asetpts=N/SR/TB'
    cmd('ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(inf),'-af',filter,
        '-c:a','pcm_s16le','-ar','24000','-ac','1',str(out))
    with wave.open(str(out),'rb') as w:
        assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(24000,1,2)
        frames=w.getnframes()
    assert abs(frames/24000-target)<.002,(i,frames,target)
    parts.append(out);framecount+=frames
    reports.append({'chapter':i,'source_original_words':c['total_source_words'],'source_original_seconds':orig,
                    'time_stretch_factor':round(tempo,6),'final_scene_duration_sec':target,
                    'source_original_kie_model':a['model'],'source_task_id':a['task_id'],'voice':a['voice_map'],
                    'source_wav_sha256':a['audio_sha256'],'source_text_unchanged':True,
                    'track_sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
    print('KIE ORIGINAL NARRATION PRESERVED',i,'source',round(orig,2),'target',target,'speed',round(tempo,3),flush=True)
final=OUT/'MARKET_SIX_KIE_FLASH_VERBATIM_CONTINUATION_30TO900.wav'
with wave.open(str(final),'wb') as output:
    output.setnchannels(1);output.setsampwidth(2);output.setframerate(24000)
    for f in parts:
        with wave.open(str(f),'rb') as source:
            output.writeframes(source.readframes(source.getnframes()))
with wave.open(str(final),'rb') as fin:
    assert (fin.getnframes(),fin.getframerate())==(870*24000,24000)
assert float(probe(final)['format']['duration'])==870
audit={'status':'ALL_15_EXACT_ORIGINAL_CHAPTER_KIE_FLASH_NARRATIONS_ALIGNED','provider':'kie.ai',
       'exact_model':'google/gemini-3-8-flash-tts','chapters':15,'complete_original_spoken_words':sum(c['total_source_words'] for c in m['chapters']),
       'original_first30_preserved_separately':True,'duration_remaining_seconds':870,'sample_rate_hz':24000,
       'sequential_source_words_preserved':True,'new_paid_tasks':0,'chapter_reports':reports,
       'full_voice_sha256':hashlib.sha256(final.read_bytes()).hexdigest()}
(OUT/'CHAPTER_TIMING_WORDS_AND_PROVIDER_QA.json').write_text(json.dumps(audit,indent=2))
print('PASS EXACT KIE GEMINI 3.8 FLASH FULL 870S REMAINING ORIGINAL SOURCE SPEECH ALL WORDS',flush=True)
