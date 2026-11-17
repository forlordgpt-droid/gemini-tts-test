#!/usr/bin/env python3
"""ONE authorized Kie.ai google/gemini-3-8-flash-tts multi-speaker request.
No other model; no paid retries; audit pre/post Kie balance. Original story lines only.
"""
import json,os,time,sys,wave,urllib.error,urllib.request,urllib.parse
from pathlib import Path

MODEL='google/gemini-3-8-flash-tts'
API='https://api.kie.ai'
OUT=Path('kie_one_task');OUT.mkdir(exist_ok=True)
manifest=json.loads(Path('film/last-safe-room-30s/tts/APPROVED_KIE_FLASH_TTS_ONE_TASK.json').read_text())
assert manifest['model']==MODEL
assert manifest['provider']=='kie.ai'
assert manifest['approved_generation_jobs']==1 and manifest['maximum_kie_credits']==5
assert len(manifest['dialogue'])==3
assert [x['speaker_id'] for x in manifest['dialogue']]==['Speaker 1','Speaker 2','Speaker 1']
assert [x['text'] for x in manifest['dialogue']]==[
    'Emma! The gas is moving faster. Get underground!',
    "Noah! It's locked!",
    "There's an emergency tunnel behind you!"
]
assert os.environ.get('GITHUB_RUN_NUMBER')=='1', 'One paid job only: workflow run_number must be 1'
assert os.environ.get('GITHUB_RUN_ATTEMPT')=='1', 'Refuse paid generation on retry'
key=os.environ.get('KIE_API_KEY','').strip()
assert len(key)>15,'Missing KIE_API_KEY secret: stop without substitutions'

def api(path,body=None):
    data=json.dumps(body,separators=(',',':')).encode() if body is not None else None
    headers={'Authorization':'Bearer '+key,'Accept':'application/json'}
    if data is not None: headers['Content-Type']='application/json'
    request=urllib.request.Request(API+path,data=data,headers=headers,method='POST' if data is not None else 'GET')
    try:
        with urllib.request.urlopen(request,timeout=45) as r:
            response=json.load(r)
    except urllib.error.HTTPError as exc:
        raise RuntimeError('Kie HTTP '+str(exc.code)+' '+exc.read(350).decode(errors='replace')) from None
    if response.get('code')!=200:
        raise RuntimeError('Kie API code '+str(response.get('code'))+' '+str(response.get('msg')))
    return response['data']

prior=float(api('/api/v1/chat/credit'))
if prior<5:
    raise RuntimeError('Kie balance under approved 5-credit headroom; no task submitted')
spoken_words=sum(len(x['text'].split()) for x in manifest['dialogue'])
assert spoken_words==17
# Kie's published rates: 70/M text input, 1260/M audio-output credits.
# A 60-second conservative budget at 25 audio tokens/s is <2 credits;
# 5 credits correspond to over 2 minutes of generated speech, far more than 17 words.
estimated_upper=((700*70)+(60*25*1260))/1_000_000
assert estimated_upper<manifest['maximum_kie_credits'], estimated_upper
print('PREFLIGHT: provider kie.ai model',MODEL,'original spoken words',spoken_words,'estimated conservative max 60s credits',estimated_upper,'credit ceiling',manifest['maximum_kie_credits'],flush=True)
# Use known prebuilt male/female Google voices; voice actor styling is not extra spoken dialogue.
# Long pauses give editorial separation so three utterances can be precisely moved to script timestamps.
payload={
 'model':MODEL,
 'input':{
  'temperature':1,
  'speakers':[
    {'speaker_id':'Speaker 1','voice_name':'Charon'},
    {'speaker_id':'Speaker 2','voice_name':'Kore'}
  ],
  'dialogue_turns':[
    {'speaker_id':'Speaker 1',
     'style':'American male voice, urgent and tense over a phone, fast intelligible delivery. Keep exact words, no filler, then leave a distinct quiet pause.',
     'text':'Emma! The gas is moving faster. Get underground! <long pause>'},
    {'speaker_id':'Speaker 2',
     'style':'American young adult female, frightened breathless yell, sharp emotional urgency. Exact words only. Then leave a distinct quiet pause.',
     'text':"Noah! It's locked! <long pause>"},
    {'speaker_id':'Speaker 1',
     'style':'Same American male phone voice, alarmed and clear, quick pace. Exact words only, no added reactions.',
     'text':"There's an emergency tunnel behind you!"}
  ]
 }
}
(OUT/'request_redacted.json').write_text(json.dumps(payload,indent=2))
print('PRE_TASK_CREDITS',prior,flush=True)
# Exactly ONE createTask attempt. Do not automatically retry on error.
task=api('/api/v1/jobs/createTask',payload)
task_id=task.get('taskId')
if not task_id:
    raise RuntimeError('Kie did not return taskId; no repeat createTask permitted')
(OUT/'CREATED_TASK.json').write_text(json.dumps({'task_id':task_id,'model':MODEL,'first_known_balance':prior,'request_count':1},indent=2))
print('ONE_AND_ONLY_PAID_TASK_ID',task_id,flush=True)
result=None
for i in range(95):
    result=api('/api/v1/jobs/recordInfo?'+urllib.parse.urlencode({'taskId':task_id}))
    state=result.get('state')
    if i%4==0:print('task_poll',i,'state',state,flush=True)
    if state=='success':break
    if state=='fail':
        raise RuntimeError('Kie generated task failed; WILL NOT CREATE SECOND TASK: '+str(result.get('failMsg') or result.get('failCode')))
    if state not in ('waiting','queuing','generating'):
        raise RuntimeError('Unrecognized Kie state '+str(state)+'; WILL NOT RETRY GENERATION')
    time.sleep(4)
else:
    raise RuntimeError('Task pending after polling. Continue polling task_id ONLY, no second generation.')
result_json=result.get('resultJson') or result.get('response') or {}
if isinstance(result_json,str):result_json=json.loads(result_json)
urls=result_json.get('resultUrls') or []
assert urls and len(urls)>0,'Successful Kie task has no WAV URL'
with urllib.request.urlopen(urls[0],timeout=100) as r:
    wav_bytes=r.read()
assert wav_bytes[:4]==b'RIFF' and wav_bytes[8:12]==b'WAVE'
out=OUT/'NOAH_EMMA_ONE_KIE_3_8_FLASH_MULTISPEAKER.wav'
out.write_bytes(wav_bytes)
with wave.open(str(out),'rb') as w:
    sr=w.getframerate();channels=w.getnchannels();width=w.getsampwidth()
    length=w.getnframes()/sr
assert sr==24000 and channels==1 and width==2,(sr,channels,width)
assert 2<length<100,'Unreasonable 17-word dialogue duration '+str(length)
after=float(api('/api/v1/chat/credit'))
spent=max(0,round(prior-after,4))
audit={
 'model':MODEL,'provider':'kie.ai','request_count':1,'task_id':task_id,
 'credits_before':prior,'credits_after':after,'observed_balance_delta':spent,
 'approved_max_credits':5,'published_rates_credits_per_million':{'text':70,'audio_output':1260},
 'audio_seconds':round(length,3),'sample_rate':sr,'channels':channels,'bit_depth':16,
 'speakers':{'NOAH':'Charon','EMMA':'Kore'},
 'lines':[x['text'] for x in manifest['dialogue']],
 'one_task_no_retry':True,'wav_file':out.name
}
(OUT/'KIE_COST_AND_SOURCE_AUDIT.json').write_text(json.dumps(audit,indent=2))
print('KIE_RESULT_AUDIT',json.dumps(audit),flush=True)
if spent>5:
    raise RuntimeError('Kie usage exceeded 5-credit authorization; STOP, no further API calls')
print('SUCCESS exactly one approved Kie Gemini 3.8 Flash task, 2 speakers, 3 lines, within 5 credits',flush=True)
