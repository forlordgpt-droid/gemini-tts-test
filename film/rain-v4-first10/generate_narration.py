#!/usr/bin/env python3
"""Prepare or resume ONE authorized rain-preview Kie Flash narration task.

Default: disabled until a current-conversation authorization JSON is supplied.
Never retries createTask. Receipt survives downloads/polling failures. A fresh
GitHub run/attempt cannot regenerate if its receipt was not restored. No keys or
signed download URLs are written to disk or printed. Standard library only.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import wave

MODEL = "google/gemini-3-8-flash-tts"
PROVIDER = "kie.ai"
API = "https://api.kie.ai"
SCOPE = "rain-v4-first10:one-narration-task"
MAX_CREDITS = 1.0
BASE = Path(__file__).resolve().parent
TEXT = ("On the first day of the rain, you think the water is the danger. "
        "You're wrong. Water is the one thing you will never run out of again.")
WAV_NAME = "RAIN_V4_FIRST10_KIE_GEMINI38_FLASH_RAW.wav"


def stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def canonical_hash(obj):
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def read_json(path):
    with Path(path).open(encoding="utf-8") as source:
        return json.load(source)


def atomic_json(path, obj):
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as dest:
        json.dump(obj, dest, indent=2, ensure_ascii=False, allow_nan=False)
        dest.write("\n")
        dest.flush()
        os.fsync(dest.fileno())
    os.replace(tmp, path)


def checked_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(label + " must be a finite number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise RuntimeError(label + " must be finite and nonnegative")
    return number


def validate_payload(payload):
    if payload.get("model") != MODEL:
        raise RuntimeError("Exact Flash model required; no substitution")
    inp = payload.get("input", {})
    if inp.get("speakers") != [{"speaker_id": "Speaker 1", "voice_name": "Fola"}]:
        raise RuntimeError("The prepared single Fola narrator must be preserved")
    turns = inp.get("dialogue_turns", [])
    if len(turns) != 1 or turns[0].get("speaker_id") != "Speaker 1":
        raise RuntimeError("Exactly one narration turn is required")
    if turns[0].get("text") != TEXT or len(TEXT.split()) != 28 or len(TEXT) >= 300:
        raise RuntimeError("The original 28-word opening must remain verbatim")
    if inp.get("temperature") != 1 or not turns[0].get("style"):
        raise RuntimeError("Prepared voice direction or temperature is missing")
    if inp.get("filler_words") is not False:
        raise RuntimeError("Added filler words must remain disabled")


def validate_authorization(path, request_hash):
    if not Path(path).is_file():
        raise RuntimeError("PAID GENERATION DISABLED: explicit rain-preview authorization is missing")
    auth = read_json(path)
    exact = {
        "approved": True,
        "approval_scope": SCOPE,
        "provider": PROVIDER,
        "model": MODEL,
        "jobs_authorized": 1,
        "provider_hard_cap": False,
        "authorization_source": "current_conversation",
        "request_sha256": request_hash,
    }
    for key, value in exact.items():
        if key not in auth or auth[key] != value or type(auth[key]) is not type(value):
            raise RuntimeError("PAID GENERATION DISABLED: authorization mismatch for " + key)
    if checked_number(auth.get("max_total_credits"), "max_total_credits") != MAX_CREDITS:
        raise RuntimeError("The local one-task estimated budget must remain one credit")
    evidence = auth.get("user_approval_evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        raise RuntimeError("Current user approval evidence is required; do not fabricate it")
    # Authorization is established from the actual conversation by the operator.
    # Do not invent an acknowledgement of a technical provider limitation. The
    # provider has no per-task hard cap; this is a local one-task estimate only.
    return auth


class Kie:
    def __init__(self):
        self.key = os.environ.get("KIE_API_KEY", "").strip()
        if len(self.key) < 16:
            raise RuntimeError("KIE_API_KEY secret unavailable; no task submitted")

    def request(self, path, body=None):
        headers = {"Authorization": "Bearer " + self.key, "Accept": "application/json"}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(API + path, data=data, headers=headers,
                                     method="POST" if body is not None else "GET")
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                obj = json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError("Kie HTTP " + str(error.code) + "; createTask is never retried") from None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            raise RuntimeError("Kie response unavailable; preserve receipt and do not resubmit") from None
        if obj.get("code") != 200:
            raise RuntimeError("Kie API code " + str(obj.get("code")) + "; no automatic paid retry")
        return obj.get("data")


def audio_details(path):
    with wave.open(str(path), "rb") as wav:
        spec = (wav.getframerate(), wav.getnchannels(), wav.getsampwidth(), wav.getcomptype())
        if spec != (24000, 1, 2, "NONE"):
            raise RuntimeError("Unexpected WAV format; preserve source and stop without substitution")
        seconds = wav.getnframes() / wav.getframerate()
        if seconds <= 0:
            raise RuntimeError("Empty narration audio")
    return {
        "duration_seconds": seconds,
        "sample_rate": 24000,
        "channels": 1,
        "bit_depth": 16,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "tempo_factor": 1.0,
        "source_audio_modified": False,
        "requires_actual_voice_timing": True,
        "speech_and_picture_alignment_verified": False,
    }


def download_source(url, path):
    # The provider result URL is used only in memory and never recorded/logged.
    if urllib.parse.urlparse(url).scheme != "https":
        raise RuntimeError("Provider returned a non-HTTPS audio URL")
    try:
        with urllib.request.urlopen(url, timeout=90) as response:
            data = response.read(16 * 1024 * 1024 + 1)
    except (urllib.error.URLError, OSError):
        raise RuntimeError("Audio download failed; resume this same task, never regenerate") from None
    if len(data) > 16 * 1024 * 1024 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise RuntimeError("Audio bytes are invalid or unexpectedly large; no regeneration")
    tmp = Path(str(path) + ".tmp")
    with tmp.open("wb") as dest:
        dest.write(data)
        dest.flush()
        os.fsync(dest.fileno())
    os.replace(tmp, path)


def run(args):
    payload = read_json(args.request)
    validate_payload(payload)
    request_hash = canonical_hash(payload)
    if args.validate_only:
        authorization_present = Path(args.authorization).is_file()
        if authorization_present:
            validate_authorization(args.authorization, request_hash)
        print(json.dumps({"prepared": True,
                          "authorization_validated": authorization_present,
                          "paid_generation": "NOT_EXECUTED_VALIDATION_ONLY",
                          "model": MODEL, "words": 28, "spoken_characters": len(TEXT),
                          "request_sha256": request_hash, "provider_hard_cap": False,
                          "local_estimated_budget_credits": MAX_CREDITS,
                          "requires_actual_voice_timing": True}))
        return 0
    auth = validate_authorization(args.authorization, request_hash)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    receipt_path = out / "TASK_RECEIPT.json"
    wav_path = out / WAV_NAME
    with (out / ".process.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another process owns this narration task; no duplicate submission") from None
        if receipt_path.exists():
            receipt = read_json(receipt_path)
            if receipt.get("request_sha256") != request_hash or receipt.get("model") != MODEL:
                raise RuntimeError("Receipt/request mismatch; do not replace or regenerate")
            if receipt.get("state") == "FAILED":
                raise RuntimeError("Recorded task failed; a second paid request is prohibited")
            if not receipt.get("task_id"):
                raise RuntimeError("Submission outcome uncertain: reconcile existing task; NEVER resubmit")
            if receipt.get("state") in ("SUCCEEDED", "SUCCEEDED_COST_UNVERIFIED", "BUDGET_EXCEEDED") and wav_path.is_file():
                details = audio_details(wav_path)
                if details["sha256"] != receipt.get("audio", {}).get("sha256"):
                    raise RuntimeError("Saved source WAV changed; do not regenerate")
                print("Existing narration verified. No API calls or new paid job.")
                return 2 if receipt["state"] == "BUDGET_EXCEEDED" else 0
        else:
            if (os.environ.get("GITHUB_ACTIONS") != "true"
                    or os.environ.get("GITHUB_RUN_NUMBER") != "1"
                    or os.environ.get("GITHUB_RUN_ATTEMPT") != "1"):
                raise RuntimeError("Fresh creation allowed only on first GitHub workflow run/attempt; restore receipt for resume")
            kie = Kie()
            balance = checked_number(kie.request("/api/v1/chat/credit"), "available credits")
            if balance < MAX_CREDITS:
                raise RuntimeError("Insufficient one-credit budget headroom; no paid task submitted")
            receipt = {
                "schema_version": 1, "project": "Ten Years of Rain V4 first10",
                "provider": PROVIDER, "model": MODEL, "voice": "Fola",
                "request_sha256": request_hash, "authorization_sha256": canonical_hash(auth),
                "creation_attempts": 1, "jobs_authorized": 1,
                "proposed_max_total_credits": MAX_CREDITS, "provider_hard_cap": False,
                "authorization_source": auth["authorization_source"],
                "budget_control": "LOCAL_ONE_TASK_ESTIMATE_AND_POST_TASK_ACCOUNTING",
                "credits_before": balance, "state": "SUBMISSION_INTENT_RECORDED",
                "created_at": stamp(), "github_run_id": os.environ.get("GITHUB_RUN_ID"),
                "requires_actual_voice_timing": True, "automatic_paid_retry_allowed": False,
            }
            # Persist intent BEFORE network submission. An ambiguous response cannot
            # result in another createTask, even if the process dies immediately.
            atomic_json(receipt_path, receipt)
            try:
                created = kie.request("/api/v1/jobs/createTask", payload)
                task_id = created.get("taskId") if isinstance(created, dict) else None
                if not task_id:
                    raise RuntimeError("Task ID unavailable; reconcile provider history without resubmission")
            except Exception:
                receipt["state"] = "CREATE_OUTCOME_UNKNOWN"
                receipt["updated_at"] = stamp()
                atomic_json(receipt_path, receipt)
                raise
            receipt.update(task_id=task_id, state="SUBMITTED", updated_at=stamp())
            atomic_json(receipt_path, receipt)  # persisted before the first poll
            print("One task recorded. All remaining requests query or download this task.", flush=True)

        kie = Kie()
        deadline = time.monotonic() + args.poll_timeout
        result = None
        while time.monotonic() < deadline:
            result = kie.request("/api/v1/jobs/recordInfo?" + urllib.parse.urlencode({"taskId": receipt["task_id"]}))
            if not isinstance(result, dict):
                raise RuntimeError("Malformed task response; preserve receipt and resume same task")
            if result.get("model") and result["model"] != MODEL:
                raise RuntimeError("Provider reported an unexpected model; stop")
            state = result.get("state")
            receipt.update(provider_state=state, updated_at=stamp())
            if result.get("creditsConsumed") is not None:
                receipt["credits_consumed"] = checked_number(result["creditsConsumed"], "creditsConsumed")
                receipt["cost_verified_from_task"] = True
            if state == "fail":
                receipt["state"] = "FAILED"
                atomic_json(receipt_path, receipt)
                raise RuntimeError("Provider task failed; receipt saved and no automatic paid retry")
            if state == "success":
                receipt["state"] = "SUCCEEDED_PENDING_DOWNLOAD"
                atomic_json(receipt_path, receipt)
                break
            if state not in ("waiting", "queuing", "generating"):
                raise RuntimeError("Unexpected task state; preserve receipt and do not regenerate")
            receipt["state"] = "PENDING"
            atomic_json(receipt_path, receipt)
            time.sleep(min(4, max(0, deadline - time.monotonic())))
        else:
            print("Task is still pending. Restore TASK_RECEIPT.json and rerun to poll this SAME task.")
            return 3

        parsed = result.get("resultJson") or result.get("response") or {}
        if isinstance(parsed, str):
            parsed = json.loads(parsed)
        urls = parsed.get("resultUrls", []) if isinstance(parsed, dict) else []
        if not urls:
            raise RuntimeError("Successful task has no audio URL; resume existing task without regeneration")
        download_source(urls[0], wav_path)
        receipt["audio"] = audio_details(wav_path)
        spent = receipt.get("credits_consumed")
        receipt["cost_verified_from_task"] = spent is not None
        receipt["state"] = "SUCCEEDED" if spent is not None else "SUCCEEDED_COST_UNVERIFIED"
        if spent is not None and spent > MAX_CREDITS:
            receipt["state"] = "BUDGET_EXCEEDED"
        receipt["updated_at"] = stamp()
        atomic_json(receipt_path, receipt)
        atomic_json(out / "NARRATION_AUDIT.json", {
            "provider": PROVIDER, "model": MODEL, "voice": "Fola", "task_id": receipt["task_id"],
            "request_sha256": request_hash, "words": 28, "exact_text": TEXT,
            "paid_creation_attempts": 1, "automatic_paid_retry_allowed": False,
            "credits_consumed": spent, "cost_verified_from_task": spent is not None,
            "proposed_max_total_credits": MAX_CREDITS, "provider_hard_cap": False,
            "source_filename": WAV_NAME, "audio": receipt["audio"],
            "next_step": "Measure actual phrase boundaries and synchronize picture; do not alter tempo or clip words.",
        })
        print(json.dumps({"state": receipt["state"], "source_wav": WAV_NAME,
                          "duration_seconds": receipt["audio"]["duration_seconds"],
                          "credits_consumed": spent, "requires_actual_voice_timing": True}))
        return 2 if receipt["state"] == "BUDGET_EXCEEDED" else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=BASE / "tts_request.json")
    parser.add_argument("--authorization", type=Path, default=BASE / "tts_authorization.json")
    parser.add_argument("--output-dir", type=Path, default=BASE / "tts_output")
    parser.add_argument("--poll-timeout", type=float, default=600)
    parser.add_argument("--validate-only", action="store_true", help="Validate preparation with ZERO network calls")
    args = parser.parse_args()
    if not math.isfinite(args.poll_timeout) or not 1 <= args.poll_timeout <= 1800:
        parser.error("--poll-timeout must be between 1 and 1800 seconds")
    try:
        return run(args)
    except Exception as error:
        # Print only controlled messages; never a traceback, credential, body or URL.
        message = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("STOP: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
