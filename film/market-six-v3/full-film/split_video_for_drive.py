#!/usr/bin/env python3
"""Split already verified original completed H.264/AAC 15-min MP4 into transfer-safe pieces.
The immutable MP4 bytes are not transcoded or regenerated. Reversible sha256-safe transfer packaging.
"""
from pathlib import Path
import argparse,hashlib,json,math,os
p=argparse.ArgumentParser()
p.add_argument('--video',default='final_full/100_DAYS_ABANDONED_SUPERMARKET_COMPLETE_15_MINUTE_FILM.mp4')
p.add_argument('--chunk-mib',type=int,default=80)
args=p.parse_args()
src=Path(args.video)
if not src.is_file() or src.stat().st_size<200000000:raise RuntimeError(f'Missing complete full movie, cannot split: {src}')
out=Path('final_full/video_parts');out.mkdir(parents=True,exist_ok=True)
CHUNK=args.chunk_mib*1024*1024
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
original_sha=sha(src); size=src.stat().st_size
pieces=[];number=0
with open(src,'rb') as r:
    while True:
        data=r.read(CHUNK)
        if not data:break
        path=out/f'PART_{number:02d}.bin';path.write_bytes(data)
        pieces.append({'name':path.name,'size_bytes':len(data),'sha256':sha(path),'index':number})
        number+=1
if not pieces or len(pieces)>48:raise RuntimeError(f'Unexpected full video parts count {len(pieces)} for {size} bytes')
h=hashlib.sha256()
for p in pieces:
    with open(out/p['name'],'rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
if h.hexdigest()!=original_sha:raise RuntimeError('Lossless multipart export mismatch - no delivery until fixed')
manifest={'status':'PASS_LOSSLESS_ORIGINAL_15MIN_MP4_TRANSFER','filename':src.name,
           'file_size_bytes':size,'sha256_full_movie':original_sha,'parts':pieces,
           'chunk_size_max_bytes':CHUNK,'media_models_unmodified':True,
           'no_new_paid_generation':True,'exact_reassembly':'Concatenate PART_00.bin ... in ascending index order; verify SHA256 against sha256_full_movie'}
(out/'TRANSFER_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
print('PASS split complete original 900s finished film into',number,'pieces of at most',args.chunk_mib,'MiB without transcoding or re-generating',original_sha,flush=True)
