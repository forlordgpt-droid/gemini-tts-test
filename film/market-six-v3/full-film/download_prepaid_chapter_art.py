#!/usr/bin/env python3
"""Fetch ONLY already-paid original SnapGen gpt-image-2.5-lower story illustrations.
No image generation, no model swaps, no substitutes. Chapter-specific durable QA cache.
"""
import argparse,concurrent.futures,hashlib,io,json,pathlib,time,urllib.request
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('--chapter',type=int,required=True);args=p.parse_args()
ch=args.chapter;assert 1<=ch<=15
BASE=pathlib.Path('film/market-six-v3/full-film')
manifest=json.loads((BASE/'paid-generation/ALL_131_ORIGINAL_ILLUSTRATIONS_VERIFIED.json').read_text())
assert manifest['exact_model']=='gpt-image-2.5-lower' and manifest['provider']=='SnapGen'
assert manifest['unique_job_count']==131 and manifest['verified_credits_spent']==131
assets=sorted([x for x in manifest['assets'] if x['key'].startswith(f'CH{ch:02d}_')],key=lambda x:x['key'])
assert len(assets)==(5 if ch==1 else 9),(ch,len(assets))
out=BASE/'chapter-projects'/f'ch{ch:02d}';raw=out/'raw';qa=out/'initial_art_qa'
raw.mkdir(parents=True,exist_ok=True);qa.mkdir(parents=True,exist_ok=True)
def fetch(pair):
    index,asset=pair
    if asset['model']!='gpt-image-2.5-lower' or asset['credits_used']!=1:raise RuntimeError('Wrong paid image model/charge; STOP')
    target=raw/f'raw_{index}.png'
    for attempt in range(2):
        try:
            req=urllib.request.Request(asset['url'],headers={'User-Agent':'Mozilla/5.0 MARKET-SIX-ORIGINAL-IMAGE-CACHE'})
            with urllib.request.urlopen(req,timeout=150) as r:data=r.read()
            if len(data)<75000:raise RuntimeError('Truncated SnapGen original image bytes')
            with Image.open(io.BytesIO(data)) as im:
                im.verify()
            with Image.open(io.BytesIO(data)) as im:
                w,h=im.size
                if not(1500<=w<=2200 and 1.75<w/h<1.82):raise RuntimeError(f'Wrong original illustration dimensions {(w,h)}')
            target.write_bytes(data)
            return {'key':asset['key'],'uuid':asset['uuid'],'file':target.name,'bytes':len(data),'width':w,'height':h,'sha256':hashlib.sha256(data).hexdigest(),'model':asset['model'],'previous_credits':asset['credits_used']}
        except Exception as e:
            if attempt==1:raise RuntimeError(f'Mandatory original SnapGen output retrieval failed {asset["key"]}: {e}') from e
            time.sleep(2)
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    records=list(ex.map(fetch,enumerate(assets)))
sheet=Image.new('RGB',(1920,1200),'#081525');d=ImageDraw.Draw(sheet)
for idx,asset in enumerate(assets):
    with Image.open(raw/f'raw_{idx}.png') as f:
        im=f.convert('RGB').resize((640,365),Image.Resampling.LANCZOS)
    x=(idx%3)*640;y=(idx//3)*400
    sheet.paste(im,(x,y+25))
    d.rectangle((x,y,x+640,y+25),fill='#091b33')
    d.text((x+14,y+6),asset['key']+'  /  ORIGINAL SNAPGEN PAINTING',fill='#f9e4bd')
sheet.save(qa/f'CH{ch:02d}_ORIGINAL_STORY_ILLUSTRATIONS_CONTACT.jpg',quality=88)
audit={'status':'SUCCESS_ALL_CHAPTER_SOURCE_IMAGES_RETRIEVED','chapter':ch,'provider':'SnapGen','exact_model':'gpt-image-2.5-lower','source_credits_already_spent':len(records),'new_paid_jobs':0,'source_verified':records}
(qa/'CHAPTER_SOURCE_PAINTING_AUDIT.json').write_text(json.dumps(audit,indent=2))
assert len(list(raw.glob('raw_*.png')))==len(assets)
print('PASS',ch,'downloaded',len(assets),'genuine rich original 2D illustrated paintings, no paid jobs',flush=True)
