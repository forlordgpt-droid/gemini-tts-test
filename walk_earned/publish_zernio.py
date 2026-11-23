#!/usr/bin/env python3
"""Publish The Walk He Earned to authorized TikTok + Facebook via Zernio.

Requires ZERNIO_API_KEY stored as a GitHub Actions secret. Never commit or print it.
Fails closed if the exact intended account names are not uniquely found.
Reads existing completed film; does not generate video or charge Snapgen credits.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://zernio.com/api/v1"
KEY = os.environ.get("ZERNIO_API_KEY", "").strip()
ROOT = Path("received/final")
TIKTOK_MEDIA = ROOT / "The_Walk_He_Earned_45s_480p_9x16.mp4"
FACEBOOK_MEDIA = Path("facebook_ready.mp4")
OUT = Path("publication_result.json")
MARKER = "The Walk He Earned — fictional AI-generated short film."

TIKTOK_CAPTION = (
    "“I’m her father. I’ll walk her.” 💍\n"
    "But the bride was waiting for someone else… 🥹\n"
    "Who really earns the honor of walking a daughter down the aisle?\n\n"
    + MARKER + "\n"
    "#WeddingDrama #Stepdad #FatherDaughter #BlendedFamily #FamilyDrama"
)
FACEBOOK_CAPTION = (
    "He stepped forward to walk his daughter down the aisle. "
    "But she had already chosen the father who showed up for her. 💙💍\n\n"
    "What makes someone a dad—biology or being there when it matters?\n\n"
    + MARKER + "\n"
    "#FamilyDrama #WeddingStory #FatherDaughter #Stepdad"
)

def api(method, path, body=None):
    headers = {
        "Authorization": "Bearer " + KEY,
        "Accept": "application/json",
        "User-Agent": "ChatGPT-WeddingShortPublisher/1.0",
    }
    payload = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(BASE + path, headers=headers, data=payload, method=method)
    try:
        with urllib.request.urlopen(request, timeout=65) as res:
            raw = res.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print("ZERNIO_API_ERROR", method, path.split("?")[0], "HTTP", e.code, flush=True)
        raise RuntimeError(f"Zernio request error: HTTP {e.code}") from None
    except Exception as e:
        print("ZERNIO_CONNECTION_ERROR", method, type(e).__name__, flush=True)
        raise RuntimeError("Could not reach Zernio") from None

def unwrap(obj):
    """Find list objects below common response wrappers."""
    if isinstance(obj, list):
        if any(isinstance(x, dict) for x in obj):
            return obj
        return []
    if isinstance(obj, dict):
        for name in ("accounts", "posts", "items", "results", "data", "result"):
            if name in obj:
                found = unwrap(obj[name])
                if found:
                    return found
    return []

def normalize_platform(a):
    p = a.get("platform") or a.get("platformType") or a.get("type") or ""
    if isinstance(p, dict):
        p = p.get("name") or p.get("id") or ""
    return str(p).lower().replace("_", "-")

def account_labels(a):
    labels = []
    for node in (a, a.get("account"), a.get("page"), a.get("profile")):
        if isinstance(node, dict):
            for key in ("name", "username", "handle", "displayName", "pageName", "socialUsername",
                        "accountName", "platformUsername", "display_name", "title"):
                value = node.get(key)
                if isinstance(value, str) and value.strip():
                    labels.append(value.strip().casefold().lstrip("@"))
    return labels

def select_account(items, platform, expected):
    matching_platform = [a for a in items if normalize_platform(a) == platform]
    expected = expected.casefold().lstrip("@")
    matching = [a for a in matching_platform
                if any(expected == label or expected in label for label in account_labels(a))]
    if len(matching) != 1:
        print("ACCOUNT_SELECTION_BLOCKED", platform, "platform_count", len(matching_platform),
              "name_matches", len(matching), flush=True)
        raise RuntimeError("Exact requested social account not uniquely found; publishing halted")
    a = matching[0]
    if a.get("isConnected") is False or str(a.get("status", "")).lower() in ("disconnected", "expired"):
        raise RuntimeError("Target account is disconnected or expired")
    aid = str(a.get("id") or a.get("_id") or a.get("accountId") or "").strip()
    if not aid:
        raise RuntimeError("Connected account lacks an account ID")
    print("ACCOUNT_VERIFIED", platform, expected, flush=True)
    return aid

def get_post_record(data):
    if not isinstance(data, dict):
        return {}
    if isinstance(data.get("post"), dict):
        return data["post"]
    for key in ("data", "result"):
        val = data.get(key)
        if isinstance(val, dict):
            return get_post_record(val)
    return data

def existing_post(posts, platform, aid):
    for x in posts:
        if not isinstance(x, dict):
            continue
        content = x.get("content") or x.get("text") or ""
        if isinstance(content, dict):
            content = content.get("text", "")
        if MARKER not in str(content):
            continue
        p = x.get("platforms", [])
        if not isinstance(p, list):
            continue
        for target in p:
            if not isinstance(target, dict):
                continue
            if str(target.get("accountId") or "") == aid or (
                str(target.get("platform") or "").lower() == platform
                and str(target.get("accountId", "")) == aid
            ):
                return x
    return None

def https_field(value, field_names):
    """Find an HTTPS URL with one of the requested field names; do not log signed URLs."""
    if isinstance(value, dict):
        for key in field_names:
            field = value.get(key)
            if isinstance(field, str) and field.startswith("https://"):
                return field
        for child in value.values():
            if isinstance(child, (dict, list)):
                got = https_field(child, field_names)
                if got:
                    return got
    if isinstance(value, list):
        for child in value:
            got = https_field(child, field_names)
            if got:
                return got
    return None


def direct_upload(file: Path, platform: str):
    """Authenticated multipart direct media upload for files below Zernio's 25 MB limit."""
    if file.stat().st_size > 24_800_000:
        raise RuntimeError("Direct media upload exceeds 25MB; presign required")
    import uuid
    boundary = "ChatGPTZernio" + uuid.uuid4().hex
    filename = f"the-walk-he-earned-{platform}.mp4"
    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: video/mp4\r\n\r\n"
    ).encode("ascii")
    closing = f"\r\n--{boundary}--\r\n".encode("ascii")
    payload = header + file.read_bytes() + closing
    req = urllib.request.Request(
        BASE + "/media/upload-direct",
        data=payload,
        method="POST",
        headers={
            "Authorization": "Bearer " + KEY,
            "Accept": "application/json",
            "Content-Type": "multipart/form-data; boundary=" + boundary,
            "User-Agent": "ChatGPT-WeddingShortPublisher/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            media = json.load(response)
    except urllib.error.HTTPError as err:
        print("DIRECT_MEDIA_HTTP_ERROR", platform, err.code, flush=True)
        raise RuntimeError("Zernio direct video upload failed") from None
    url = https_field(media, ("url", "fileUrl", "file_url", "publicUrl", "mediaUrl"))
    if not url:
        if isinstance(media, dict):
            print("DIRECT_MEDIA_RESPONSE_KEYS", sorted(media.keys()), flush=True)
        raise RuntimeError("Zernio returned no usable direct-upload video URL")
    print("DIRECT_MEDIA_UPLOADED", platform, file.stat().st_size, flush=True)
    return url


def upload_video(file: Path, platform: str):
    if not file.is_file() or file.stat().st_size < 1_000_000:
        raise RuntimeError("Verified film was not downloaded")
    presigned = api("POST", "/media/presign", {
        "filename": f"the-walk-he-earned-{platform}.mp4",
        "contentType": "video/mp4",
    })
    upload_url = https_field(presigned, ("uploadUrl", "upload_url", "signedUrl", "presignedUrl", "presigned_url"))
    public_url = https_field(presigned, ("fileUrl", "file_url", "publicUrl", "public_url", "mediaUrl"))
    if upload_url and public_url:
        video = file.read_bytes()
        request = urllib.request.Request(
            upload_url, data=video, method="PUT",
            headers={"Content-Type": "video/mp4", "Content-Length": str(len(video))}
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as resp:
                if resp.status not in (200, 201, 204):
                    raise RuntimeError("Media upload unsuccessful")
        except urllib.error.HTTPError as e:
            print("PRESIGNED_MEDIA_HTTP_ERROR", platform, e.code, flush=True)
            raise RuntimeError("Could not upload video to presigned storage") from None
        print("MEDIA_UPLOADED", platform, len(video), flush=True)
        return public_url
    if isinstance(presigned, dict):
        print("PRESIGN_RESPONSE_KEYS", sorted(presigned.keys()), flush=True)
    print("PRESIGN_UNUSABLE_USING_DIRECT_UPLOAD", platform, flush=True)
    return direct_upload(file, platform)


def is_compatible_privacy(creator_info):
    txt = json.dumps(creator_info).upper()
    # A public post is requested. Stop if creator info explicitly lists other privacy only.
    for field in ("privacyLevelOptions", "privacy_level_options", "privacyLevels", "privacy_levels"):
        if isinstance(creator_info, dict):
            opts = creator_info.get(field)
            if isinstance(opts, list) and opts:
                return "PUBLIC_TO_EVERYONE" in str(opts).upper()
    return True

def publish(platform, aid, caption, media_path, current_posts):
    prior = existing_post(current_posts, platform, aid)
    if prior is not None:
        old = get_post_record(prior)
        print("EXISTING_POST_DETECTED", platform, "status", str(old.get("status", "unknown"))[:45], flush=True)
        return {"platform": platform, "action": "existing", "post_id": old.get("id") or old.get("_id"),
                "status": old.get("status"), "public_url": old.get("platformPostUrl") or old.get("url")}
    video_url = upload_video(media_path, platform)
    target = {"platform": platform, "accountId": aid}
    if platform == "tiktok":
        # TikTok requires creator-info before posting.
        info = api("GET", "/accounts/" + aid + "/tiktok/creator-info")
        creator_info = info.get("data", info) if isinstance(info, dict) else {}
        if not is_compatible_privacy(creator_info):
            raise RuntimeError("TikTok account does not permit public publishing")
        target["platformSpecificData"] = {
            "privacyLevel": "PUBLIC_TO_EVERYONE",
            "allowComment": True,
            "allowDuet": False,
            "allowStitch": False,
            "contentPreviewConfirmed": True,
            "expressConsentGiven": True,
            "draft": False,
            "commercialContentType": "none",
            "videoMadeWithAi": True,
            "videoCoverTimestampMs": 1000,
            "autoAddMusic": False
        }
    # Facebook treats standard single video posts as Reels. Only "story" needs explicit contentType.
    payload = {
        "content": caption,
        "platforms": [target],
        "mediaItems": [{"type": "video", "url": video_url}],
        "publishNow": True
    }
    response = get_post_record(api("POST", "/posts", payload))
    post_id = str(response.get("id") or response.get("_id") or response.get("postId") or "")
    if not post_id:
        # Never retry without checking the account first, because Zernio may have accepted it.
        raise RuntimeError("Zernio creation returned no post ID; manual status check required")
    print("PUBLISH_REQUEST_ACCEPTED", platform, flush=True)
    result = {"platform": platform, "action": "created", "post_id": post_id}
    for _ in range(24):
        time.sleep(10)
        try:
            record = get_post_record(api("GET", "/posts/" + post_id))
        except Exception:
            print("STATUS_POLL_ERROR", platform, flush=True)
            break
        status = str(record.get("status") or record.get("publishStatus") or "").lower()
        result["status"] = status
        result["public_url"] = (record.get("platformPostUrl") or record.get("postUrl")
                                or record.get("url") or record.get("permalink") or None)
        for t in record.get("platforms", []) if isinstance(record.get("platforms"), list) else []:
            if isinstance(t, dict) and str(t.get("platform", "")).lower() == platform:
                result["status"] = str(t.get("status") or status).lower()
                result["public_url"] = (t.get("url") or t.get("postUrl")
                                        or t.get("platformPostUrl") or result["public_url"])
        if result["status"] in ("published", "success", "posted", "failed", "error"):
            break
    print("POST_STATUS", platform, result.get("status", "not-confirmed"), flush=True)
    return result

def main():
    if not KEY:
        print("BLOCKED: GitHub repository secret ZERNIO_API_KEY is missing.", flush=True)
        return 2
    if not TIKTOK_MEDIA.is_file() or not FACEBOOK_MEDIA.is_file():
        print("BLOCKED: Video files missing.")
        return 3
    accounts = unwrap(api("GET", "/accounts"))
    tiktok_id = select_account(accounts, "tiktok", "forlordak")
    facebook_id = select_account(accounts, "facebook", "Naija AI Cinema")
    posts = unwrap(api("GET", "/posts?limit=80"))
    results = []
    for platform, aid, caption, path in [
        ("tiktok", tiktok_id, TIKTOK_CAPTION, TIKTOK_MEDIA),
        ("facebook", facebook_id, FACEBOOK_CAPTION, FACEBOOK_MEDIA),
    ]:
        try:
            result = publish(platform, aid, caption, path, posts)
            results.append(result)
            OUT.write_text(json.dumps({"film":"The Walk He Earned", "results":results}, indent=2)+"\n")
        except Exception as e:
            print("PUBLISHING_BLOCKED", platform, type(e).__name__, str(e)[:180], flush=True)
            OUT.write_text(json.dumps({"film":"The Walk He Earned", "results":results,
                                       "blocked_platform":platform, "error_type":type(e).__name__}, indent=2)+"\n")
            return 5
    return 0

if __name__ == "__main__":
    sys.exit(main())
