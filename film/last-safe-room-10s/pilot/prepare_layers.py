#!/usr/bin/env python3
"""Pillow + OpenCV guided, alpha-correct depth extraction. Exact tool stack, zero paid calls."""
import json
from pathlib import Path
import numpy as np
import cv2
cv2.setNumThreads(2)
from PIL import Image,ImageFilter,ImageDraw
ROOT=Path(__file__).resolve().parent
RAW=ROOT/'raw';OUT=ROOT/'assets';QA=ROOT/'qc'
OUT.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
TARGET=(1920,1080)

def polygon(shape,verts):
    mask=np.zeros(shape[:2],np.uint8)
    cv2.fillPoly(mask,[np.asarray(verts,np.int32)],255)
    return mask

def person_segment(original,scene):
    oh,ow=original.shape[:2]
    im=cv2.resize(original,(ow//2,oh//2),interpolation=cv2.INTER_AREA)
    h,w=im.shape[:2];hint=np.full((h,w),cv2.GC_BGD,np.uint8)
    if scene==0:
        rect=(415,335,625,740)
        probs=[[(476,440),(512,370),(581,360),(595,410),(579,490),(561,550),(563,650),(533,729),(484,726),(472,623),(439,490)]]
        sure=[(522,454,20),(522,520,15),(513,610,11),(550,394,9)]
    elif scene==1:
        rect=(630,120,1080,875)
        probs=[[(824,158),(920,130),(1018,155),(1047,226),(1029,360),(996,430),(965,485),(1000,654),(1072,818),(1020,853),(930,777),(876,647),(811,591),(708,715),(643,724),(658,665),(748,523),(771,416),(673,397),(646,351),(675,281),(754,230)]]
        sure=[(901,321,35),(889,400,19),(839,530,25),(953,704,21),(989,204,13)]
    else:
        rect=(0,0,1075,941)
        probs=[[(178,313),(306,174),(403,165),(510,70),(758,0),(908,0),(978,120),(990,310),(933,434),(922,600),(1000,851),(1039,941),(0,941),(100,724)]]
        sure=[(612,170,58),(653,330,45),(438,610,50),(743,630,46),(878,463,18)]
    x0,y0,x1,y1=(int(v*.5) for v in rect)
    hint[y0:y1,x0:x1]=cv2.GC_PR_BGD
    for verts in probs:
        pts=np.array([(int(x*.5),int(y*.5)) for x,y in verts],np.int32)
        cv2.fillPoly(hint,[pts],cv2.GC_PR_FGD)
    for x,y,r in sure:cv2.circle(hint,(int(x*.5),int(y*.5)),max(2,int(r*.5)),cv2.GC_FGD,-1)
    bgd=np.zeros((1,65),np.float64);fgd=np.zeros((1,65),np.float64)
    cv2.grabCut(im,hint,None,bgd,fgd,3,cv2.GC_INIT_WITH_MASK)
    alpha=np.where((hint==cv2.GC_FGD)|(hint==cv2.GC_PR_FGD),255,0).astype('uint8')
    alpha=cv2.resize(alpha,(ow,oh),interpolation=cv2.INTER_NEAREST)
    return cv2.morphologyEx(alpha,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))

def front_mask(scene,shape):
    m=np.zeros(shape[:2],np.uint8)
    if scene==0:
        m|=polygon(shape,[(0,402),(110,434),(303,504),(410,578),(467,698),(501,790),(760,814),(825,941),(0,941)])
    elif scene==1:
        m|=polygon(shape,[(0,355),(115,416),(280,560),(350,701),(490,810),(560,941),(0,941)])
        m|=polygon(shape,[(0,0),(77,0),(74,97),(51,327),(0,367)])
        m|=polygon(shape,[(113,55),(240,77),(385,154),(371,248),(91,157)])
        m|=polygon(shape,[(30,33),(371,20),(369,55),(20,78)])
    else:
        m|=polygon(shape,[(1184,475),(1376,498),(1475,537),(1450,733),(1408,941),(970,941),(867,879),(940,770),(1055,690),(1138,490)])
    return m

def rgba(image,mask,blur=1.35):
    alpha=Image.fromarray(mask).filter(ImageFilter.GaussianBlur(radius=blur))
    out=Image.fromarray(cv2.cvtColor(image,cv2.COLOR_BGR2RGBA));out.putalpha(alpha)
    return out

metadata=[];previews=[]
for i in range(3):
    p=RAW/('raw_'+str(i)+'.png')
    if not p.exists():raise FileNotFoundError('Approved GPT Image 2.5 Lower image missing: '+str(p))
    original=cv2.imread(str(p))
    if original is None:raise RuntimeError('Invalid original approved illustration')
    h,w=original.shape[:2]
    assert abs(w/h-16/9)<.02, (w,h)
    mid=person_segment(original,i);front=front_mask(i,original.shape)
    mid[front>0]=0
    mid=cv2.morphologyEx(mid,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    for mask in (mid,front):
        assert mask.any(),('Empty independent parallax plane',i)
    cutout=cv2.dilate(cv2.bitwise_or(mid,front),np.ones((5,5),np.uint8),iterations=2)
    far=cv2.inpaint(original,cutout,7,cv2.INPAINT_TELEA)
    farP=Image.fromarray(cv2.cvtColor(far,cv2.COLOR_BGR2RGB)).resize(TARGET,Image.Resampling.LANCZOS)
    midP=rgba(original,mid).resize(TARGET,Image.Resampling.LANCZOS)
    frontP=rgba(original,front).resize(TARGET,Image.Resampling.LANCZOS)
    farP.save(OUT/('far_'+str(i)+'.jpg'),quality=93,subsampling=0)
    midP.save(OUT/('mid_'+str(i)+'.png'),compress_level=4)
    frontP.save(OUT/('front_'+str(i)+'.png'),compress_level=4)
    sheet=Image.new('RGB',(1280,720),'#101b2c')
    shot=Image.fromarray(cv2.cvtColor(original,cv2.COLOR_BGR2RGB)).resize((640,360))
    sheet.paste(shot,(0,0));sheet.paste(farP.resize((640,360)),(640,0))
    for idx,mask in enumerate((mid,front)):
        small=Image.fromarray(mask).resize((640,360))
        sheet.paste(Image.merge('RGB',(small,small,small)),(640*idx,360))
    d=ImageDraw.Draw(sheet)
    d.text((16,14),'ORIGINAL ART / SHOT '+str(i+1),fill='white')
    d.text((655,14),'REPAIRED BACKGROUND PLATE',fill='white')
    d.text((16,378),'ACTOR MIDDLE ALPHA',fill='#f5d9ae')
    d.text((655,378),'FOREGROUND ALPHA',fill='#f5d9ae')
    sheet.save(QA/('SEGMENTATION_REVIEW_'+str(i)+'.jpg'),quality=91)
    metadata.append({'shot':i,'source_pixels':[w,h],'output_pixels':[1920,1080],'middle_area':float(np.mean(mid>0)),'front_area':float(np.mean(front>0)),'inpaint_area':float(np.mean(cutout>0))})
(QA/'LAYER_PREPARATION.json').write_text(json.dumps({'processor':'Pillow + OpenCV GrabCut+inpaint','independent_illustrated_planes_per_shot':3,'shot_qa':metadata},indent=2))
print('PASS all nine independently layered images extracted from precisely three approved sources')
