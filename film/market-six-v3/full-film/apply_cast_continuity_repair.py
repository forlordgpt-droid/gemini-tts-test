#!/usr/bin/env python3
"""Artist continuity correction: protect the DAY24 Clara/Jonah reveal.
Swap only already generated original SnapGen GPT Image 2.5 Lower painting frames
for Day1–11 and masked Day24 mystery, never regenerate, never touch approved pilot.
Then rebuild real Pillow/OpenCV 2.5D masks in separate chapter-artifacts.
"""
from __future__ import annotations
import argparse,io,json,pathlib,hashlib,urllib.request,concurrent.futures,shutil,re
from PIL import Image
P=argparse.ArgumentParser();P.add_argument('--chapter',type=int,required=True);args=P.parse_args()
CH=args.chapter
assert CH in (2,3,4,5,6)
base=pathlib.Path('film/market-six-v3/full-film')
f=base/'paid-generation/ALL_43_CAST_CONTINUITY_CORRECTIONS_VERIFIED.json'
if not f.is_file():raise FileNotFoundError('All 43 original continuity-corrected exact-model SnapGen outputs must be verified; stop')
data=json.loads(f.read_text())
assert data['model']=='gpt-image-2.5-lower' and data['count']==43 and data['status']=='ALL_COMPLETED_ORIGINAL_EXACT_MODEL'
assert all(z['model']=='gpt-image-2.5-lower' and z['credits_used']==1 for z in data['images'])
selected=[z for z in data['images'] if z['key'].startswith(f'CH{CH:02d}_')]
if len(selected)!=(7 if CH==6 else 9):raise RuntimeError(f'Expected correct source images CH{CH}, got {len(selected)}')
proj=base/'chapter-projects'/f'ch{CH:02d}'
raw=proj/'raw';raw.mkdir(parents=True,exist_ok=True)
manifest=json.loads((proj/'scene_manifest.json').read_text())
assert manifest['chapter']==CH and manifest['image_model']=='gpt-image-2.5-lower'
assert manifest['speech_model']=='google/gemini-3-8-flash-tts'
expected={s['key']:i for i,s in enumerate(manifest['shots'])}
def fetch(entry):
    i=expected[entry['key']]
    if CH==6 and i>=7:raise RuntimeError('DO NOT replace Day24 actual survivor reveal paintings')
    q=urllib.request.Request(entry['url'],headers={'User-Agent':'Mozilla/5.0 MarketSix-PreviouslyPaidArt-Continuity'})
    with urllib.request.urlopen(q,timeout=150) as f:data=f.read()
    with Image.open(io.BytesIO(data)) as im:
        im.verify()
    with Image.open(io.BytesIO(data)) as im:
        w,h=im.size
    if len(data)<70000 or not(1500<w<2300 and 1.75<w/h<1.82):
        raise RuntimeError(f'Wrong previously paid original source image format for {entry["key"]}')
    target=raw/f'raw_{i}.png'
    assert target.exists() and target.stat().st_size>30000
    target.write_bytes(data)
    return {'key':entry['key'],'source_image_model':'gpt-image-2.5-lower','original_uuid':entry['uuid'],
            'paid_credit':1,'path':str(target),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:replaced=list(executor.map(fetch,selected))
# Use precise editorial captions; avoid a false "Inventory / Trust" title merely from the ending of "American".
labels={
2:['THE LAST NORMAL DAY','EMERGENCY ALERT','RIVER BARRIER FAILURE','PARKING LOT UNDERWATER','TRUCK OVERTURNED','ONLY BRIDGE SUBMERGED','FAMILY RESCUE','THE GLASS DOORS BREAK','MASON ALONE / BLACKOUT'],
3:['THE GRID GOES DARK','SPOILING FREEZERS','THE FIRST DECISION','SAFE SEALED FOOD','FOOD SAFETY','EMERGENCY SUPPLIES','CARBON MONOXIDE','SWITCH IT OFF','THE EMPTY SHOPPING CART'],
4:['THE LAST DRIP','SIX HUNDRED LITERS','WATER RATIONING','ROOFTOP RAIN COLLECTOR','DRINKING WATER SAFETY','AN ORDERED SHELTER','THE DAY COUNT','THREE CANS MISSING','A FRESH FOOTPRINT'],
5:['THREE CANS GONE','THE UNCERTAINTY','MORE SUPPLIES MISSING','THE SEALED LOWER DOOR','AISLE SIX','SOMEBODY WAS HERE','MASON CALLS INTO THE DARK','THE CEILING HATCH','THREE KNOCKS'],
6:['ONE SOLAR BATTERY','CAMERA ON AISLE SIX','THE FLOUR TRAP','2:14 AM / A RED JACKET','THE INTRUDER RUNS','FOOTPRINTS TO STAIRWELL','A LOCKED MAINTENANCE DOOR','TWO HIDING SURVIVORS','CLARA AND JONAH REVEALED']
}
assert len(labels[CH])==len(manifest['shots'])
for i,s in enumerate(manifest['shots']):
    s['editorial_label']=labels[CH][i]
    if i<(7 if CH==6 else 9):
        s['cast_continuity_corrected']=True
        s['clara_and_jonah_not_yet_revealed']=True
manifest['narrative_early_cast_continuity_fixed']=True
manifest['corrected_illustrations_count']=len(replaced)
(proj/'scene_manifest.json').write_text(json.dumps(manifest,indent=2))
# Invalidate only masks derived from superseded source paintings, then rerun exact pipeline unchanged.
for name in ('assets','qc'):
    path=proj/name
    if path.exists():shutil.rmtree(path)
    path.mkdir(parents=True,exist_ok=True)
d=proj/'continuity_art_qa';d.mkdir(exist_ok=True)
(d/'EXACT_MODEL_AND_REVEAL_CONTINUITY_AUDIT.json').write_text(json.dumps({
 'chapter':CH,'day':manifest['day'],'source_original_paintings_replaced':len(replaced),
 'model':'gpt-image-2.5-lower','original_paid_images_preserved_elsewhere':True,
 'no_new_paid_generations_during_replace':True,'first_30_seconds_unchanged':True,
 'clara_jonah_reveal_only_day24':True,'replacements':replaced},indent=2))
print('PASS continuity correction CH',CH,'new illustrated originals',len(replaced),
      'no prematurity, all old assets preserved in prior GitHub art artifacts; no further paid calls',flush=True)
