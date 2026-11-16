#!/usr/bin/env python3
"""Download existing Snapgen generation assets using their verified history UUIDs.

No new images or videos are generated. API key is read only from SNAPGEN_API_KEY.
Use inside GitHub Actions; never print media URLs or secrets.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request

API_BASE = "https://api.snapgen.ai/uapi/v1"
MANIFEST = Path(__file__).with_name("snapgen-asset-manifest.json")
OUTPUT = Path("hotel-room-next-door-assets")
KEY = os.environ.get("SNAPGEN_API_KEY", "").strip()


def load_history(uuid: str) -> dict:
    request = urllib.request.Request(
        f"{API_BASE}/history/{uuid}",
        headers={
            "x-api-key": KEY,
            "Accept": "application/json",
            "User-Agent": "HotelRoomNextDoor-AssetArchive/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        raw = json.load(response)
    if not isinstance(raw, dict):
        raise ValueError("History response is not a JSON object")
    return raw


def history_with_retries(uuid: str) -> dict:
    for attempt in range(4):
        try:
            return load_history(uuid)
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == 3:
                raise RuntimeError("Could not retrieve Snapgen history after retries") from None
            time.sleep(2 ** attempt)
    raise RuntimeError("Unreachable")


def assert_completed(history: dict, uuid: str) -> None:
    actual = history.get("uuid")
    if actual and actual != uuid:
        raise ValueError("History UUID does not match requested UUID")
    if history.get("status") != 2 and str(history.get("status_desc", "")).upper() != "COMPLETED":
        raise ValueError("Generation is not reported as completed")


def selected_url(history: dict, kind: str) -> str:
    field = "generated_image" if kind == "image" else "generated_video"
    key = "image_url" if kind == "image" else "video_url"
    medias = history.get(field) or []
    if not isinstance(medias, list):
        raise ValueError("Malformed generated-media list")
    for media in medias:
        if isinstance(media, dict) and media.get(key):
            url = media[key]
            if isinstance(url, str) and url.startswith("https://"):
                return url
    raise ValueError("Completed generation has no HTTPS media URL")


def download(url: str, out: Path, kind: str) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = out.with_suffix(out.suffix + ".partial")
    try:
        for attempt in range(4):
            try:
                request = urllib.request.Request(
                    url, headers={"User-Agent": "HotelRoomNextDoor-AssetArchive/1.0"}
                )
                with urllib.request.urlopen(request, timeout=90) as response, temp.open("wb") as file:
                    sha = hashlib.sha256()
                    byte_count = 0
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        file.write(chunk)
                        sha.update(chunk)
                        byte_count += len(chunk)
                if byte_count < 1024:
                    raise ValueError("Downloaded file unexpectedly small")
                with temp.open("rb") as file:
                    signature = file.read(32)
                if kind == "image" and not (
                    signature.startswith(b"\x89PNG\r\n\x1a\n")
                    or signature.startswith(b"\xff\xd8\xff")
                    or signature.startswith(b"RIFF") and b"WEBP" in signature
                ):
                    raise ValueError("Downloaded image has unexpected signature")
                if kind == "video" and b"ftyp" not in signature[:20]:
                    raise ValueError("Downloaded video is not MP4")
                temp.replace(out)
                return {"bytes": byte_count, "sha256": sha.hexdigest()}
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                if attempt == 3:
                    raise RuntimeError("Media download failed after retries") from None
                time.sleep(2 ** attempt)
    finally:
        if temp.exists():
            temp.unlink()
    raise RuntimeError("Download did not complete")


def one_asset(asset: dict) -> dict:
    uuid = asset["uuid"]
    kind = asset["kind"]
    aid = asset["id"]
    if kind not in ("image", "video") or re.fullmatch(r"[A-Z][A-Z0-9_]{1,49}", aid) is None:
        raise ValueError("Invalid asset manifest entry")
    if not re.fullmatch(r"[a-f0-9-]{36}", uuid):
        raise ValueError("Invalid generation UUID")
    response = history_with_retries(uuid)
    assert_completed(response, uuid)
    url = selected_url(response, kind)
    ext = ".png" if kind == "image" else ".mp4"
    out = OUTPUT / kind / (aid + ext)
    data = download(url, out, kind)
    return {"id": aid, "kind": kind, "uuid": uuid, "path": str(out), **data}


def main() -> int:
    if not KEY:
        print("Missing GitHub Actions secret SNAPGEN_API_KEY", file=sys.stderr)
        return 2
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = manifest.get("assets", [])
    if not assets:
        print("No generation UUIDs in manifest", file=sys.stderr)
        return 2
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results = []
    failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        mapping = {executor.submit(one_asset, asset): asset for asset in assets}
        for future in concurrent.futures.as_completed(mapping):
            asset = mapping[future]
            try:
                result = future.result()
                results.append(result)
                print(f"OK {asset['id']}: {result['bytes']} bytes, SHA-256 {result['sha256'][:12]}")
            except Exception as exc:
                # Avoid exposing signed media URLs in exception text.
                print(f"FAILED {asset['id']}: {type(exc).__name__}", file=sys.stderr)
                failed.append({"id": asset["id"], "error_type": type(exc).__name__})
    report = {
        "project": manifest.get("project"),
        "expected_count": len(assets),
        "downloaded_count": len(results),
        "assets": sorted(results, key=lambda item: item["id"]),
        "failures": failed,
    }
    (OUTPUT / "download-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(results)}/{len(assets)} assets")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
