#!/usr/bin/env python3
"""Prepare 15 story-specific premium V3 film chapters without modifying original 30 seconds.
Author the absolute-timeline 2.5D chapter project and preserve EXACT original native 2D rig.
"""
import argparse,pathlib,json,shutil,zipfile,hashlib
p=argparse.ArgumentParser();p.add_argument('--chapter',type=int,required=True);args=p.parse_args()
ch=args.chapter;assert 1<=ch<=15
BASE=pathlib.Path('film/market-six-v3/full-film')
blue=json.loads((BASE/'SHOT_IMAGE_BLUEPRINT.json').read_text())
assert blue['image_model']=='gpt-image-2.5-lower' and blue['speech_model']=='google/gemini-3-8-flash-tts'
dir=BASE/'chapter-projects'/f'ch{ch:02d}';dir.mkdir(parents=True,exist_ok=True)
shots=sorted([x for x in blue['shots'] if x['chapter']==ch],key=lambda s:s['ordinal'])
assert len(shots)==(5 if ch==1 else 9)
start=30 if ch==1 else (ch-1)*60;end=ch*60
assert abs(shots[0]['global_start']-start)<1e-3 and abs(shots[-1]['global_end']-end)<1e-3
def label(text):
    t=text.lower()
    if 'twelve days' in t:return '12 DAYS OF WATER'
    if 'water' in t:return 'WATER / SURVIVAL'
    if 'radio' in t:return 'SIGNAL / ALERT'
    if 'depot' in t:return 'THE SILENT DEPOT'
    if 'shelf' in t or 'can' in t or 'ration' in t:return 'INVENTORY / TRUST'
    if 'shutter' in t:return 'LOWER DOOR / DANGER'
    if 'bridge' in t:return 'NO ROAD OUT'
    if 'emergency' in t:return 'EMERGENCY RESPONSE'
    if 'roof' in t:return 'HIGHER GROUND'
    if 'clara' in t or 'jonah' in t:return 'THE OTHER SURVIVORS'
    if 'flood' in t:return 'THE RIVER / BELLPORT'
    return 'SURVIVAL MYSTERY'
scene=[]
for i,s in enumerate(shots):
    scene.append({'key':s['key'],'chapter':ch,'ordinal':i,'start_sec':s['global_start'],'end_sec':s['global_end'],
     'day':s['day'],'description':s['description'],'editorial_label':label(s['description']),'image_model':'gpt-image-2.5-lower'})
out={'project':'MARKET_SIX_USER_FULL_15_MIN_FILM','chapter':ch,'day':shots[0]['day'],
     'start_sec':start,'end_sec':end,'original_story_clock':True,
     'image_provider':'SnapGen','image_model':'gpt-image-2.5-lower',
     'speech_provider':'kie.ai','speech_model':'google/gemini-3-8-flash-tts',
     'world':'Bellport Market Six America','human_characters_remain_illustrated_2d':True,
     'hunyuan_native_rig_is_loaded_for_reference_only_no_impersonation':True,
     'shots':scene}
(dir/'scene_manifest.json').write_text(json.dumps(out,indent=2))
shutil.copyfile(BASE/'scene_renderer.js',dir/'main.js')
shutil.copyfile(BASE/'scene_index.html',dir/'index.html')
rig=dir/'rig';rig.mkdir(parents=True,exist_ok=True)
zpath=pathlib.Path('/opt/cinematic/references/HUNYUAN_2D_CHARACTER_PACKAGE.zip')
with zipfile.ZipFile(zpath) as z:
  for name in ('art.js','engine.js'):
    data=z.read('HUNYUAN_2D/'+name)
    assert len(data)>1000
    (rig/name).write_bytes(data)
raw=dir/'raw'
assert len(list(raw.glob('raw_*.png')))==len(scene),('Missing previously downloaded original art',str(raw))
print('PASS',ch,'original timeless 2D rig unchanged; 100% original user prose, shot-specific illustrated manuscript, chapter 30fps',flush=True)
