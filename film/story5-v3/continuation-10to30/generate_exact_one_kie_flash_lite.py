#!/usr/bin/env python3
"""One explicit owner-authorized Kie Gemini 3.8 Flash-Lite narrator job for story5 10-30.
No retries, no other voices, exact original words, credit debit and task audit.
"""
from pathlib import Path
import hashlib,json,os,time,urllib.request,urllib.parse,urllib.error,wave,sys
ROOT=Path("film/story5-v3/continuation-10to30")
M=json.loads((ROOT/"APPROVED_10TO30_MANIFEST.json").read_text())
N=M["narration"];AUTH=M["user_authorization"];OUT=Path("story5_10to30_kie_voice");OUT.mkdir(exist_ok=True)
MODEL="google/gemini-3-8-flash-lite-tts"
TEXT="She ran past abandoned cars, desperately searching for somewhere safe. Then her phone rang. A mysterious caller warned her to hide underground. Emma rushed into an empty subway station, but the main gate was locked. Suddenly, she heard heavy footsteps approaching from the darkness. With no time to think, she escaped through a maintenance tunnel."
assert TEXT==N["text"] and len(TEXT.split())==55
assert N["provider"]=="kie.ai" and N["model"]==MODEL and N["voice"]=="Charon"
assert N["mode"]=="SINGLE_NARRATOR_VERBATIM" and N["approved_new_jobs"]==1 and N["max_credits"]==5
assert (AUTH["tts_jobs_max"],AUTH["tts_credits_max"],AUTH["image_jobs_max"],AUTH["image_credits_max"],AUTH["stage_total_credits_max"])==(1,5,4,4,9)
assert AUTH["no_automatic_paid_retries"] is True and AUTH["provider_hard_enforceable_credit_cap"] is False
assert M["images"]["new_jobs_completed"]==1 and M["images"]["new_paid_credits"]==1
assert M["approved_first10"]["mutate"] is False
assert os.environ.get("GITHUB_RUN_NUMBER")=="1" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1", "One paid job only; reruns forbidden"
KEY=os.environ.get("KIE_API_KEY","").strip()
if len(KEY)<16:raise RuntimeError("Missing KIE_API_KEY secret; fail closed")
API="https://api.kie.ai"
def request(path,body=None):
    data=json.dumps(body).encode() if body is not None else None
    headers={"Authorization":"Bearer "+KEY,"Accept":"application/json"}
    if data is not None:headers["Content-Type"]="application/json"
    req=urllib.request.Request(API+path,data=data,headers=headers,method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req,timeout=45) as resp:d=json.load(resp)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Kie HTTP {e.code}, {e.read(350).decode(errors='replace')}") from None
    if d.get("code")!=200:raise RuntimeError(f"Kie returned {d.get('code')}: {d.get('msg')}")
    return d["data"]
before=float(request("/api/v1/chat/credit"))
if before<5:raise RuntimeError("Insufficient Kie 5-credit headroom. Do not generate")
estimate=(800*70+40*25*840)/1e6
if estimate>AUTH["tts_credits_max"]:raise RuntimeError("Estimated speech exceeds user budget")
turn={"speaker_id":"Speaker 1","style":"THE SAME Charon offscreen male narrator as the approved story5 0 to 10 seconds. Stylish, cinematic thriller, brisk natural narrative pace about 185 to 205 words per minute, concise breath pauses, controlled fear, clearly articulated. Read all 55 words exactly once and only once, no introductions, no invented dialogue or reaction sounds; do not impersonate the caller.","text":TEXT}
payload={"model":MODEL,"input":{"temperature":1,"speakers":[{"speaker_id":"Speaker 1","voice_name":"Charon"}],"dialogue_turns":[turn]}}
(OUT/"EXACT_AUTHORITATIVE_NARRATION.txt").write_text(TEXT+"\n")
(OUT/"REQUEST_WITHOUT_SECRET.json").write_text(json.dumps(payload,indent=2))
print("PREFLIGHT",json.dumps({"model":MODEL,"words":55,"one_job":True,"balance_before":before,"max_approved_credits":5,"estimated_upper":estimate}),flush=True)
# Exactly ONE submission. No automatic retries for failures or ambiguity.
created=request("/api/v1/jobs/createTask",payload)
task=created.get("taskId")
if not task:raise RuntimeError("No task ID; DO NOT RESUBMIT")
(OUT/"TASK_PROGRESS.json").write_text(json.dumps({"task_id":task,"one_paid_createTask":True,"no_retry":True,"status":"CREATED"},indent=2))
print("ONE_AND_ONLY_PAID_TASK_ID",task,flush=True)
for i in range(120):
    r=request("/api/v1/jobs/recordInfo?"+urllib.parse.urlencode({"taskId":task}))
    state=r.get("state")
    if i%6==0:print("TASK_STATUS",state,"poll",i,flush=True)
    if state=="success":break
    if state=="fail":raise RuntimeError("Kie failed task; DO NOT RESUBMIT: "+str(r.get("failMsg") or r.get("failCode")))
    if state not in ("waiting","queuing","generating"):raise RuntimeError("Unexpected state "+str(state)+"; DO NOT RESUBMIT")
    time.sleep(4)
else:raise RuntimeError("Task still pending; resume polling SAME task ID; no new generation")
result=r.get("resultJson") or r.get("response") or {}
if isinstance(result,str):result=json.loads(result)
urls=result.get("resultUrls") or []
if not urls:raise RuntimeError("Kie success returned no WAV URL; DO NOT RESUBMIT")
with urllib.request.urlopen(urls[0],timeout=110) as resp:raw=resp.read()
if raw[:4]!=b"RIFF" or raw[8:12]!=b"WAVE":raise RuntimeError("Kie audio format mismatch; no substitutes")
voice=OUT/"STORY5_10TO30_KIE38_FLASH_LITE_CHARON.wav"
voice.write_bytes(raw)
with wave.open(str(voice)) as w:rate,chan,width,seconds=w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getnframes()/w.getframerate()
if (rate,chan,width)!=(24000,1,2):raise RuntimeError("Unexpected WAV format")
after=float(request("/api/v1/chat/credit"))
spent=max(0,round(before-after,4))
audit={"status":"SUCCESS_ONE_PAID_JOB","provider":"kie.ai","model":MODEL,"voice":"Charon","task_id":task,"created_jobs":1,"retry_count":0,"balance_before":before,"balance_after":after,"credits_spent":spent,"approved_max_credits":5,"hard_cap_enforceable_by_provider":False,"source_text":TEXT,"source_words":55,"audio_seconds":round(seconds,3),"sample_rate":rate,"channels":chan,"bit_depth":width*8,"sha256":hashlib.sha256(raw).hexdigest(),"filename":voice.name}
(OUT/"KIE_EXACT_SPEND_AND_VOICE_AUDIT.json").write_text(json.dumps(audit,indent=2))
print("KIE_10TO30_AUDIT",json.dumps(audit),flush=True)
if spent>5:raise RuntimeError("Credit cap exceeded; STOP no new job")
print("SUCCESS ONE exact user approved Flash-Lite narrator task",flush=True)
