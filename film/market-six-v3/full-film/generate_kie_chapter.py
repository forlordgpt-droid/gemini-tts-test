#!/usr/bin/env python3
"""One exact-user-approved paid Kie Gemini 3.8 FLASH task per original source chapter.
Preserves verbatim story and all dialogue, never changes model, never repeats a failed paid task.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, time, urllib.request, urllib.error, urllib.parse, wave
from datetime import datetime, timezone

p=argparse.ArgumentParser();p.add_argument('--chapter',required=True,type=int);args=p.parse_args()
ROOT=pathlib.Path('film/market-six-v3/full-film')
manifest=json.loads((ROOT/'ORIGINAL_STORY_SPOKEN_TURNS.json').read_text())
assert manifest['exact_provider']=='kie.ai'
MODEL='google/gemini-3-8-flash-tts'
assert manifest['exact_model']==MODEL
ch=int(args.chapter);assert 1<=ch<=15
entry=manifest['chapters'][ch-1];assert entry['chapter']==ch
turns=entry['turns'];assert turns and 15<=entry['total_source_words']<=175
assert sum(len(t['text'].split()) for t in turns)==entry['total_source_words']
assert os.getenv('GITHUB_RUN_NUMBER')=='1' and os.getenv('GITHUB_RUN_ATTEMPT')=='1',"Do not rerun paid TTS workflow: duplicate jobs prohibited"
out=pathlib.Path('voice')/f'ch{ch:02d}';out.mkdir(parents=True,exist_ok=True)
if (out/'PAID_TASK_ID.json').exists():raise RuntimeError('Prior paid request already present, refuse duplicate charge')
key=os.environ.get('KIE_API_KEY','').strip()
if len(key)<16:raise RuntimeError('Secret KIE_API_KEY absent. Stop, never switch TTS provider or model')
voice_map={'NARRATOR':('Speaker 1','Charon'),'MASON':('Speaker 1','Charon'),
           'RADIO':('Speaker 2','Kore'),'CLARA':('Speaker 2','Kore'),'UNKNOWN VOICE':('Speaker 2','Kore')}
converted=[]
for x in turns:
    speaker,name=voice_map[x['speaker']]
    if x['speaker']=='NARRATOR':
        style='Deep American male cinematic narrator, adult, restrained emotional urgency, immersive survival mystery, warm expressive voice with immaculate clarity, deliberate natural sentence breaks. Consistent Charon voice. Target 154 words per minute. Speak EXACT verbatim original words once; no extra material.'
    elif x['speaker']=='RADIO':
        style='Distinct detached urgent emergency-radio announcement, crisp clear delivery, American female dispatcher, no extra words or preamble.'
    elif x['speaker']=='CLARA':
        style='Clara is a determined American woman in her thirties, emotionally truthful, worried and urgent, concise, exact words.'
    else:
        style='Fearful but gentle frightened survivor speaking softly in darkness, human emotional urgency, exact words.'
    converted.append({'speaker_id':speaker,'style':style,'text':x['text']})
payload={'model':MODEL,'input':{'temperature':1,'speakers':[
    {'speaker_id':'Speaker 1','voice_name':'Charon'},
    {'speaker_id':'Speaker 2','voice_name':'Kore'}],
    'dialogue_turns':converted}}
def request(path,body=None):
    data=json.dumps(body,separators=(',',':')).encode() if body is not None else None
    head={'Authorization':'Bearer '+key,'Accept':'application/json'}
    if data is not None:head['Content-Type']='application/json'
    req=urllib.request.Request('https://api.kie.ai'+path,data=data,headers=head,method='POST' if data is not None else 'GET')
    try:
        with urllib.request.urlopen(req,timeout=65) as r:obj=json.load(r)
    except urllib.error.HTTPError as exc:
        raise RuntimeError('Kie HTTP '+str(exc.code)+' '+exc.read(350).decode(errors='replace')) from None
    if obj.get('code')!=200:raise RuntimeError('Kie task API '+str(obj.get('code'))+': '+str(obj.get('msg')))
    return obj['data']
before=float(request('/api/v1/chat/credit'))
if before<3:raise RuntimeError('Kie account balance below conservative single 150-word task headroom; do not create paid job')
(out/'EXACT_ORIGINAL_SPEECH.txt').write_text('\n'.join(x['text'] for x in turns)+'\n')
(out/'PUBLIC_GENERATION_REQUEST.json').write_text(json.dumps(payload,indent=2))
print('CHAPTER_TTS_PREFLIGHT',json.dumps({'chapter':ch,'provider':'kie.ai','model':MODEL,'words':entry['total_source_words'],'turns':len(converted),'credit_balance_before':before,'new_jobs':1,'no_auto_retry':True}),flush=True)
task=request('/api/v1/jobs/createTask',payload)
tid=task.get('taskId')
if not tid:raise RuntimeError('No taskId returned, one paid request may already have been charged. Do not retry blindly')
stamp=datetime.now(timezone.utc).isoformat()
(out/'PAID_TASK_ID.json').write_text(json.dumps({'chapter':ch,'taskId':tid,'model':MODEL,'provider':'kie.ai','submitted_at_utc':stamp,'createTask_calls':1,'auto_retries':0},indent=2))
print('CREATED_EXACT_KIE_FLASH_PAID_TASK',ch,tid,flush=True)
for i in range(220):
    state=request('/api/v1/jobs/recordInfo?'+urllib.parse.urlencode({'taskId':tid}))
    status=state.get('state')
    if i%8==0:print('EXISTING_KIE_TASK',ch,tid,status,i,flush=True)
    if status=='success':break
    if status=='fail':raise RuntimeError('Failed exact paid task '+tid+': '+str(state.get('failMsg') or state.get('failCode'))+'; task may not be resubmitted blindly')
    if status not in ('waiting','queuing','generating'):raise RuntimeError('Unknown Kie status '+str(status)+'; no substitutions')
    time.sleep(4)
else:raise RuntimeError('Kie task still active; resume polling SAME task id without recreating')
data=state.get('resultJson') or state.get('response') or {}
if isinstance(data,str):data=json.loads(data)
urls=data.get('resultUrls') or []
if not urls:raise RuntimeError('Kie success but missing WAV; no regeneration')
with urllib.request.urlopen(urls[0],timeout=150) as f:wav_data=f.read()
if wav_data[:4]!=b'RIFF' or wav_data[8:12]!=b'WAVE':raise RuntimeError('Expected exact generated 24kHz PCM WAV')
audio=out/f'chapter_{ch:02d}_EXACT_KIE_GEMINI38_FLASH.wav';audio.write_bytes(wav_data)
with wave.open(str(audio),'rb') as w:
    rate=w.getframerate();channels=w.getnchannels();depth=w.getsampwidth()*8;seconds=w.getnframes()/rate
if (rate,channels,depth)!=(24000,1,16):raise RuntimeError('Kie output format non-compliant')
if not (8<seconds<130):raise RuntimeError('Implausible source speech duration '+str(seconds))
after=float(request('/api/v1/chat/credit'))
report={'chapter':ch,'status':'SUCCESS_ONCE','model':MODEL,'provider':'kie.ai','voice_map':voice_map,
    'dialogue_turn_count':len(turns),'source_words':entry['total_source_words'],
    'source_script_sha256':hashlib.sha256((' '.join(t['text'] for t in turns)).encode()).hexdigest(),
    'task_id':tid,'create_task_attempts':1,'paid_auto_retries':0,
    'duration_sec':round(seconds,4),'channels':channels,'sample_rate_hz':rate,'bit_depth':depth,
    'audio_sha256':hashlib.sha256(wav_data).hexdigest(),'credit_balance_before':before,
    'credit_balance_after':after,
    'credit_delta_concurrent_account_shared':round(before-after,4),
    'credit_delta_caution':'For concurrent jobs account balance deltas may include other chapters: use final aggregate actual spend instead.'}
(out/'CHAPTER_TTS_QA_AND_CREDITS.json').write_text(json.dumps(report,indent=2))
print('SUCCESS_KIE_FLASH_EXACT_STORY',json.dumps({'chapter':ch,'seconds':round(seconds,3),'jobs':1,'model':MODEL,'task_id':tid}),flush=True)
