#!/usr/bin/env python3
"""Reproducible offline V3 source + UNCHANGED original Hunyuan reference pack.
No user secrets, no font file redistribution, no paid media calls.
"""
from pathlib import Path
from zipfile import ZipFile,ZIP_STORED,ZIP_DEFLATED
import json,hashlib,sys
ENGINE=Path(__file__).resolve().parents[1]
REPO=ENGINE.parents[1]
OUT=REPO/'release/HUNYUAN_CINEMATIC_ENGINE_V3_SOURCE_AND_UNCHANGED_REFERENCES.zip'
OUT.parent.mkdir(exist_ok=True,parents=True)
spec=json.loads((ENGINE/'config/ORIGINAL_REFERENCE_SHA256.json').read_text())
entries={}
def add(filepath,arc):
    data=Path(filepath).read_bytes()
    if arc in entries:raise RuntimeError('Duplicate archive entry '+arc)
    entries[arc]=data
    return data
for f in ENGINE.rglob('*'):
    if not f.is_file():continue
    rel=f.relative_to(ENGINE)
    if rel.parts[0] in ('reference_input','__pycache__','node_modules','.git'):continue
    if f.suffix in ('.pyc','.mp4','.wav','.jpg','.png','.zip'):continue
    if any(t in f.name.lower() for t in ('api_key','.env','secret_token')):continue
    add(f,'engine/'+rel.as_posix())
for workflow in ('hunyuan-v3-environment.yml','hunyuan-v3-cold-start-test.yml','hunyuan-v3-longform-production.yml'):
    f=REPO/'.github/workflows'/workflow
    if f.exists():add(f,'workflows/'+workflow)
refs=REPO/'film/hunyuan-2m'
for x in spec['references']:
    f=ENGINE/'reference_input'/x['filename'] if x['filename'].endswith('.mp4') else refs/x['filename']
    data=add(f,'original_unchanged/'+x['filename'])
    if hashlib.sha256(data).hexdigest()!=x['sha256']:raise RuntimeError('Original reference was changed: '+str(f))
for x in spec['text_files']:
    file=ENGINE/x['path']
    d=file.read_bytes()
    if len(d)!=x['bytes'] or hashlib.sha256(d).hexdigest()!=x['sha256']:raise RuntimeError('Original user instruction changed: '+str(file))
meta={'status':'Verified source + unchanged 2D user instructions and 30s reference',
      'source_prefix':'engine/','references_prefix':'original_unchanged/',
      'contains_original_30_second_mp4':True,'contains_original_native_2d_art_js_engine_js':True,
      'contains_3d_human_character_substitution':False,'tool_or_model_substitutions':False,
      'paid_api_generation_calls':0,
      'files':{key:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for key,data in sorted(entries.items())}}
with ZipFile(OUT,'w') as z:
    for arc,data in sorted(entries.items()):
        z.writestr(arc,data,compress_type=ZIP_STORED if arc.endswith(('.mp4','.zip')) else ZIP_DEFLATED)
    z.writestr('SOURCE_AND_REFERENCE_SHA256_MANIFEST.json',json.dumps(meta,indent=2),compress_type=ZIP_DEFLATED)
    z.writestr('START_HERE.txt',
      'READ engine/AGENTS.md, engine/authoritative/* in full.\nWatch original_unchanged/HUNYUAN_FIRST_30S_PARALLAX_PREVIEW.mp4.\n'
      'Use original_unchanged/HUNYUAN_2D_CHARACTER_PACKAGE.zip art.js and engine.js for the native 2D Hunyuan rig only.\n'
      'Use GHCR environment and repo workflows, not a generic or photorealistic substitute.\n'
      'No API keys or paid generations are included. New story assets and Kie TTS need separate explicit approval.\n')
with ZipFile(OUT) as z:
    if z.testzip() is not None:raise RuntimeError('Packaged archive corrupt')
    for p,d in entries.items():
        if hashlib.sha256(z.read(p)).digest()!=hashlib.sha256(d).digest():
            raise RuntimeError('Archive byte mismatch '+p)
print(json.dumps({'file':str(OUT),'bytes':OUT.stat().st_size,'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
    'file_count':len(entries),'originals_verbatim':True},indent=2))
