#!/usr/bin/env python3
"""Generate a WAV via Kie.ai Gemini 3.8 Flash-Lite TTS (standard library only)."""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.kie.ai/api/v1/jobs"
MODEL = "google/gemini-3-8-flash-lite-tts"

def request(path, key, body=None):
    headers = {"Authorization": "Bearer " + key, "Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=headers,
                                 method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError("Kie.ai HTTP %s: %s" % (exc.code, exc.read(1000).decode(errors="replace"))) from None
    if payload.get("code") != 200:
        raise RuntimeError("Kie.ai error %s: %s" % (payload.get("code"), payload.get("msg")))
    return payload["data"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="Yes this is working")
    parser.add_argument("--voice", default="Fola")
    parser.add_argument("--task-id", help="Resume a previous task instead of creating a new one")
    parser.add_argument("--output", default="yes_this_is_working.wav")
    args = parser.parse_args()
    key = os.environ.get("KIE_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Missing repository Actions secret KIE_API_KEY")
    if args.task_id:
        task_id = args.task_id
    else:
        payload = {
            "model": MODEL,
            "input": {
                "temperature": 1,
                "speakers": [{"speaker_id": "Speaker 1", "voice_name": args.voice}],
                "dialogue_turns": [{
                    "speaker_id": "Speaker 1",
                    "style": "Speak clearly and naturally, at a conversational pace.",
                    "text": args.text
                }]
            }
        }
        task_id = request("/createTask", key, payload).get("taskId")
        if not task_id:
            raise RuntimeError("No task ID was returned")
    print("Kie.ai task ID:", task_id, flush=True)
    for attempt in range(75):
        result = request("/recordInfo?"+urllib.parse.urlencode({"taskId":task_id}), key)
        state = result.get("state")
        print("Task state:", state, flush=True)
        if state == "success":
            parsed = result.get("response") or result.get("resultJson") or {}
            if isinstance(parsed, str):
                parsed = json.loads(parsed)
            urls = parsed.get("resultUrls") or []
            if not urls:
                raise RuntimeError("Successful task returned no audio URL")
            with urllib.request.urlopen(urls[0], timeout=80) as response:
                audio = response.read()
            if not (audio.startswith(b"RIFF") and audio[8:12] == b"WAVE"):
                raise RuntimeError("Downloaded audio is not a WAV file")
            with open(args.output, "wb") as f:
                f.write(audio)
            print("Saved WAV:", args.output, "bytes:", len(audio))
            return
        if state == "fail":
            raise RuntimeError("Generation failed: " + str(result.get("failMsg") or result.get("failCode")))
        if state not in ("waiting", "queuing", "generating"):
            raise RuntimeError("Unexpected task state: "+str(state))
        time.sleep(5)
    raise RuntimeError("Task still processing; resume with --task-id "+task_id)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR:", exc, file=sys.stderr)
        sys.exit(1)
