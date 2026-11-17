#!/usr/bin/env python3
"""ONE new explicitly approved second Kie.ai Gemini 3.8 Flash task after first failed with 0 charge.
No automatic retries, no model substitution, no additional dialogue, audit actual credit delta.
"""
from __future__ import annotations
import json, os, sys, time, wave, urllib.parse, urllib.request, urllib.error, hashlib
from pathlib import Path

MODEL="google/gemini-3-8-flash-tts"
API="https://api.kie.ai"
BASE=Path("film/story5-v3/narrated-first10")
MANIFEST=BASE/"NARRATION_LOCKED_FIRST10_MANIFEST.json"
OUT=Path("story5_second_authorized_narrator")
OUT.mkdir(parents=True,exist_ok=True)
m=json.loads(MANIFEST.read_text())
retry_approval=json.loads((BASE/"SECOND_PAID_ATTEMPT_USER_AUTHORIZATION.json").read_text())
assert retry_approval["previous_failed_task_id"]=="50214fd411ae5bd5c280faf60a3f809d"
assert retry_approval["previous_credit_debit"]==0
assert retry_approval["provider"]=="kie.ai" and retry_approval["model"]==MODEL
assert retry_approval["new_jobs_approved"]==1 and retry_approval["new_max_credit_spend"]==5
assert retry_approval["automatic_paid_retries"] is False
assert retry_approval["hard_charge_cap_enforceable_by_provider"] is False
assert retry_approval["user_acknowledged_no_hard_cap"] is True
assert retry_approval["images_generated_new"]==0
assert retry_approval["first_10s_source"]=="The entire city had been evacuated. A deadly yellow gas was spreading through the streets, killing anyone who breathed it. But Emma was still trapped."
expected="The entire city had been evacuated. A deadly yellow gas was spreading through the streets, killing anyone who breathed it. But Emma was still trapped."
assert m["narration_first10_exact"]==expected and m["words"]==25
assert m["narration_mode"]=="SINGLE_NARRATOR_VERBATIM"
assert m["tts"]["model"]==MODEL and m["tts"]["provider"]=="kie.ai"
assert m["tts"]["approved_generation_jobs"]==0 and m["tts"]["authorized_credits"]==0
assert m["tts"]["completed_approved_paid_attempts"]==1
assert m["tts"]["last_task_id"]==retry_approval["previous_failed_task_id"]
assert m["tts"]["last_task_state"]=="fail" and m["tts"]["observed_credit_debit"]==0
assert m["tts"]["new_approval_required_for_any_paid_retry"] is True
assert m["tts"]["proposed_max_credits"]==5 and m["tts"]["automatic_retries_allowed"] is False
assert m["tts"]["user_acknowledged_no_hard_cap"] is True
assert m["tts"]["hard_cap_enforceable_by_provider"] is False
assert m["tts"]["approval_scope"]=="ONE SINGLE NARRATOR JOB for first10 of story5 only"
assert m["tts"]["paid_generation_disabled"] is True  # Old spending approval remains consumed; ONLY new approval authorizes second job
assert m["narrator_voice"]=="Charon"
assert os.environ.get("GITHUB_RUN_NUMBER")=="1", "DISABLED: cannot repeat paid job (run_number != 1)"
assert os.environ.get("GITHUB_RUN_ATTEMPT")=="1", "DISABLED: cannot rerun paid job"
key=os.environ.get("KIE_API_KEY","").strip()
if len(key)<16:raise RuntimeError("Missing GitHub KIE_API_KEY secret: no job submitted")
def api(path,body=None):
    data=json.dumps(body,separators=(",",":")).encode() if body is not None else None
    headers={"Authorization":"Bearer "+key,"Accept":"application/json"}
    if data is not None:headers["Content-Type"]="application/json"
    req=urllib.request.Request(API+path,data=data,headers=headers,method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req,timeout=45) as resp: obj=json.load(resp)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Kie HTTP {exc.code}: {exc.read(350).decode(errors='replace')}") from None
    if obj.get("code")!=200:raise RuntimeError(f"Kie API returned {obj.get('code')}: {obj.get('msg')}")
    return obj["data"]
before=float(api("/api/v1/chat/credit"))
if before<retry_approval["new_max_credit_spend"]:raise RuntimeError("Kie balance is under the user's 5-credit headroom; stop without generation")
# conservative estimated possible 60 sec audio, 500 input tokens at published rate
max_conservative_estimate=(500*70+60*25*1260)/1000000
assert max_conservative_estimate<retry_approval["new_max_credit_spend"],max_conservative_estimate
payload={
 "model":MODEL,
 "input":{
   "temperature":1,
   "speakers":[{"speaker_id":"Speaker 1","voice_name":"Charon"}],
   "dialogue_turns":[{"speaker_id":"Speaker 1","style":
    "Single off-screen male narrator telling a suspenseful cinematic thriller. Brisk, crisp, emotionally controlled, immersive, urgent but intelligible, approximately 170 to 185 words per minute. Read the text VERBATIM, exactly once, with very short natural sentence pauses, absolutely no introductory phrase, no dialogue performance, no extra words and no trailing speech.",
    "text":expected}]
 }
}
(OUT/"EXACT_NARRATION_TEXT.txt").write_text(expected+"\n")
(OUT/"REQUEST_WITHOUT_SECRET.json").write_text(json.dumps(payload,indent=2))
print("PRE_FLIGHT",json.dumps({"provider":"kie.ai","model":MODEL,"words":25,"jobs":1,"credits_before":before,"user_proposed_max":retry_approval["new_max_credit_spend"],"second_explicit_approval":True,"previous_failed_task":retry_approval["previous_failed_task_id"],"estimated_60s_credits":max_conservative_estimate,"hard_cap_enforceable":False,"retry_allowed":False}),flush=True)
# Exactly ONE paid network submission, no retry irrespective of error or crash.
job=api("/api/v1/jobs/createTask",payload)
task_id=job.get("taskId")
if not task_id:raise RuntimeError("No taskId returned; DO NOT resubmit")
state={"task_id":task_id,"provider":"kie.ai","model":MODEL,"requested_jobs":1,"paid_retries_allowed":False,"credits_before":before,"status":"CREATED"}
(OUT/"TASK_PROGRESS.json").write_text(json.dumps(state,indent=2))
print("ONE_PAID_JOB_ID",task_id,flush=True)
for i in range(120):
    res=api("/api/v1/jobs/recordInfo?"+urllib.parse.urlencode({"taskId":task_id}))
    status=res.get("state")
    if i%6==0:print("KIE_STATE",status,"poll",i,flush=True)
    if status=="success":break
    if status=="fail":raise RuntimeError("Paid request failed: "+str(res.get("failMsg") or res.get("failCode"))+"; DO NOT retry")
    if status not in ("waiting","queuing","generating"):raise RuntimeError("Unexpected job state "+str(status)+"; do not retry")
    time.sleep(4)
else:raise RuntimeError("Paid task still active; ONLY resume polling SAME task_id; do not generate again")
result=res.get("resultJson") or res.get("response") or {}
if isinstance(result,str):result=json.loads(result)
urls=result.get("resultUrls") or []
if not urls:raise RuntimeError("Successful paid task returned no resultUrl; no regeneration allowed")
with urllib.request.urlopen(urls[0],timeout=120) as resp:
    wav_bytes=resp.read()
if wav_bytes[:4]!=b"RIFF" or wav_bytes[8:12]!=b"WAVE":
    raise RuntimeError("Wrong output format (not WAV); no model substitution")
audio=OUT/"EMMA_STORY5_FIRST10_KIE_GEMINI38_FLASH_NARRATOR.wav"
audio.write_bytes(wav_bytes)
with wave.open(str(audio),"rb") as w:
    sample_rate,channels,bit_depth=w.getframerate(),w.getnchannels(),w.getsampwidth()*8
    seconds=w.getnframes()/sample_rate
if (sample_rate,channels,bit_depth)!=(24000,1,16):raise RuntimeError(f"Unexpected WAV PCM spec {(sample_rate,channels,bit_depth)}")
if not 3<seconds<40:raise RuntimeError(f"Narration duration out-of-range {seconds}s; do not regenerate automatically")
after=float(api("/api/v1/chat/credit"))
spent=max(0,round(before-after,4))
audit={
    "status":"SUCCESS_ONE_PAID_JOB","project":"Emma story5 narrator for revised first ten seconds",
    "provider":"kie.ai","model":MODEL,"voice":"Charon","jobs_created":1,"retry_count":0,
    "task_id":task_id,"credits_before":before,"credits_after":after,"credits_spent_from_balance":spent,
    "user_proposed_ceiling":retry_approval["new_max_credit_spend"],"new_explicit_approval_job":True,"previous_failed_no_debit_task":retry_approval["previous_failed_task_id"],"provider_hard_ceiling":False,"user_acknowledged_no_hard_ceiling":True,
    "recorded_seconds":round(seconds,4),"sample_rate":sample_rate,"channels":channels,"bit_depth":bit_depth,
    "exact_narration_text":expected,"audio_sha256":hashlib.sha256(wav_bytes).hexdigest(),
    "audio_filename":audio.name,"published_rates_credits_per_million_tokens":{"text":70,"audio_output":1260}
}
(OUT/"KIE_ONE_NARRATOR_COST_AND_AUDIO_AUDIT.json").write_text(json.dumps(audit,indent=2))
print("KIE_ONE_NARRATOR_AUDIT",json.dumps(audit),flush=True)
if spent>retry_approval["new_max_credit_spend"]:raise RuntimeError("Kie exceeded approved estimated 5-credit maximum; STOP, no more requests")
print("PASS: first ten second story5 narration GENERATED once, no dialog, without other paid assets",flush=True)
