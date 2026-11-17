#!/usr/bin/env python3
"""HARD FAILURE GATE for the exact approved Hunyuan 2D cinematic pipeline.
No new images/audio requested or charged here.
Never silently substitute the character rig, motion method, models, or software.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, subprocess, sys, zipfile
from PIL import Image
import cv2

ENGINE = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ENGINE/'config/ORIGINAL_REFERENCE_SHA256.json').read_text())
LOCKS = json.loads((ENGINE/'config/LOCKED_MODELS_AND_GATES.json').read_text())
REFS = pathlib.Path(os.getenv('HUNYUAN_REFERENCE_DIR','/opt/cinematic/references'))
if not REFS.is_dir():
    REFS = ENGINE/'references'

def die(msg):
    raise RuntimeError('HUNYUAN_V3_PREFLIGHT_FAIL: '+msg)

def check_hash(path, expected, size=None):
    if not path.is_file(): die('Missing exact reference file '+str(path))
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected: die('Reference changed! '+str(path)+' sha='+digest+' expected='+expected)
    if size is not None and path.stat().st_size != size:die('Reference byte length changed '+str(path))
    return str(path)

def proc(*args, cwd=None):
    p=subprocess.run(args,cwd=cwd,check=True,text=True,capture_output=True)
    return p.stdout.strip()

def check():
    print('HUNYUAN V3: verification of authoritative unchanged originals')
    assert LOCKS['no_substitutions'] is True
    assert LOCKS['characters_must_remain_2d'] is True
    assert LOCKS['paid_generation_default']=='DISABLED'
    assert LOCKS['exact_models']['illustrations']['model']=='gpt-image-2.5-lower'
    assert LOCKS['exact_models']['speech']['model']=='google/gemini-3-8-flash-tts'
    for x in MANIFEST['text_files']:
        print('  AUTHORITATIVE',check_hash(ENGINE/x['path'],x['sha256'],x['bytes']))
    for x in MANIFEST['references']:
        print('  ORIGINAL REFERENCE',check_hash(REFS/x['filename'],x['sha256'],x['bytes']))
    with zipfile.ZipFile(REFS/'HUNYUAN_2D_CHARACTER_PACKAGE.zip') as z:
        if z.testzip() is not None:die('Original character rig ZIP corrupt')
        required={'HUNYUAN_2D/art.js','HUNYUAN_2D/engine.js','HUNYUAN_2D/assets/RIG.json','HUNYUAN_2D/assets/Hunyuan_MODEL_SHEET.svg'}
        if not required.issubset(z.namelist()):die('Original 2D Hunyuan rig API/illustration missing')
        print('  Native authored Hunyuan 2D art.js + engine.js OK; 3D rig substitution prohibited')
    with zipfile.ZipFile(REFS/'HUNYUAN_30S_PARALLAX_SOURCE.zip') as z:
        if z.testzip() is not None:die('Original Three.js 2.5D source ZIP corrupt')
        names=z.namelist()
        if sum(x.endswith('.jpg') for x in names)!=6 or sum(x.endswith('.webp') for x in names)!=12:
            die('Approved original 6 compositions + 12 depth layers not present')
        if not any(x.endswith('main.js') for x in names):die('Original camera/animation source missing')
    movie=REFS/'HUNYUAN_FIRST_30S_PARALLAX_PREVIEW.mp4'
    meta=json.loads(proc('ffprobe','-v','error','-show_entries','stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames:format=duration','-of','json',str(movie)))
    v=next((s for s in meta['streams'] if s['codec_type']=='video'),None)
    a=next((s for s in meta['streams'] if s['codec_type']=='audio'),None)
    if not v or not a:die('Approved video reference missing video or audio')
    if (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))!=('h264',1920,1080,'30/1',900):die('Approved preview no longer 1080p/900 frames')
    if a['codec_name']!='aac' or abs(float(meta['format']['duration'])-30)>.08:die('Approved reference audio or duration mismatch')
    version=proc('node','--version')
    if not version.startswith('v22.'):die('Pinned Node 22 runtime required, found '+version)
    print('  ffmpeg:',proc('ffmpeg','-version').splitlines()[0])
    print('  ffprobe:',proc('ffprobe','-version').splitlines()[0])
    print('  Node:',version,'Pillow:',Image.__version__,'OpenCV:',cv2.__version__)
    if os.getenv('HUNYUAN_SKIP_NODE_PACKAGE_CHECK')!='1':
        cmd="""import * as THREE from 'three';import gsap from 'gsap';import {Output,CanvasSource,Mp4OutputFormat} from 'mediabunny';import {createRequire} from 'node:module';const require=createRequire(import.meta.url);const pw=require('playwright');if(typeof THREE.PerspectiveCamera!=='function'||typeof gsap.timeline!=='function'||typeof Output!=='function'||typeof CanvasSource!=='function'||typeof Mp4OutputFormat!=='function'||typeof pw.chromium.launch!=='function')throw Error('Required exact JS API missing');console.log('Three.js PerspectiveCamera, GSAP, WebCodecs/Mediabunny, Playwright: OK')"""
        print('  '+proc('node','--input-type=module','-e',cmd,cwd='/opt/cinematic'))
    gates=LOCKS['human_approval_gates']
    if gates[0]['phase']!='first 10 seconds' or gates[1]['phase']!='first complete 30 seconds':die('Artist approval gates removed')
    print('PASS: exact unchanged instructions, original rig, original source, approved video and required tools.')
    print('PASS: zero credit-consuming API calls permitted by environment preflight')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--check',action='store_true')
    a=p.parse_args()
    try:check()
    except Exception as e:
        print('FAIL',type(e).__name__,str(e),file=sys.stderr)
        sys.exit(1)
