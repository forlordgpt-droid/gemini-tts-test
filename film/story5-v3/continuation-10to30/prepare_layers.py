#!/usr/bin/env python3
"""Required Pillow + OpenCV. One new approved story5 painting + three previously paid paintings -> 12 separate depth planes.
Distinct alpha foreground, actor/action middle and object-removed full repaired plate; QA required."""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageFilter,ImageDraw,ImageOps
cv2.setNumThreads(2)
ROOT=Path(__file__).resolve().parent
RAW=ROOT/'raw';OUT=ROOT/'assets';QA=ROOT/'qc'
for q in [OUT,QA]:q.mkdir(parents=True,exist_ok=True)
TGT=(1920,1080)
# Artwork composition controls: center of Emma and rough region (relative source pixels),
# calibrated against four prompts; do not infer Hunyuan is Emma.
PEOPLE=[
 (.62,.54,.45,.90),    # new EMPTY street + phone + subway arrival, Emma at right
 (.55,.55,.45,.85),    # stairs
 (.51,.53,.51,.86),    # locked gate
 (.77,.66,.41,.72)     # Emma looks into dark corridor
]
def polygon(shape,verts):
    mask=np.zeros(shape[:2],np.uint8)
    cv2.fillPoly(mask,[np.asarray(verts,np.int32)],255)
    return mask

def foreground_mask(shape,idx):
    h,w=shape[:2]
    def p(v):return [(round(x*w),round(y*h)) for x,y in v]
    m=np.zeros((h,w),np.uint8)
    if idx==0:
        # Street foreground fender, railing and near urban framing
        coords=[[(0,.36),(.09,.39),(.25,.57),(.29,.85),(.37,1),(0,1)],
                [(0,0),(.042,0),(.044,.51),(.012,.56),(0,.58)]]
    elif idx==1:
        # Near handrails frame the descending stairwell, mid-level cutout stays separate
        coords=[[(0,.30),(.12,.42),(.26,.59),(.38,.82),(.49,1),(0,1)],
                [(.87,0),(1,0),(1,1),(.96,1),(.94,.76),(.92,.33)]]
    elif idx==2:
        # Locked gate foreground: silhouetted side bars frame actor
        coords=[[(0,0),(.10,0),(.12,1),(0,1)],
                [(.91,0),(1,0),(1,1),(.92,1)],
                [(0,.90),(.18,.89),(.19,1),(0,1)]]
    else:
        # Hanging pipes and heavy dark mechanical arch at left/top
        coords=[[(0,0),(.34,0),(.37,.16),(.28,.26),(.18,.53),(0,.59)],
                [(0,.88),(.17,.87),(.19,1),(0,1)],
                [(.85,0),(1,0),(1,.13),(.91,.14)]]
    for verts in coords:m|=polygon(shape,p(verts))
    return m

def smart_actor_mask(src,scene):
    H,W=src.shape[:2];s=.5
    h,w=H//2,W//2
    mini=cv2.resize(src,(w,h),interpolation=cv2.INTER_AREA)
    cx,cy,rw,rh=PEOPLE[scene]
    # Extract independent illustrator-drawn Emma layer with color-guided GC mask.
    # Model: background everywhere, inside actor bounding region probable foreground.
    x0=int(max(1,(cx-rw/2)*w));x1=int(min(w-1,(cx+rw/2)*w))
    y0=int(max(1,(cy-rh/2)*h));y1=int(min(h-1,(cy+rh/2)*h))
    m=np.full((h,w),cv2.GC_BGD,np.uint8)
    m[y0:y1,x0:x1]=cv2.GC_PR_BGD
    def ellipse(mx,my,rx,ry,status):
        cv2.ellipse(m,(int(mx*w),int(my*h)),(max(2,int(rx*w)),max(2,int(ry*h))),0,0,360,status,-1)
    # Generic human head, torso/jacket, hips and lower limbs;
    # probable rather than certain until red-corals supply exact seeds.
    if scene==3:
        ellipse(cx,.58,.11,.17,cv2.GC_PR_FGD)
        ellipse(cx,.79,.16,.18,cv2.GC_PR_FGD)
    else:
        ellipse(cx,cy-.19,.08,.105,cv2.GC_PR_FGD)
        ellipse(cx,cy+.025,.11,.24,cv2.GC_PR_FGD)
        ellipse(cx-.05,cy+.25,.06,.19,cv2.GC_PR_FGD)
        ellipse(cx+.065,cy+.24,.06,.21,cv2.GC_PR_FGD)
    hsv=cv2.cvtColor(mini,cv2.COLOR_BGR2HSV)
    # Salmon/coral rust jacket color; select local high-saturation orange-red segments.
    hch=hsv[:,:,0];sat=hsv[:,:,1];val=hsv[:,:,2]
    jacket=(((hch<25)|(hch>174)) & (sat>68) & (val>48)).astype(np.uint8)
    roi=np.zeros((h,w),np.uint8);roi[y0:y1,x0:x1]=1
    jacket*=roi
    nk,labels,stats,cent=cv2.connectedComponentsWithStats(jacket,8)
    candidates=[]
    for j in range(1,nk):
        a=int(stats[j,4])
        if a<8:continue
        xx,yy=cent[j];cx0,cy0=PEOPLE[scene][:2]
        d=((xx/w-cx0)**2+(yy/h-cy0)**2)**.5
        candidates.append((a/(.20+d),j))
    if candidates:
        _,j=max(candidates)
        sure=(labels==j).astype(np.uint8)
        sure=cv2.erode(sure,np.ones((3,3),np.uint8),iterations=1)
        if sure.sum()>5:m[sure>0]=cv2.GC_FGD
    # Conservative fallback seed well within intended Emma's jacket near shot center.
    if not np.any(m==cv2.GC_FGD):
        mx,my=(cx, min(.88,cy+.07))
        cv2.circle(m,(int(mx*w),int(my*h)),4,cv2.GC_FGD,-1)
    bg=np.zeros((1,65),np.float64);fg=np.zeros((1,65),np.float64)
    cv2.grabCut(mini,m,None,bg,fg,3,cv2.GC_INIT_WITH_MASK)
    result=np.where((m==cv2.GC_FGD)|(m==cv2.GC_PR_FGD),255,0).astype('uint8')
    result=cv2.resize(result,(W,H),interpolation=cv2.INTER_LINEAR)
    result=cv2.morphologyEx(result,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    return result

def rgba(img,mask):
    a=Image.fromarray(mask).filter(ImageFilter.GaussianBlur(radius=1.25))
    x=Image.fromarray(cv2.cvtColor(img,cv2.COLOR_BGR2RGBA));x.putalpha(a);return x

qa=[]
for scene in range(4):
    f=RAW/('raw_'+str(scene)+'.png')
    if not f.exists():raise FileNotFoundError('Required approved SnapGen frame missing: '+str(f))
    src=cv2.imread(str(f))
    if src is None:raise ValueError('Invalid original png: '+str(f))
    h,w=src.shape[:2]
    assert abs(w/h-16/9)<.025,(scene,w,h)
    near=foreground_mask(src.shape,scene)
    actor=smart_actor_mask(src,scene)
    actor[near>0]=0
    assert actor.sum()>h*w*255*.002,(scene,'actor segmentation empty')
    assert near.sum()>h*w*255*.006,(scene,'foreground segmentation empty')
    # Original image objects removed from rear plate by OpenCV Telea.
    # Limit mask dilation to retain painterly background context and avoid holes at plane overlap.
    removed=cv2.dilate(cv2.bitwise_or(actor,near),np.ones((5,5),np.uint8),iterations=2)
    background=cv2.inpaint(src,removed,6,cv2.INPAINT_TELEA)
    far=Image.fromarray(cv2.cvtColor(background,cv2.COLOR_BGR2RGB))
    far=far.resize(TGT,Image.Resampling.LANCZOS)
    middle=rgba(src,actor).resize(TGT,Image.Resampling.LANCZOS)
    front=rgba(src,near).resize(TGT,Image.Resampling.LANCZOS)
    far.save(OUT/('far_'+str(scene)+'.jpg'),quality=94,subsampling=0)
    middle.save(OUT/('mid_'+str(scene)+'.png'),compress_level=4)
    front.save(OUT/('front_'+str(scene)+'.png'),compress_level=4)
    sheet=Image.new('RGB',(1280,740),'#0d1528')
    original=Image.fromarray(cv2.cvtColor(src,cv2.COLOR_BGR2RGB)).resize((640,360))
    sheet.paste(original,(0,24));sheet.paste(far.resize((640,360)),(640,24))
    for ind,mask in enumerate((actor,near)):
        prev=Image.fromarray(mask).resize((640,360))
        sheet.paste(Image.merge('RGB',(prev,prev,prev)),(ind*640,390))
    d=ImageDraw.Draw(sheet)
    d.text((10,5),'SHOT '+str(scene)+' / ORIGINAL APPROVED 2D PAINTING',fill='white')
    d.text((651,5),'BACKPLATE WITH REPAIRED OBJECT HOLES',fill='white')
    d.text((10,400),'ACTOR / ACTION MIDDLE DEPTH ALPHA',fill='#ffdfa5')
    d.text((651,400),'NEAR PROP FOREGROUND ALPHA',fill='#ffdfa5')
    sheet.save(QA/('LAYER_QA_'+str(scene)+'.jpg'),quality=90)
    qa.append({'scene':scene,'width':w,'height':h,
               'middle_fraction':round(float((actor>0).mean()),4),
               'foreground_fraction':round(float((near>0).mean()),4),
               'inpaint_fraction':round(float((removed>0).mean()),4)})
(QA/'LAYER_QA.json').write_text(json.dumps({'layers_per_scene':3,
 'processor':'Pillow+OpenCV grabCut/Telea inpaint',
 'model':'gpt-image-2.5-lower', 'approved_additional_images':1, 'scenes':qa},indent=2))
print('PASS one new story5 image and three previously generated images yield twelve 1080p depth planes')
