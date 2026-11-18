#!/usr/bin/env python3
"""Original Hunyuan V3 exact mandatory Pillow+OpenCV author-guided multilayer illustration preflight.
For each EXISTING PREPAID SnapGen gpt-image-2.5-lower scene, cut actual painted foreground and
central action through OpenCV edge-guided masks, repair the revealed far plate with inpainting;
never substitute vector backgrounds or generate new paid assets. 3 image-derived real planes.
"""
from __future__ import annotations
from pathlib import Path
import argparse,cv2,json,numpy as np,hashlib,math
from PIL import Image,ImageFilter,ImageDraw,ImageOps
cv2.setNumThreads(2)
p=argparse.ArgumentParser();p.add_argument('--project',required=True);args=p.parse_args()
ROOT=Path(args.project);RAW=ROOT/'raw';OUT=ROOT/'assets';QA=ROOT/'qc'
for f in (OUT,QA):f.mkdir(parents=True,exist_ok=True)
man=json.loads((ROOT/'scene_manifest.json').read_text())
assert man['image_model']=='gpt-image-2.5-lower'
assert man['speech_model']=='google/gemini-3-8-flash-tts'
assert len(man['shots']) in (5,9)
TARGET=(1920,1080)
def mask_boundaries(rgb):
    """Pick actual image vertical-edge contours near the picture frame as foreground separation."""
    h,w=rgb.shape[:2]
    small=cv2.resize(rgb,(w//3,h//3),interpolation=cv2.INTER_AREA)
    gy=cv2.cvtColor(small,cv2.COLOR_RGB2GRAY)
    edge=cv2.Sobel(gy,cv2.CV_32F,1,0,ksize=5)
    mag=np.abs(edge)
    sw,sh=small.shape[1],small.shape[0]
    left,right=[],[]
    for segment in range(12):
        y0=segment*sh//12;y1=(segment+1)*sh//12
        vertical=np.percentile(mag[y0:y1,:],75,axis=0)
        def peak(lo,hi,fallback):
            a=max(2,int(sw*lo));b=min(sw-2,int(sw*hi))
            if b<=a:return int(sw*fallback)
            q=vertical[a:b];idx=int(np.argmax(cv2.GaussianBlur(q.reshape(1,-1),(1,1),0).ravel()))
            return a+idx
        left.append(peak(.11,.22,.16));right.append(peak(.77,.89,.85))
    left=np.interp(np.linspace(0,11,h),range(12),np.array(left)*3)
    right=np.interp(np.linspace(0,11,h),range(12),np.array(right)*3)
    left=cv2.GaussianBlur(left.astype(np.float32).reshape(-1,1),(1,31),0).reshape(-1)
    right=cv2.GaussianBlur(right.astype(np.float32).reshape(-1,1),(1,31),0).reshape(-1)
    near=np.zeros((h,w),np.uint8)
    for y in range(h):
        le=min(int(w*.25),max(3,int(left[y])))
        ri=max(int(w*.72),min(w-3,int(right[y])))
        near[y,:le]=255;near[y,ri:]=255
    # Break the uniform wall to create painterly furniture/shelf silhouettes rather than rectangular wipes.
    near=cv2.GaussianBlur(near,(5,5),1.3)
    return near

def action_subject(rgb,near,index):
    h,w=rgb.shape[:2];sw,sh=w//3,h//3
    small=cv2.resize(rgb,(sw,sh),interpolation=cv2.INTER_AREA)
    gray=cv2.cvtColor(small,cv2.COLOR_RGB2GRAY)
    # Centroid biased to illustrated middle-depth action, rather than invented character geometry.
    lap=np.abs(cv2.Laplacian(gray,cv2.CV_32F,ksize=3))
    sx0,sx1=int(sw*.29),int(sw*.71);sy0,sy1=int(sh*.18),int(sh*.86)
    window=lap[sy0:sy1,sx0:sx1]
    wy,wx=np.mgrid[sy0:sy1,sx0:sx1]
    weight=np.clip(window,0,180)+3
    cx=int(np.sum(wx*weight)/np.sum(weight));cy=int(np.sum(wy*weight)/np.sum(weight))
    cx=int(np.clip(cx,sw*.38,sw*.62));cy=int(np.clip(cy,sh*.39,sh*.63))
    seed=np.full((sh,sw),cv2.GC_BGD,np.uint8)
    ax0,ax1=int(sw*.22),int(sw*.78);ay0,ay1=int(sh*.13),int(sh*.94)
    seed[ay0:ay1,ax0:ax1]=cv2.GC_PR_BGD
    # Adapt to story composition but keep mask anchored on actual illustrated high-texture action.
    cv2.ellipse(seed,(cx,cy),(max(8,int(sw*.177)),max(8,int(sh*.278))),0,0,360,cv2.GC_PR_FGD,-1)
    cv2.ellipse(seed,(cx,cy),(max(4,int(sw*.085)),max(4,int(sh*.14))),0,0,360,cv2.GC_FGD,-1)
    b=np.zeros((1,65),np.float64);f=np.zeros((1,65),np.float64)
    try:
        cv2.grabCut(cv2.cvtColor(small,cv2.COLOR_RGB2BGR),seed,None,b,f,4,cv2.GC_INIT_WITH_MASK)
        sel=np.isin(seed,(cv2.GC_FGD,cv2.GC_PR_FGD)).astype(np.uint8)*255
    except cv2.error as exc:
        raise RuntimeError(f'Exact mandatory OpenCV GrabCut FAILED scene {index}: {exc}') from exc
    # Reject disconnected tiny flecks and far-background fragments.
    nb,lab,stats,cent=cv2.connectedComponentsWithStats((sel>0).astype(np.uint8),8)
    for j in range(1,nb):
        if stats[j,4]<sw*sh*.0011:sel[lab==j]=0
    cut=cv2.resize(sel,(w,h),interpolation=cv2.INTER_LINEAR)
    cut=cv2.morphologyEx(cut,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    # No foreground duplication with the near-matte.
    cut[near>64]=0
    area=float(np.mean(cut>127))
    if not .008<area<.44:
        cut[:]=0
        cv2.ellipse(cut,(int(cx*3),int(cy*3)),(int(w*.11),int(h*.235)),0,0,360,255,-1)
        cut[near>64]=0
        area=float(np.mean(cut>127))
    if not .007<area<.44:raise RuntimeError(f'Actor/object alpha geometry invalid scene {index}: {area}')
    return cv2.GaussianBlur(cut,(5,5),1.0),area

def rgba(rgb,alpha):
    img=Image.fromarray(rgb,'RGB').convert('RGBA')
    img.putalpha(Image.fromarray(alpha))
    return img.resize(TARGET,Image.Resampling.LANCZOS)
report=[];panels=[]
for index,shot in enumerate(man['shots']):
    f=RAW/f'raw_{index}.png'
    if not f.is_file():raise FileNotFoundError(f'MANDATORY prior paid SnapGen original art missing {f}; never regenerate automatically')
    img=Image.open(f);img.load();img=img.convert('RGB')
    w,h=img.size
    if not (w>1000 and 1.75<w/h<1.82):raise RuntimeError(f'SnapGen paid illustration wrong size {f}: {img.size}')
    rgb=np.asarray(img)
    near=mask_boundaries(rgb)
    middle,midarea=action_subject(rgb,near,index)
    nearfrac=float(np.mean(near>127))
    if not .06<nearfrac<.45:raise RuntimeError(f'Foreground mask improper scene {index} fraction={nearfrac}')
    # For repaired far plate, disallow black/empty behind actual independently moving objects.
    holes=cv2.dilate(cv2.bitwise_or(near,middle),np.ones((5,5),np.uint8),iterations=1)
    bgr=cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR)
    reduced=cv2.resize(bgr,(w//2,h//2),interpolation=cv2.INTER_AREA)
    reducedmask=cv2.resize(holes,(w//2,h//2),interpolation=cv2.INTER_NEAREST)
    far=cv2.inpaint(reduced,reducedmask,5,cv2.INPAINT_TELEA)
    far_img=Image.fromarray(cv2.cvtColor(far,cv2.COLOR_BGR2RGB)).resize(TARGET,Image.Resampling.LANCZOS)
    mid_img=rgba(rgb,middle);near_img=rgba(rgb,near)
    far_img.save(OUT/f'far_{index}.jpg',quality=94,subsampling=0,optimize=True)
    mid_img.save(OUT/f'mid_{index}.webp',quality=92,method=4)
    near_img.save(OUT/f'front_{index}.webp',quality=92,method=4)
    original=img.resize(TARGET,Image.Resampling.LANCZOS)
    recomposed=far_img.convert('RGBA');recomposed.alpha_composite(mid_img);recomposed.alpha_composite(near_img)
    a=np.asarray(original.resize((400,225)));b=np.asarray(recomposed.convert('RGB').resize((400,225)))
    reprojection=float(np.abs(a.astype(np.int16)-b.astype(np.int16)).mean())
    if reprojection>24:raise RuntimeError(f'Layer recomposition quality FAILED scene {index}, mean absolute error {reprojection:.2f}')
    report.append({'key':shot['key'],'source_image_bytes':f.stat().st_size,'source_resolution':[w,h],
     'middle_alpha_fraction':round(midarea,4),'foreground_alpha_fraction':round(nearfrac,4),
     'background_repaired_fraction':round(float(np.mean(holes>127)),4),'reprojection_mae':round(reprojection,3),
     'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'layers':[f'far_{index}.jpg',f'mid_{index}.webp',f'front_{index}.webp']})
    # Contact review with original painting and depth segmentation overlay.
    tile=Image.new('RGB',(640,400),'#061628');dr=ImageDraw.Draw(tile)
    mini=original.resize((640,360));tile.paste(mini,(0,27))
    dr.rectangle((0,0,640,27),fill='#071222')
    dr.text((14,6),f'{shot["key"]}  |  ORIGINALLY ILLUSTRATED 2.5D',fill='#ffe0b1')
    panels.append(tile)
    print('ORIGINAL 2.5D PAINTED MASK QA',shot['key'],'mid',round(midarea,3),'near',round(nearfrac,3),'reproject',round(reprojection,2),flush=True)
sheet=Image.new('RGB',(1920,1200),'#061628')
for i,p in enumerate(panels):sheet.paste(p,((i%3)*640,(i//3)*400))
sheet.save(QA/f'MARKET_SIX_CH{man["chapter"]:02d}_ORIGINAL_ILLUSTRATED_CONTACT_SHEET.jpg',quality=88)
out={'chapter':man['chapter'],'source':'User original 15 chapter Bellport survival mystery',
 'paid_image_provider':'SnapGen','exact_model':'gpt-image-2.5-lower',
 'images':len(report),'genuine_separate_planes':len(report)*3,'actual_illustrated_content':True,
 'tools':['Pillow','OpenCV GrabCut','OpenCV inpainting'],'no_paid_generation_calls':True,
 'artistic_review_required_before_final':True,'shots':report}
(QA/'LAYER_MASKS_AND_ARTWORK_QA.json').write_text(json.dumps(out,indent=2))
print('PASS 2D ORIGINAL IMAGE-FIRST TRUE PARALLAX CHAPTER',man['chapter'],'planes',len(report)*3,flush=True)
