#!/usr/bin/env python3
"""Restore *exact* AAC bitstream from the user-approved Drive master.

Only the MP4 wrapper is remuxed, never the video frames or AAC packets.
The GitHub historical artifact has video-identical content but a distinct AAC
track; do not treat it as the approved narrated source.
"""
from pathlib import Path
import hashlib, json, subprocess

ROOT=Path('film/rain-v4-first300')
VIDEO=Path('first120/RAIN_V4_FIRST120_COMPLETE.mp4')
PART=ROOT/'approved120_audio_parts'
OUT=Path('first120/RAIN_V4_APPROVED_STREAMS_REMUX.mp4')
META=json.loads((ROOT/'film_manifest.json').read_text())
EXPECTED_APPROVED='85ed2c24b43d7d528062a743caa5be2d01dae0030b0049be58a087be2224ddf4'
EXPECTED_ARCHIVED='4f30ead382cff713e0be277d4189e19b0d83a7d58739108019ab1d8962f46426'
EXPECTED_VIDEO='f8a4f063b86531492fd29086c18dea1512e818b8a84840ccad6025c9b2a60e98'
EXPECTED_AUDIO='2bebd840ecbdc89183d4cb53fc140b229a9db4d9b6afc3ff7623ee1b45ca9d44'
EXPECTED_PARTS=[
('audio_00.part',360000,'686ef1a74c58a8aa2f24e1b0d54a34a6bf46bc97f38f0cda53946a766c471c48'),
('audio_01.part',360000,'a7720d0fd7dfab7e5d2479c848274333827b3c2327f81405ab5e4f9191b71882'),
('audio_02.part',360000,'e02625846ce51ef7f04163e31f6cc8ee391f4d17070067377d2d204feb102e36'),
('audio_03.part',360000,'104d6911ccdd9ed29795b3a6100dbf47041c43d941c8dd9e897efc76236de5ba'),
('audio_04.part',360000,'49fd1d9dd0fe85d55adbe671d8db6f12055a8e309e717989d289d1ec8596ea3a'),
('audio_05.part',360000,'5a24b880527ce3468d892b0e3e070ae17b96286f08c65ea70bb960a61f4bc82d'),
('audio_06.part',234386,'cbab40392ccb9668657b98d72c70697f86b0587661a407c0091c17fb3db435e8'),
]
def sha(data):return hashlib.sha256(data).hexdigest()
def file_hash(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for ch in iter(lambda:f.read(1024*1024),b''):h.update(ch)
 return h.hexdigest()
def stream_hash(p,kind):
 fmt={'video':('v:0','h264'),'audio':('a:0','adts')}
 stream,container=fmt[kind]
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-i',str(p),'-map','0:'+stream,'-c','copy','-f',container,'pipe:1']
 proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 h=hashlib.sha256()
 while True:
  b=proc.stdout.read(1024*1024)
  if not b:break
  h.update(b)
 error=proc.stderr.read().decode(errors='replace')
 if proc.wait()!=0:raise RuntimeError('Failed to verify '+kind+' essence: '+error[-500:])
 return h.hexdigest()
assert META['approved_first120_sha256']==EXPECTED_APPROVED, 'Provenance metadata does not match user-approved Drive file'
assert VIDEO.is_file() and file_hash(VIDEO)==EXPECTED_ARCHIVED, 'GitHub archived master changed; stop'
assert stream_hash(VIDEO,'video')==EXPECTED_VIDEO, 'Archived video pixels not the approved video'
AAC=PART/'approved_first120_audio.aac'
with AAC.open('wb') as out:
 for name,n,digest in EXPECTED_PARTS:
  raw=(PART/name).read_bytes()
  assert len(raw)==n and sha(raw)==digest,name
  out.write(raw)
assert AAC.stat().st_size==2394386 and file_hash(AAC)==EXPECTED_AUDIO, 'Approved AAC bitstream changed'
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(VIDEO),'-fflags','+genpts','-i',str(AAC),'-map','0:v:0','-map','1:a:0','-c','copy','-movflags','+faststart',str(OUT)],check=True)
assert stream_hash(OUT,'video')==EXPECTED_VIDEO, 'Failed video essence verification after remux'
assert stream_hash(OUT,'audio')==EXPECTED_AUDIO, 'Failed audio essence verification after remux'
# Preserve *every* approved AAC packet; do not trim the last packet.
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,codec_type,nb_frames:format=duration','-of','json',str(OUT)]))
v=next(z for z in probe['streams'] if z['codec_type']=='video');a=next(z for z in probe['streams'] if z['codec_type']=='audio')
assert int(v['nb_frames'])==3600 and int(a['nb_frames'])==5626,(v,a)
assert abs(float(probe['format']['duration'])-120)<0.15,probe
approved_audit={
 'source_original_mp4_sha256':EXPECTED_APPROVED,'archived_video_mp4_sha256':EXPECTED_ARCHIVED,
 'remux_sha256':file_hash(OUT),'approved_video_sha256':EXPECTED_VIDEO,'approved_audio_sha256':EXPECTED_AUDIO,
 'approved_video_identical':True,'approved_audio_identical':True,
 'note':'Stream-copy remux changes MP4 container hash; H.264 and AAC stream bytes exactly match the delivered user-approved version.',
 'new_paid_calls':0}
(ROOT/'approved120_stream_audit.json').write_text(json.dumps(approved_audit,indent=2)+'\n')
OUT.replace(VIDEO)
assert file_hash(VIDEO)==approved_audit['remux_sha256']
print('PASS: all 3600 original approved video frames and 5626 original approved AAC packets restored without re-encoding',flush=True)
