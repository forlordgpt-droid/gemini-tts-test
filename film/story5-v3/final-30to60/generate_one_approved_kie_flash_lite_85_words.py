#!/usr/bin/env python3
"""One user-authorized paid Kie.ai Gemini 3.8 Flash-Lite SINGLE-narrator request.
Original story5 30–60 exactly, 85 words, no dialogue and no paid retry.
"""
from pathlib import Path
import json,os,time,urllib.request,urllib.parse,urllib.error,hashlib,wave
ROOT=Path("film/story5-v3/final-30to60")
m=json.loads((ROOT/"FINAL_30TO60_APPROVED_PRODUCTION_MANIFEST.json").read_text())
out=Path("emma_story5_final_kie_voice");out.mkdir(exist_ok=True)
model="google/gemini-3-8-flash-lite-tts";voice="Charon"
text=m["source_narration_30_60"]
assert text==m["source_narration_30_45"]+" "+m["source_narration_45_60"]
assert len(text.split())==m["words"]==85
assert m["story_mode"]=="VERBATIM_SINGLE_NARRATOR_NOT_DIALOGUE" and m["narration_voice"]==voice
assert m["tts_model"]==model and m["provider"]=="kie.ai"
c=m["credit_plan"]
assert c["new_tts_jobs_max"]==1 and c["tts_credit_budget_max"]==4 and c["stage_new_credits_cap"]==12
assert c["no_auto_paid_retry"] is True and c["provider_enforces_hard_spend_limit"] is False
assert m["approve_first30"]["do_not_change"] is True
assert os.environ.get("GITHUB_RUN_NUMBER")=="1" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1","No paid job on workflow retries or manual re-run"
key=os.environ.get("KIE_API_KEY","").strip()
if len(key)<16:raise RuntimeError("Missing preinstalled KIE_API_KEY GitHub secret, STOP no substitution")
API="https://api.kie.ai"
def req(path,payload=None):
    data=json.dumps(payload,separators=(",",":")).encode() if payload is not None else None
    h={"Authorization":"Bearer "+key,"Accept":"application/json"}
    if payload is not None:h["Content-Type"]="application/json"
    request=urllib.request.Request(API+path,headers=h,data=data,method="POST" if payload is not None else "GET")
    try:
        with urllib.request.urlopen(request,timeout=45) as resp:answer=json.load(resp)
    except urllib.error.HTTPError as exc:
        raise RuntimeError("Kie HTTP "+str(exc.code)+": "+exc.read(350).decode(errors="replace")) from None
    if answer.get("code")!=200:raise RuntimeError("Kie error "+str(answer.get("code"))+": "+str(answer.get("msg")))
    return answer["data"]
before=float(req("/api/v1/chat/credit"))
assert before>=4,"Kie balance insufficient to guarantee budget headroom"
# Model's current 70/M input, 840/M output. Even 90 sec at 25 output tokens/s <2 credits.
estimated_upper=(1000*70+90*25*840)/1e6
assert estimated_upper<4,estimated_upper
style=("Same single off-screen MALE CHAron narrator as Emma story5 preceding 30s. "
       "Premium immersive suspense thriller with frightened rising tension but clearly intelligible, "
       "brisk naturally paced 190 to 205 spoken words per minute, short precise sentence pauses, "
       "and a chilling quiet final sentence. Read EXACTLY the supplied 85 words, every word once, "
       "no introduction, no additions, no dialogue acting, no name or fictional words beyond source.")
payload={"model":model,"input":{"temperature":1,
  "speakers":[{"speaker_id":"Speaker 1","voice_name":voice}],
  "dialogue_turns":[{"speaker_id":"Speaker 1","style":style,"text":text}]}}
(out/"EXACT_85_WORD_ORIGINAL_NARRATION.txt").write_text(text+"\n")
(out/"TTS_REQUEST_NO_SECRET.json").write_text(json.dumps(payload,indent=2))
print("PAYMENT_PREFLIGHT",json.dumps({"provider":"kie.ai","model":model,"voice":voice,
"new_jobs":1,"word_count":85,"balance_before":before,"estimated_conservative_upper_credits":estimated_upper,
"max_credits_user_stage":4,"no_hard_provider_cap":True,"no_retry":True}),flush=True)
# Single POST only: never retry createTask, even if request is ambiguous/fails.
task=req("/api/v1/jobs/createTask",payload).get("taskId")
if not task:raise RuntimeError("No taskID; STOP never retry createTask")
(out/"TASK_ID_AND_STATUS.json").write_text(json.dumps({"task_id":task,"status":"CREATED","model":model,"submitted_jobs":1,"retry":False},indent=2))
print("APPROVED_PAID_KIE_TASK_ID",task,flush=True)
for i in range(140):
    r=req("/api/v1/jobs/recordInfo?"+urllib.parse.urlencode({"taskId":task}))
    state=r.get("state")
    if i%8==0:print("KIE_TASK_STATE",state,"poll",i,flush=True)
    if state=="success":break
    if state=="fail":raise RuntimeError("Kie task FAILED; no paid retries: "+str(r.get("failMsg") or r.get("failCode")))
    if state not in ("waiting","queuing","generating"):raise RuntimeError("Unexpected status "+str(state)+"; no retries")
    time.sleep(4)
else:raise RuntimeError("Task still active; read-only poll same ID, do not submit again")
parsed=r.get("resultJson") or r.get("response") or {}
if isinstance(parsed,str):parsed=json.loads(parsed)
urls=parsed.get("resultUrls") or []
if not urls:raise RuntimeError("Provider success gave no WAV file; no regeneration")
with urllib.request.urlopen(urls[0],timeout=120) as response:audio=response.read()
assert audio[:4]==b"RIFF" and audio[8:12]==b"WAVE"
filename=out/"EMMA_STORY5_30TO60_KIE_GEMINI38_FLASH_LITE_CHARON.wav"
filename.write_bytes(audio)
with wave.open(str(filename),"rb") as w:sr,ch,width,length=w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getnframes()/w.getframerate()
assert (sr,ch,width)==(24000,1,2),(sr,ch,width)
assert 20<length<60,length
after=float(req("/api/v1/chat/credit"))
spent=max(0,round(before-after,4))
audit={"status":"SUCCESS_ONE_USER_APPROVED_PAID_JOB","provider":"kie.ai","model":model,"voice":voice,
"create_task_count":1,"retry_count":0,"task_id":task,"credits_before":before,"credits_after":after,
"credits_spent":spent,"stage_credits_ceiling":4,"provider_hard_spend_cap_enforceable":False,
"source_text":text,"source_words":85,"source_scene3_words":37,"source_scene4_words":48,
"audio_seconds":round(length,3),"sample_rate":sr,"channels":ch,"sample_width_bytes":width,
"audio_sha256":hashlib.sha256(audio).hexdigest(),"audio_file":filename.name,
"paid_image_jobs_in_this_workflow":0,"prior_first30_preserved":True}
(out/"KIE_FINAL_30TO60_CREDIT_AND_TTS_AUDIT.json").write_text(json.dumps(audit,indent=2))
print("FINAL_KIE_CREDIT_AUDIT",json.dumps(audit),flush=True)
if spent>4:raise RuntimeError("Kie overspent approved stage cap. STOP; zero more calls")
print("SUCCESS: exactly ONE voice job complete, source text intact, no paid retries",flush=True)
