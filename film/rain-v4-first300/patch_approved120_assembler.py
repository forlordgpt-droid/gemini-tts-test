#!/usr/bin/env python3
"""Preserve provenance guard while verifying *streams*, not remux container bytes.
The previously approved Drive MP4 is identified by SHA256; the GitHub MP4 has
identical H264 bitstream but different AAC. restore_approved120_streams.py
replaces the AAC with the exact approved audio stream and checks both hashes.
"""
from pathlib import Path
p=Path('film/rain-v4-first300/assemble300.py')
s=p.read_text(encoding='utf-8')
needle=" assert OLD.is_file() and sha(OLD)==MAN['approved_first120_sha256'],'Original audio source altered'"
replacement=""" assert OLD.is_file(), 'Missing restored approved audio/video'
 audit=json.loads((ROOT/'approved120_stream_audit.json').read_text())
 assert audit['source_original_mp4_sha256']==MAN['approved_first120_sha256'], 'Approved Drive provenance changed'
 assert audit['approved_video_identical'] and audit['approved_audio_identical'], 'Approved source stream verification missing'
 assert sha(OLD)==audit['remux_sha256'], 'Stream-verified remux changed after audit'"""
assert s.count(needle)==1,'Unexpected assembler version: refuse to weaken validation'
p.write_text(s.replace(needle,replacement),encoding='utf-8')
print('PASS: strong content-level source integrity replaces invalid wrapper byte-identity check')
