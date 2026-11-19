#!/usr/bin/env python3
"""Offline deterministic restore and integrity audit of approved image artwork."""
from pathlib import Path
import json,hashlib,io,zipfile
root=Path('film/rain-v4-first120')
chunks=json.loads((root/'asset_chunks_120.json').read_text())
manifest=json.loads((root/'asset_manifest.json').read_text())
assert len(chunks['parts'])==chunks['count']==10
b=bytearray()
for item in chunks['parts']:
 p=root/'asset_parts'/item['name']
 assert p.is_file(),p
 raw=p.read_bytes();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],p
 b.extend(raw)
assert len(b)==chunks['total_bytes'] and hashlib.sha256(b).hexdigest()==chunks['zip_sha256']
z=zipfile.ZipFile(io.BytesIO(b));assert z.testzip() is None
expected={m['filename']:m for m in manifest['assets']}
assert len(expected)==24 and set(z.namelist())==set(expected)
folder=root/'scenes'/'assets';folder.mkdir(parents=True,exist_ok=True)
for name in sorted(expected):
 assert '/' not in name and name.endswith('.webp'),name
 data=z.read(name)
 assert hashlib.sha256(data).hexdigest()==expected[name]['sha256'] and len(data)==expected[name]['bytes'],name
 (folder/name).write_bytes(data)
print('PASS 24 approved original-painting-derived assets; 0 image-generation calls',flush=True)
