#!/usr/bin/env python3
"""Source-locked preproduction and Kie Gemini TTS. ChatGPT exclusively generates images.
No secrets are logged or persisted. Fail closed rather than substitute fake assets.
"""
import argparse, concurrent.futures, hashlib, json, os, pathlib, re, time, urllib.parse, urllib.request, urllib.error, wave
from datetime import datetime, timezone

ROOT=pathlib.Path(__file__).resolve().parent
STORY=json.loads((ROOT/"story.json").read_text(encoding="utf-8"))
OUT=pathlib.Path("output")
MODEL_IMAGE="CHATGPT_IMAGE_GENERATION_ONLY"
MODEL_TTS="google/gemini-3-8-flash-lite-tts"
STYLE=("Photorealistic premium American psychological thriller; meticulous 35mm anamorphic film cinematography, "
       "deep cobalt shadows against subtle tungsten and crimson practicals, rain-reflected Manhattan city lights, "
       "believable natural skin pores, lifelike hand anatomy, nuanced restrained acting, filmic highlight roll-off, "
       "subtle tasteful grain, true photographic lens depth, rich shadow detail, elegant art direction, "
       "no illustration, no CGI appearance, no plastic skin, no artificial image sharpening. ")
NO_LABEL="No text, no labels, no logos, no watermarks, no collage."
SHOTS=[]
for sn in range(1,5):
    scene=str(sn)
    d=STORY["dialogue"][scene]
    actions=STORY["actions"][scene]
    j=0
    for i in range(len(d)+1):
        for a in [a for a in actions if a[0]==i]:
            j+=1
            after, kind, visual, subjects, motion, effect, requested=a
            sid=f"S{sn}_{j:02d}"
            SHOTS.append(dict(id=sid,scene=sn,scene_title=STORY["scene_titles"][sn-1],
                         source_order=i,kind="ACTION",shot=kind,visual=visual,subjects=subjects,
                         camera=motion,effect=effect,preferred_hold=float(requested),
                         speaker="-",spoken_text="",delivery="-"))
        if i<len(d):
            j+=1
            speaker,line,kind,subjects,emotion,motion=d[i]
            sid=f"S{sn}_{j:02d}"
            SHOTS.append(dict(id=sid,scene=sn,scene_title=STORY["scene_titles"][sn-1],
                         source_order=i+1,kind="DIALOGUE",shot=kind,visual=emotion,subjects=subjects,
                         camera=motion,effect="none",preferred_hold=0,
                         speaker=speaker,spoken_text=line,delivery=emotion))
for s in SHOTS:
    s["on_screen"]=[x.strip() for x in s["subjects"].split(",") if x.strip() in STORY["characters"]]
    is_recorded=s["speaker"].startswith("RECORDED") or s["effect"]=="recorded_restaurant"
    loc="restaurant" if is_recorded else ("suite" if s["scene"]==1 else ("elevator" if s["scene"]==2 and s["source_order"]<=6 and s["effect"] not in ("exit_elevator","bag_clue","door_swing","jenna_exit","ethan_exit","four_freeze") else "corridor"))
    if s["scene"]==4 and s["effect"] in ("tv_turn_on","recording_freeze","next_file_title","remote_reach","remote_play"):
        loc="suite"
    s["location"]=loc
    ppl=s["on_screen"]; shot=s["shot"]
    if len(ppl)==1:
        prefix=("SINGLE-PERSON CLEAN FRAME. Exactly one human is visible anywhere in the image: "+ppl[0]+
                ". Empty foreground. No other human body, face, head, hair, shoulder, arm, hand, silhouette, reflection, shadow-person, blurred person, or background person may appear. This is NOT an over-the-shoulder shot and NOT a two-shot. ")
        if shot=="OTS":
            prefix="" # OTS requires a human foreground anchor
    else: prefix=""
    if shot=="CU" or (shot=="REACTION" and len(ppl)==1):
        framing="Tight photographic head-and-shoulders close-up, subject face occupies 60-70 percent of frame height, softly blurred background. "
    elif shot=="MEDIUM":
        framing="Intimate medium cinematic framing, featured human fills much of frame, readable eyes and upper torso. "
    elif shot=="OTS":
        framing="True over-the-shoulder frame, foreground shoulder and back-of-head softly blurred on near edge, focused dominant character beyond. "
    elif shot=="REACTION":
        framing="Listener/observer-dominant close cinematic reaction, readable expression at thumbnail size. "
    elif shot=="INSERT":
        framing="Extreme detailed photographic insert, tangible prop or proof entirely dominates frame, controlled negative space. "
    elif shot=="WIDE":
        framing="Intentional luxurious wide master, hotel geography clearly readable, cinematic perspective and balanced negative space. "
    elif shot=="DOORWAY":
        framing="Architectural cinematic doorway/entrance composition, threshold unmistakable, beautiful depth and authentic material surfaces. "
    else:
        framing="Expressive close two-person composition, clear spatial relationships and motivated eyelines. "
    names=" ".join(
        f"{x}: {STORY['characters'][x]['identity']}; "
        f"{STORY['characters'][x]['close'] if shot in ('CU','REACTION','OTS') else STORY['characters'][x]['wide']}. "
        for x in ppl)
    if shot=="OTS" and len(ppl)==1:
        other= "JENNA" if s["scene"]==1 else ("CHLOE" if s["scene"]==2 else ("JENNA" if s["scene"]==3 else "JENNA"))
        names+=f"Only the soft foreground shoulder/edge of {other} is also visible, not their face. "
    if len(ppl)==1 and shot!="OTS":
        exclusions="Only "+ppl[0]+" may be visible, no competing foreground person or second face. "
    elif not ppl:
        exclusions="No human faces or silhouettes; do not show extra people. "
    else: exclusions="No extra humans beyond specified subjects. "
    loc_text=STORY["locations"][loc] if shot in ("WIDE","MEDIUM","DOORWAY","TWO-SHOT") else f"same {loc} location, intentionally softly out of focus"
    dominant=(ppl[0] if len(ppl)==1 else (s["subjects"] if ppl else "the named hero prop or architectural clue"))
    s["image_prompt"]=prefix+STYLE+framing+f"Dominant subject: {dominant}. "+s["visual"]+". "+names+f"Location continuity: {loc_text}. "+exclusions+NO_LABEL
    ref=[]
    for x in ppl[:3]:
        ref.append("CHAR_"+x)
    if not ppl:
        p={"ring_drop":"ring","phone_wake":"phone","decline":"phone","mystery_message":"phone","bag_clue":"handbag","identical_text":"phone","four_beeps":"phone","door_swing":"door","door_click":"door","remote_reach":"remote","remote_play":"remote"}.get(s["effect"])
        if p:ref.append("PROP_"+p.upper())
    if len(ref)<4:ref.append("LOC_"+loc.upper())
    if len(ref)>4:ref=ref[:4]
    s["references_used"]=ref
    s["asset_id"]=f"PLATE_{s['id']}"
    s["camera_axis"]="Corridor axis locked: Brian/Chloe screen-left; Jenna/Ethan screen-right" if loc=="corridor" else "Source scene consistent"
    s["eyeline"]="Toward partner across locked axis" if ppl else "not applicable"
    s["screen_position"]="Dominant subject central or rule-of-thirds, clean negative space"
    s["shot_purpose"]="Visually clarify "+s["effect"] if s["kind"]=="ACTION" else "Deliver exact dialogue with clear emotional stakes"
    s["reaction_target"]=s["subjects"] if s["shot"]=="REACTION" else "none"
    s["next_shot_reason"]="Natural story beat change"
    s["initial_state"]="Before "+s["effect"] if s["effect"]!="none" else "static plate"
    s["final_state"]="After "+s["effect"] if s["effect"]!="none" else "static plate"
    s["fixed_elements"]="Room architecture, character identity, face and light direction"
    s["occlusion_rule"]="Moving overlay must not expose nonexistent backdrop; test composition in export"
    s["counts_toward_minimum"]=s["effect"] in {"ring_drop","phone_wake","door_swing","four_beeps","tv_turn_on","remote_play"}
    s["verification_evidence"]=None
    s["provisional_start_s"]=round(sum(x.get("preferred_hold",2.5) if x["kind"]=="ACTION" else 2.5 for x in SHOTS if x["scene"]==s["scene"] and x["id"]<s["id"]),2)

def save_json(name,data):
    p=OUT/name; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

def preflight():
    OUT.mkdir(exist_ok=True)
    settings=dict(PROJECT_MODE="REALISTIC_DRAMA",ASPECT_RATIO="16:9",TARGET_RESOLUTION="1920x1080",
       TARGET_FPS=30,SETTING_AND_ACCENT="Manhattan, New York City; American English",
       SCRIPT_LOCK="Source screenplay dialogue exact, no new story material",
       IMAGE_ENGINE="ChatGPT native image generation ONLY; assets must be imported as real PNGs",TTS_ENGINE=MODEL_TTS,ANIMATION_ENGINE="Pillow/OpenCV-free 2.5D compositing",
       RENDER_ENGINE="Python/Pillow/NumPy + FFmpeg x264 CPU",
       MAX_REFERENCES_PER_SHOT=4,CHARACTER_ANIMATION="NONE",OBJECT_ANIMATION="STORY_MOTIVATED",
       ENVIRONMENT_MODE="LAYERED_2_5D",DELIVERY_MODE="rendered movie",DURATION_TARGET_SECONDS=180,
       SOURCE_HASH=hashlib.sha256((ROOT/"story.json").read_bytes()).hexdigest(),
       GITHUB_CPU="GitHub-hosted public-repository ubuntu-latest matrix, CPU only")
    save_json("PROJECT_SETTINGS.json",settings)
    save_json("SHOT_MANIFEST_V9.json",SHOTS)
    effect_rows=[]
    for s in SHOTS:
        if s["effect"] not in ("none","opening_establish","approach","pull_away","exit_elevator","bag_clue","jenna_exit","ethan_exit","four_freeze","ethan_stare","jenna_step_away","after_shout","chloe_wipe","eight_months_reaction","bitter_aftermath","recorded_restaurant","recording_freeze","remote_reach","everyone_turns","end_card"):
            effect_rows.append(dict(EFFECT_ID="FX_"+s["id"],SHOT_ID=s["id"],OBJECT_ID=s["effect"],
                SOURCE_PLATE=s["asset_id"],MASK_OR_LAYER="Deterministic Pillow transparent RGBA overlay",
                BOUNDING_BOX="relative to 1920x1080 composition",ANCHOR="object origin or architectural hinge",
                DEPTH_ORDER="above clean plate; behind visible composited foreground when relevant",
                START_S="scene timeline resolved after measured TTS",END_S="scene timeline resolved after measured TTS",
                EASING="smoothstep",TRANSFORM_OR_EFFECT=s["effect"],TRIGGER_BEAT=s["visual"],
                AUDIO_CUE=s["effect"],RENDER_CHECK="sample first,mid,last frames",
                INITIAL_STATE=s["initial_state"],FINAL_STATE=s["final_state"],
                FIXED_ELEMENTS=s["fixed_elements"],OCCLUSION_RULE=s["occlusion_rule"],
                COUNTS_TOWARD_MINIMUM=s["counts_toward_minimum"],VERIFICATION_EVIDENCE=None))
    save_json("OBJECT_EFFECTS_MANIFEST.json",effect_rows)
    save_json("CAMERA_TIMELINE.json",[
        dict(SHOT_ID=s["id"],MOTION=s["camera"],DURATION_S="measured during render",
             FOCAL_TARGET=s["subjects"],START_TRANSFORM={"scale":1.045 if s["camera"]!="HOLD" else 1.0,"x":0,"y":0},
             END_TRANSFORM={"scale":1.085 if s["camera"]=="SLOW_PUSH" else 1.0,"x":-0.015 if s["camera"]=="SLOW_PAN" else 0,"y":0},
             EASING="smoothstep",SAFE_CROP=">=6% overscan on moving shots") for s in SHOTS])
    bible=["# Character, Location, Prop, Style and Voice Bible","",STYLE,""]
    for name,c in STORY["characters"].items():
        bible += [f"## CHARACTER: {name}",f"ID: {name}",f"LOOK: {c['identity']} | {c['wide']}",
                 f"VOICE_ID: {c['voice']}",f"VOICE_PROFILE: {c['vocal']}",
                 "REF_SHEET_PROMPT: Photorealistic studio identity image containing exactly three views of the same "+
                 name+" character in one image on solid pure-white background, left: head-only front close-up, "+
                 "center: full-body standing front, right: full-body standing back; same exact face, hair identity, "+
                 "skin tone, body proportions and wardrobe across all three views. "+c["identity"]+". "+
                 c["wide"]+". Clean even studio lighting. Three views separated by natural white space, "+
                 "no overlap, no extra poses, no fourth figure, no text, no labels, no logos, no watermarks, "+
                 "no decorative borders, no mood-board elements.",""]
    for name,descr in STORY["locations"].items():
        bible += [f"LOCATION: {name}",f"LOOK: {descr}",
                  f"REF_SHEET_PROMPT: Single clean empty location photograph, {descr}. No humans. {NO_LABEL}",""]
    for name,descr in STORY["props"].items():
        bible += [f"PROP: {name}",f"LOOK: {descr}",f"REF_SHEET_PROMPT: Single high-end product shot of {descr}. {NO_LABEL}",""]
    (OUT/"CHARACTER_LOCATION_PROP_BIBLE.md").write_text("\n".join(bible),encoding="utf-8")
    production=["=== REFERENCE BIBLE ==="]
    for name,c in STORY["characters"].items():
        production += [f"CHARACTER: {name}",f"ID: {name}",f"LOOK: {c['identity']}",f"STATES: single wardrobe lock",
                       f"REF_SHEET_PROMPT: three-view identity sheet as written in CHARACTER_LOCATION_PROP_BIBLE.md"]
    for name,loc in STORY["locations"].items(): production += [f"LOCATION: {name}",f"ID: LOC_{name.upper()}",f"LOOK: {loc}",f"REF_SHEET_PROMPT: clean empty location shot"]
    for name,prop in STORY["props"].items(): production += [f"PROP: {name}",f"ID: PROP_{name.upper()}",f"LOOK: {prop}",f"REF_SHEET_PROMPT: isolated clean hero prop"]
    production += ["=== VOICE BIBLE ==="]
    for name,c in STORY["characters"].items():production += [f"ID: {name}",f"VOICE_ID: {c['voice']}",f"VOICE_PROFILE: {c['vocal']}"]
    production+=["=== STYLE PREFIX ===",STYLE]
    for s in SHOTS:
        production+=[f"=== SCENE {s['scene']} ===" if s==next(x for x in SHOTS if x['scene']==s['scene']) else "",
                     f"=== IMAGE {s['scene']}.{s['id'].split('_')[1]} ===",
                     f"SCENE: {s['scene']}",f"COVERS: {s['scene_title']} | beat {s['source_order']}",
                     f"TRACK: {s['kind']}",f"SHOT: {s['shot']}",f"CAMERA_ANGLE: {s['camera_axis']}",
                     f"ON_SCREEN: {','.join(s['on_screen']) or '-'}",f"REFS: {','.join(s['references_used'])}",
                     f"FOCUS: {s['subjects']}",f"IMAGE_PROMPT: {s['image_prompt']}",
                     f"LINE {s['source_order']}: {s['speaker']} | {s['spoken_text']}" if s['kind']=="DIALOGUE" else "",
                     f"NARRATION_VO: -",f"SPEAKER: {s['speaker']}",f"DELIVERY: {s['delivery']}",
                     f"MOTION: {s['camera'].lower().replace('_',' ')}",f"TRANSITION_IN: {'fadeblack' if s['id']=='S1_01' else 'cut'}",""]
    production += ["=== COVERAGE SUMMARY ===",f"SHOT_COUNT: {len(SHOTS)}",f"DIALOGUE_COUNT: {sum(x['kind']=='DIALOGUE' for x in SHOTS)}",
                   "AUDIO: exact authorized lines only"]
    (OUT/"V8_COMPATIBLE_PRODUCTION_PACKAGE.txt").write_text("\n".join(x for x in production if x!="")+"\n",encoding="utf-8")
    sound=["DIALOGUE STILL VIDEO STUDIO — OPTIONAL SOUND PLAN FORMAT v1","",
           "The production package remains authoritative. This companion file is optional.",
           "If no sound plan is imported, the app does not invent background music, SFX, or ambience.",
           "","=== SOUND PLAN ===","VERSION: 1","","=== GLOBAL ===",
           "MUSIC_ENABLED: true","SFX_ENABLED: true","AMBIENCE_ENABLED: true","DUCKING: normal"]
    for sn in range(1,5):
        sound += ["",f"=== SCENE {sn} ===",
                  f"AMBIENCE: {'quiet upscale Manhattan hotel suite with nighttime rain' if sn==1 else 'quiet hotel elevator and corridor room tone'}",
                  "AMBIENCE_FILE: amb_manhattan_hotel_rain_01.wav",
                  f"MUSIC: {'restrained dark suspense' if sn!=3 else 'minimal betrayal tension with pauses'}",
                  "MUSIC_FILE: music_original_cinematic_suspense_01.wav","DUCKING: normal"]
        for s in [x for x in SHOTS if x["scene"]==sn and x["effect"] in ("ring_drop","phone_wake","floor_ding","door_swing","four_beeps","tv_turn_on","remote_play")]:
            sound += ["",f"=== IMAGE {sn}.{s['id'].split('_')[1]} ===",
                      f"SFX: sfx_{s['effect']}_01.wav | at=0.30 | gain=-12"]
    sound+=["","=== END SOUND PLAN ==="]
    (OUT/"SOUND_PLAN.txt").write_text("\n".join(sound)+"\n",encoding="utf-8")
    checks=[]
    groups={
      "V9.1.1":["full master read","register applicable requirements","preserve exact screenplay","resolve source conflicts","record status evidence timestamps"],
      "V9.1.2":["distinct story-motivated object animations","at least one physical object movement","selective independent camera movement","real normal-speed visible effects","no fake crop as object animation"],
      "V9.1.3":["plan effect layer anchor hinge and fixed parts","clean plates and transparent overlays","occlusion and preserved backgrounds","coherent object texture shadow and attachment"],
      "V9.1.4":["record camera transforms and focal targets","stable deterministic absolute timing","safe overscan and no black edges","selective HOLD reaction coverage"],
      "V9.1.5":["Gate A preproduction","Gate B visual asset inspection","Gate C accurate TTS timing","Gate D full decoded movie probe","Gate D human normal-speed review","Gate D full audio listening review","Gate E exact delivered package"],
      "V9-A":["realistic drama mode","16:9 landscape","1920x1080","30fps","Manhattan location","American accents","exact spoken words","correct selected TTS model","actual chosen image engine","no fabricated reference access"],
      "V9-B":["every dialogue beat mapped","key listener reactions","eyeline and 180-degree geography","genuine OTS","dominant subject and shot rationale"],
      "V9-C":["character identity sheets three views","locked wardrobe","location references","prop references","references actually attached to image requests","maximum four references","anti-drift anatomy check","readable overlaid onscreen text","contact sheet","missing-shot report"],
      "V9-D":["varied camera movement","motivated reaction holds","no repeated three push-ins","no fake orbit","smooth eased movement","no random shake","restrained scene transitions"],
      "V9-E":["effect source plate","isolated object motion","initial/final state","mechanical door movement","phone isolated screen wake","ring isolated falling","TV isolated screen state","four phones message behavior"],
      "V9-F":["four locked voices","one voice per character","Gemini 3.8 Flash-Lite actual verification","all words verbatim","measured waveform duration","performances emotional not flat","intentional breathing room","voice-first ducked music","SFX sync","no unintended lip-sync demand"],
      "V9-G":["script to scenes","references before shots","image QA","audio timing before timeline","render from source","actual 1080p CPU x264","reproducible GitHub workflow"],
      "V9-H":["PROJECT_SETTINGS.json","CHARACTER_LOCATION_PROP_BIBLE.md","SHOT_MANIFEST_V9.json","V8_COMPATIBLE_PRODUCTION_PACKAGE.txt","SOUND_PLAN.txt","ASSET_QA_REPORT.md","RENDER_QA_REPORT.md","AGENT_HANDOFF.md","final MP4 and actual links"],
      "V8-1":["single three-view sheet no extra pose","visible-only wardrobe in CUs","framing enforced in prompts","exact foreground exclusions","reaction purpose clear","per-image shot reset","adjacent composition diversity","silent ACTION beats","reveal staged multi-beat","scene bridge coverage","hard cut reaction timing","source-authorized SFX only","precise companion sound format","separate narration and dialogue fields"]
    }
    for section,requirements in groups.items():
        for i,req in enumerate(requirements,1):
            checks.append(dict(REQUIREMENT_ID=f"{section}-{i:02d}",SOURCE_SECTION=section,
                  REQUIREMENT=req,APPLICABILITY="mandatory",
                  STATUS="PASS" if req in ("realistic drama mode","16:9 landscape","1920x1080","30fps","Manhattan location","American accents","exact spoken words","maximum four references","script to scenes","PROJECT_SETTINGS.json","CHARACTER_LOCATION_PROP_BIBLE.md","SHOT_MANIFEST_V9.json","V8_COMPATIBLE_PRODUCTION_PACKAGE.txt","SOUND_PLAN.txt") else "PENDING",
                  EVIDENCE="preflight settings and source-locked manifests" if req in ("realistic drama mode","16:9 landscape","1920x1080","30fps","Manhattan location","American accents","exact spoken words","maximum four references","script to scenes","PROJECT_SETTINGS.json","CHARACTER_LOCATION_PROP_BIBLE.md","SHOT_MANIFEST_V9.json","V8_COMPATIBLE_PRODUCTION_PACKAGE.txt","SOUND_PLAN.txt") else None,
                  ISSUE=None,FIX=None,VERIFIED_ARTIFACT="preproduction manifests" if req in ("realistic drama mode","16:9 landscape","1920x1080","30fps","Manhattan location","American accents","exact spoken words","maximum four references","script to scenes","PROJECT_SETTINGS.json","CHARACTER_LOCATION_PROP_BIBLE.md","SHOT_MANIFEST_V9.json","V8_COMPATIBLE_PRODUCTION_PACKAGE.txt","SOUND_PLAN.txt") else None,
                  VERIFIED_AT=datetime.now(timezone.utc).isoformat() if req in ("realistic drama mode","16:9 landscape","1920x1080","30fps","Manhattan location","American accents","exact spoken words","maximum four references","script to scenes","PROJECT_SETTINGS.json","CHARACTER_LOCATION_PROP_BIBLE.md","SHOT_MANIFEST_V9.json","V8_COMPATIBLE_PRODUCTION_PACKAGE.txt","SOUND_PLAN.txt") else None))
    checks +=[dict(REQUIREMENT_ID="USER-CPU-PARALLEL",SOURCE_SECTION="current user request",
                  REQUIREMENT="multiple parallel public GitHub Actions CPU runners",APPLICABILITY="mandatory",
                  STATUS="PENDING",EVIDENCE=None,ISSUE=None,FIX=None,VERIFIED_ARTIFACT=None,VERIFIED_AT=None),
              dict(REQUIREMENT_ID="USER-TTS-KIE",SOURCE_SECTION="current user request",REQUIREMENT="Kie.ai Gemini 3.8 Flash-Lite TTS, no substitute",APPLICABILITY="mandatory",
                  STATUS="PENDING",EVIDENCE=None,ISSUE=None,FIX=None,VERIFIED_ARTIFACT=None,VERIFIED_AT=None),
              dict(REQUIREMENT_ID="USER-VISUAL-QUALITY",SOURCE_SECTION="current user request",REQUIREMENT="premium watchable visually rich story, no generic slideshow",APPLICABILITY="mandatory",
                  STATUS="PENDING",EVIDENCE=None,ISSUE=None,FIX=None,VERIFIED_ARTIFACT=None,VERIFIED_AT=None)]
    save_json("COMPLIANCE_AUDIT.json",dict(source="V9.1 full master+story",audit_type="producer self-audit",checks=checks,
       conflicts=[dict(conflict='V8 "Animation optional" versus V9.1 "story-motivated object animation required" ',
                       controlling="V9.1 mandatory rendered-video gate",resolution="animate isolated ring, phone, door, television, remote"),
                  dict(conflict='V8 Nigerian visual/accent default versus specific Manhattan American screenplay',
                       controlling="user screenplay and V9-A",resolution="Manhattan American English, do not impose Nigerian identity")],
       final_artifact_status="BLOCKED",final_sha256=None))
    (OUT/"AGENT_HANDOFF.md").write_text("# Current state\nPreproduction generated. Actual paid image/TTS work and final export require the connected GitHub Actions run and valid KIE_API_KEY secret.\nNever claim a completed video from manifest files alone.\n",encoding="utf-8")
    print("Preflight: source-locked",len(SHOTS),"shots, audit",len(checks),"individual checks",flush=True)

def request_api(path,key,payload=None):
    url="https://api.kie.ai/api/v1/jobs"+path
    body=json.dumps(payload).encode("utf-8") if payload is not None else None
    headers={"Authorization":"Bearer "+key,"Accept":"application/json"}
    if body is not None: headers["Content-Type"]="application/json"
    last=None
    for attempt in range(6):
        try:
            req=urllib.request.Request(url,headers=headers,data=body,method="POST" if body else "GET")
            with urllib.request.urlopen(req,timeout=70) as r:
                res=json.load(r)
            if res.get("code")!=200:raise RuntimeError(f"Kie API code {res.get('code')}: {res.get('msg')}")
            return res["data"]
        except urllib.error.HTTPError as e:
            error=e.read(2000).decode(errors="replace")
            last=RuntimeError(f"Kie HTTP {e.code}: {error[:300]}")
            if e.code not in (429,500,502,503,504):break
        except Exception as e:
            last=e
            if "402" in str(e) or "401" in str(e) or "insufficient" in str(e).lower():break
        time.sleep(min(30,2**attempt))
    raise RuntimeError(str(last))

def kie_task(model,inputs,output_path):
    key=os.getenv("KIE_API_KEY","").strip()
    if not key:raise RuntimeError("GitHub Actions secret KIE_API_KEY is missing")
    payload={"model":model,"input":inputs}
    tid=request_api("/createTask",key,payload).get("taskId")
    if not tid:raise RuntimeError("Kie createTask returned no taskId")
    print("Submitted",output_path.name,"task",tid,flush=True)
    start=time.monotonic()
    while time.monotonic()-start<950:
        data=request_api("/recordInfo?"+urllib.parse.urlencode({"taskId":tid}),key)
        state=data.get("state")
        if state=="success":
            r=data.get("response") or data.get("resultJson") or {}
            if isinstance(r,str):r=json.loads(r)
            urls=r.get("resultUrls") or (r.get("result_urls") if isinstance(r,dict) else None) or []
            if not urls:raise RuntimeError(f"{tid} returned success but no downloadable resultUrls")
            output_path.parent.mkdir(parents=True,exist_ok=True)
            with urllib.request.urlopen(urls[0],timeout=140) as f:contents=f.read()
            if len(contents)<600:raise RuntimeError("Returned media suspiciously small")
            output_path.write_bytes(contents)
            return dict(task_id=tid,model=model,public_url=urls[0],bytes=len(contents),file=str(output_path))
        if state=="fail":raise RuntimeError(f"Kie task {tid} failed: {data.get('failMsg') or data.get('failCode')}")
        if state not in ("waiting","queuing","generating"):raise RuntimeError(f"Unexpected Kie status {state}: {tid}")
        time.sleep(7)
    raise RuntimeError(f"Kie task timed out: {tid} (check status to recover; do not duplicate expense blindly)")

def reference_jobs():
    raise RuntimeError("DISABLED: images MUST be generated with ChatGPT, not Kie.ai. Supply native ChatGPT PNG references under output/refs/ and verify independently.")

def frames(shard):
    raise RuntimeError("DISABLED: images MUST be generated with ChatGPT, not Kie.ai. Supply native ChatGPT PNG frames under output/frames/ and verify independently.")

def voices(scene):
    d=[s for s in SHOTS if s["scene"]==scene and s["kind"]=="DIALOGUE"]
    def do(s):
        speaker=s["speaker"].replace("RECORDED ","")
        if speaker=="UNKNOWN VOICE":speaker="BRIAN"
        c=STORY["characters"][speaker]
        emotion=s["delivery"].lower()
        intensity="restrained";pace="measured and natural"
        if any(k in emotion for k in ("anger","shout","outrage","fury")):intensity="controlled firm urgency";pace="clipped with clear consonants"
        if any(k in emotion for k in ("fear","shock","panic","terrified","devastation","hurt")):intensity="subdued, emotionally authentic";pace="slower with breath"
        if "bitter" in emotion:intensity="wry devastated";pace="hesitant, bitterly ironic"
        style=f"Act as {c['vocal']} Performance: {emotion}. {intensity}, {pace}. American English. Recite the supplied text exactly, not character names or directions. No invented words."
        p=OUT/"voices"/(s["id"]+".wav")
        if p.exists() and p.stat().st_size>600:
            result=dict(model=MODEL_TTS,file=str(p),bytes=p.stat().st_size,
                        cached_from_previous_run=True)
        else:
            for attempt in range(3):
                try:
                    result=kie_task(MODEL_TTS,dict(temperature=0.75,
                      speakers=[dict(speaker_id="Speaker 1",voice_name=c["voice"])],
                      dialogue_turns=[dict(speaker_id="Speaker 1",style=style,text=s["spoken_text"])]),
                      p)
                    break
                except RuntimeError as e:
                    if any(y in str(e).lower() for y in ("internal error","please try again later","timeout")) and attempt<2:
                        print("Transient audio error, retrying only",s["id"],flush=True)
                        time.sleep(7*(attempt+1))
                    else:
                        raise
        with wave.open(str(p),"rb") as w:
            dur=w.getnframes()/w.getframerate()
            fmt=dict(channels=w.getnchannels(),rate=w.getframerate(),bits=w.getsampwidth()*8)
        return s["id"],dict(**result,source_text=s["spoken_text"],character=speaker,voice=c["voice"],duration_s=dur,format=fmt)
    result={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for k,v in ex.map(do,d):result[k]=v
    save_json(f"voice_receipts/scene_{scene}.json",result)
    print("Verified WAV header for",len(result),"dialogue performances scene",scene,flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("stage",choices=("preflight","refs","frames","voices"))
    p.add_argument("--shard",type=int,default=0)
    p.add_argument("--scene",type=int,default=1)
    a=p.parse_args()
    if a.stage=="preflight":preflight()
    elif a.stage=="refs":reference_jobs()
    elif a.stage=="frames":frames(a.shard)
    elif a.stage=="voices":voices(a.scene)
if __name__=="__main__": main()
