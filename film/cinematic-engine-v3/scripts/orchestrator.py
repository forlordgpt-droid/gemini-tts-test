#!/usr/bin/env python3
"""Reusable deterministic 2.5D film shot/shard planner. No paid service calls.
Preserves original creative gates and plans up to 15 minutes with many CPUs.
Project-specific story artwork and animation remain authored, not generic.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys, re

HERE=pathlib.Path(__file__).resolve().parents[1]
LOCK=json.loads((HERE/'config/LOCKED_MODELS_AND_GATES.json').read_text())
EPS=1e-7
SHARD_DEFAULT=10
VALID_PHASES={'first10','first30','remainder','all'}
PHASE_REQUIRED={'first10':None,'first30':'first10_approved','remainder':'first30_approved','all':'first30_approved'}

def bad(msg):raise ValueError(msg)
def require(check,msg):
    if not check:bad(msg)
def load(path):
    p=pathlib.Path(path).resolve()
    obj=json.loads(p.read_text())
    return p,obj
def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def validate(manifest, strict=False, phase='first10'):
    require(isinstance(manifest,dict),'Manifest must be a JSON object')
    require(re.fullmatch(r'[a-zA-Z0-9_-]{3,80}',manifest.get('project_id','')) is not None,'project_id must be stable, 3-80 safe characters')
    fmt=manifest.get('format',{})
    require(fmt=={'width':1920,'height':1080,'fps':30,'video_codec':'h264','audio_codec':'aac'},'NO SUBSTITUTIONS: export must be FullHD/30fps/H.264/AAC')
    seconds=manifest.get('duration_seconds')
    require(type(seconds) is int and 30<=seconds<=3600,'Duration must be an integer number of seconds, 30-3600')
    require(manifest.get('story_source'),'Story file/source required')
    require(manifest.get('image_model')=='gpt-image-2.5-lower','SnapGen model change forbidden')
    require(manifest.get('tts_model')=='google/gemini-3-8-flash-tts','Kie Gemini 3.8 Flash model change forbidden')
    require(manifest.get('image_provider')=='SnapGen' and manifest.get('tts_provider')=='kie.ai','Providers locked')
    require(manifest.get('camera')=='Three.js PerspectiveCamera','True perspective camera is mandatory')
    require(manifest.get('animation')=='GSAP paused absolute-time','GSAP absolute-time is mandatory')
    require(manifest.get('character_rig')=='original native Hunyuan 2D art.js + engine.js','Original 2D rig must be retained')
    approvals=manifest.get('approvals',{})
    require(type(approvals) is dict,'approvals must be explicit')
    for flag in ('first10_approved','first30_approved'):
        require(type(approvals.get(flag)) is bool,flag+' must be explicit boolean')
    require(phase in VALID_PHASES,'Unknown phase')
    needed=PHASE_REQUIRED[phase]
    if needed:
        require(approvals.get(needed) is True,phase+' requires previous visible user approval: '+needed)
    money=manifest.get('paid_media',{})
    require(money.get('default_disabled') is True,'Paid media must be DISABLED by default')
    require(money.get('image_generation_approved') is False or money.get('image_generation_approved') is True,'Paid image approval boolean missing')
    require(money.get('tts_generation_approved') is False or money.get('tts_generation_approved') is True,'Paid TTS approval boolean missing')
    if money.get('image_generation_approved'):
        for k in ('image_jobs','max_image_credits','credit_estimate_per_image'):
            require(isinstance(money.get(k),(float,int)) and money[k]>0,'Missing explicit image budget: '+k)
    if money.get('tts_generation_approved'):
        for k in ('tts_jobs','max_tts_credits','credit_estimate_per_tts_job'):
            require(isinstance(money.get(k),(float,int)) and money[k]>0,'Missing explicit TTS budget: '+k)
    shots=manifest.get('shots',[])
    require(isinstance(shots,list) and len(shots)>0,'Story-specific shot list cannot be empty')
    next_frame=0;names=set()
    for i,shot in enumerate(shots):
        ident=shot.get('id')
        require(isinstance(ident,str) and ident not in names and len(ident)>1,'Duplicate/invalid shot id')
        names.add(ident)
        start,end=shot.get('start_frame'),shot.get('end_frame')
        require(type(start) is int and type(end) is int and start==next_frame and end>start,f'{ident}: story frame coverage gap/overlap')
        next_frame=end
        for k in ('story_beat','art_direction','character_action','lighting','transition','sound_cues','motion_graphics_purpose'):
            require(isinstance(shot.get(k),str) and shot[k].strip(),f'{ident}: missing narrative/art requirement {k}')
        layers=shot.get('layers')
        require(isinstance(layers,dict) and set(layers)=={'foreground','midground','background'},f'{ident}: three independent depth planes mandatory')
        require(all(isinstance(p,str) and len(p)>3 for p in layers.values()),f'{ident}: source planes missing')
        require(len(set(layers.values()))==3,f'{ident}: a flat artwork reused for all three planes is prohibited')
        camera=shot.get('camera',{})
        for name in ('start','end'):
            q=camera.get(name,{})
            require(all(type(q.get(k)) in (float,int) for k in ('x','y','z')),f'{ident}: explicit 3D PerspectiveCamera {name} missing')
        a,b=camera['start'],camera['end']
        require(sum(abs(a[k]-b[k]) for k in ('x','y','z'))>0.08,f'{ident}: static camera shot violates visible choreography')
        if strict:
            for name,p in layers.items():
                require(pathlib.Path(p).is_file(),f'{ident}: missing actual {name} artwork {p}')
    require(next_frame==seconds*30,f'Shot coverage {next_frame} frames does not equal requested duration {seconds*30}')
    return {'project_id':manifest['project_id'],'duration_seconds':seconds,'frames':next_frame,'shots':len(shots),'model_locked':True,'phase':phase,'storyboard_hash':digest(manifest)}

def frame_limits(seconds,phase):
    total=seconds*30
    if phase=='first10':return 0,min(300,total)
    if phase=='first30':return 0,min(900,total)
    if phase=='remainder':return min(900,total),total
    return 0,total

def plan(m,phase,chunk_seconds,max_parallel):
    assert chunk_seconds in (5,10,15,20,30),'Shard length must be 5,10,15,20,30 seconds'
    assert 1<=max_parallel<=24,'Max parallel runners must be between 1 and 24'
    info=validate(m,phase=phase)
    first,last=frame_limits(m['duration_seconds'],phase)
    groups=[]
    for i,start in enumerate(range(first,last,chunk_seconds*30)):
        end=min(last,start+chunk_seconds*30)
        beats=[s['id'] for s in m['shots'] if s['end_frame']>start and s['start_frame']<end]
        chunk={ 'project_id':m['project_id'], 'shard_index':i, 'start_frame':start,
          'end_frame':end,'start_seconds':start/30,'duration_frames':end-start,
          'fps':30,'shots':beats, 'render_contract':'window.renderFrame(absolute_time); WebCodecs CanvasSource.add(local_frame/30,1/30)',
          'source_shot_sha256':digest([s for s in m['shots'] if s['id'] in beats]),
          'cache_key':digest({'version':'v3-locked','shot_sha':digest([s for s in m['shots'] if s['id'] in beats]),'start':start,'end':end})[:24]}
        groups.append(chunk)
    return {'description':'Reference-locked, no-paid-default, parallel CPU shard plan',
      'project_id':m['project_id'],'phase':phase,'max_parallel':max_parallel,
      'frame_count':last-first,'shard_count':len(groups),'matrix':{'include':groups},
      'visual_review_required':True,'asset_approval_required_before_paid_jobs':True,
      'scene_manifest_sha256':info['storyboard_hash']}
def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=('validate','plan'))
    p.add_argument('--manifest',required=True)
    p.add_argument('--phase',choices=sorted(VALID_PHASES),default='first10')
    p.add_argument('--shard-seconds',type=int,default=SHARD_DEFAULT)
    p.add_argument('--max-parallel',type=int,default=8)
    p.add_argument('--strict-assets',action='store_true')
    p.add_argument('--out',default='')
    a=p.parse_args()
    path,m=load(a.manifest)
    result=validate(m,a.strict_assets,a.phase) if a.command=='validate' else plan(m,a.phase,a.shard_seconds,a.max_parallel)
    payload=json.dumps(result,indent=2)
    if a.out:
        dest=pathlib.Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(payload+'\n')
    print(payload)
if __name__=='__main__':
    try:main()
    except Exception as e:print('HUNYUAN_V3_STORY_PLAN_FAILED:',str(e),file=sys.stderr);sys.exit(1)
