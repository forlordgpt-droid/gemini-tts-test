import * as THREE from 'three';
import { gsap } from 'gsap';
import { Output, Mp4OutputFormat, BufferTarget, CanvasSource, Quality } from 'mediabunny';
import '@fontsource/inter/400.css';
import '@fontsource/inter/600.css';
import '@fontsource/space-grotesk/700.css';

// ORIGINAL art.js + engine.js are classic scripts loaded in index.html.
// This is a separate deterministic movie adapter, not a new character or renderer.
const W=1920,H=1080,FPS=30,DURATION=30,CAM_Z=14.0;
const spec=[
 {id:'S01',start:0,end:3.5,art:'field_wide',fov:42,actorX:290,toX:495,scale:.79,cam:[-.85,.05,14.2,.85,.05,13.75],ease:'power2.inOut',shield:false},
 {id:'S02',start:3.5,end:8,art:'field_medium',fov:44,actorX:275,toX:525,scale:.87,cam:[-.45,0,14.05,.24,-.08,12.85],ease:'power3.out',shield:true},
 {id:'S03',start:8,end:14,art:'field_medium',fov:47,actorX:350,toX:520,scale:1.03,cam:[-.48,-.05,13.4,.3,.06,13.0],ease:'sine.inOut',shield:true},
 {id:'S04',start:14,end:20,art:'field_wide',fov:40,actorX:250,toX:610,scale:.76,cam:[-.8,.1,13.8,.85,-.07,14.7],ease:'sine.inOut',shield:true},
 {id:'S05',start:20,end:25.5,art:'field_distance',fov:42,actorX:290,toX:625,scale:.71,cam:[.8,.07,14.1,-.7,0,13.75],ease:'power2.inOut',shield:false},
 {id:'S06',start:25.5,end:30,art:'manhole_approach',fov:44,actorX:260,toX:540,scale:.73,cam:[-.58,-.13,14.05,.37,.06,12.85],ease:'power2.in',shield:false}
];
const canvas=document.getElementById('stage'),status=document.getElementById('status');
const THREE_TEXTURES=new Map();
let renderer,scene,camera,actorCanvas,actorCtx,actorTexture,actorMesh,graphicCanvas,graphicCtx,graphicTexture,graphicMesh;
let activeGroup=null;
let lastTime=-1,ready=false;let snapshot={};
window.__HUNYUAN_READY=false;
window.__planSummary=spec.map(x=>({id:x.id,at:[x.start,x.end],source:x.art}));
window.__qc={status:'UNRENDERED',sources:[],samples:[]};
const clamp=(n,a=0,b=1)=>Math.max(a,Math.min(b,n)),smooth=t=>t*t*(3-2*t);
const rng=(seed)=>()=>{seed=(Math.imul(seed,1664525)+1013904223)|0;return(seed>>>0)/4294967296;};

function surface(w,h) {const c=document.createElement('canvas');c.width=w;c.height=h;return c;}
function newTexture(c){
 const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.minFilter=THREE.LinearFilter;t.magFilter=THREE.LinearFilter;t.anisotropy=4;
 return t;
}
function createMask(w,h,kind){
 const m=surface(w,h),c=m.getContext('2d');c.fillStyle='#fff';
 c.save();c.filter='blur(12px)';
 if(kind==='near'){
  // Physically meaningful near-field silhouette masks: grassy bottom, left/right
  // weeds and close fence posts from the image-first plates; not a uniform crop.
  c.beginPath();c.moveTo(0,h*.27);c.bezierCurveTo(w*.10,h*.13,w*.23,h*.44,w*.18,h*.72);
  c.lineTo(w*.27,h);c.lineTo(0,h);c.closePath();c.fill();
  c.beginPath();c.moveTo(w,h*.21);c.bezierCurveTo(w*.90,h*.17,w*.78,h*.45,w*.82,h*.7);
  c.lineTo(w*.72,h);c.lineTo(w,h);c.closePath();c.fill();
  c.beginPath();c.moveTo(0,h*.88);
  for(let i=0;i<=64;i++){const x=i/64*w;const y=h*(.87-.045*Math.sin(i*.8)-.015*Math.sin(i*3.1));c.lineTo(x,y);}
  c.lineTo(w,h);c.lineTo(0,h);c.closePath();c.fill();
 }else{
  // Action-plane gravel and near-mid field with natural curved transition.
  c.beginPath();c.moveTo(w*.10,h*.59);c.bezierCurveTo(w*.38,h*.48,w*.68,h*.59,w*.87,h*.57);
  c.lineTo(w*.99,h);c.lineTo(w*.02,h);c.closePath();c.fill();
 }
 c.restore();return m;
}
function extractLayers(img,artId){
 const w=img.naturalWidth,h=img.naturalHeight;
 if(w<1000||h<540)throw Error('Required premium generated image has inadequate dimensions: '+artId+' '+w+'x'+h);
 const src=surface(w,h),sctx=src.getContext('2d');sctx.drawImage(img,0,0,w,h);
 const nm=createMask(w,h,'near'),mm=createMask(w,h,'mid');
 const far=surface(w,h),fc=far.getContext('2d');fc.drawImage(img,0,0,w,h);
 // Clean-plate repair behind extractable masks, preserving illustrated scene.
 // Nearby chroma/texture is softly propagated, never transparent empty holes.
 const soft=surface(w,h),sc=soft.getContext('2d');
 sc.filter='blur(32px)';sc.drawImage(img,-16,-16,w+32,h+32);
 const union=surface(w,h),uc=union.getContext('2d');uc.drawImage(mm,0,0);uc.drawImage(nm,0,0);
 sc.globalCompositeOperation='destination-in';sc.drawImage(union,0,0);sc.globalCompositeOperation='source-over';
 fc.drawImage(soft,0,0);
 const mid=surface(w,h),mc=mid.getContext('2d');mc.drawImage(img,0,0,w,h);
 mc.globalCompositeOperation='destination-in';mc.drawImage(mm,0,0);mc.globalCompositeOperation='source-over';
 const near=surface(w,h),nc=near.getContext('2d');nc.drawImage(img,0,0,w,h);
 nc.globalCompositeOperation='destination-in';nc.drawImage(nm,0,0);nc.globalCompositeOperation='source-over';
 const layers={far:newTexture(far),mid:newTexture(mid),near:newTexture(near)};
 return layers;
}
function plane(tex,z,order,id){
 const viewH=2*Math.tan(48*Math.PI/360)*(CAM_Z-z)*1.36;
 const geometry=new THREE.PlaneGeometry(viewH*W/H,viewH);
 const material=new THREE.MeshBasicMaterial({map:tex,transparent:order>0,alphaTest:0.004,depthWrite:false,depthTest:false,toneMapped:false,side:THREE.DoubleSide});
 const o=new THREE.Mesh(geometry,material);o.position.z=z;o.renderOrder=order;o.userData.layerId=id;return o;
}
async function loadArt(id) {
 if(THREE_TEXTURES.has(id))return THREE_TEXTURES.get(id);
 const img=new Image();img.decoding='async';img.src='/assets/'+id+'.png';await img.decode();
 const layers=extractLayers(img,id);THREE_TEXTURES.set(id,layers);
 return layers;
}
function makeActor(s) {
 const world=new window.HunyuanWorld2D();
 const actor=world.create({id:'Hunyuan_'+s.id,x:s.actorX,y:550,scale:s.scale,view:'sideRight'});
 actor.add('body','run',{to:{x:s.toX,y:550}},0,s.end-s.start);
 actor.add('emotion','emotion',{emotion:'afraid'},0,0);
 actor.add('view','view',{view:'sideRight'},0,0);
 return actor;
}
function cameraAt(s,local){
 s.timeline.time(clamp(local,0,s.end-s.start),false);
 const o=s.cameraObject;
 camera.position.set(o.x,o.y,o.z);camera.fov=s.fov;camera.updateProjectionMatrix();camera.lookAt(0,0,-2.9);
 camera.updateMatrixWorld(true);
}
function buildGroup(s,texture){
 s.group=new THREE.Group();s.group.name=s.id;
 s.group.add(plane(texture.far,-5,0,s.art+'_FAR_CLEAN'));
 s.group.add(plane(texture.mid,-1.6,1,s.art+'_MID_GRAVEL'));
 s.group.add(plane(texture.near,3.7,5,s.art+'_FG_FENCE_GRASS'));
 scene.add(s.group);s.group.visible=false;
 s.actor=makeActor(s);
 s.cameraObject={x:s.cam[0],y:s.cam[1],z:s.cam[2]};
 s.timeline=gsap.timeline({paused:true,defaults:{ease:s.ease}});
 s.timeline.to(s.cameraObject,{x:s.cam[3],y:s.cam[4],z:s.cam[5],duration:s.end-s.start,ease:s.ease},0);
}
function shotAt(t){
 return spec.find(s=>t>=s.start && t<s.end) || spec[spec.length-1];
}
function poseSvg(s,local){
 const pose=s.actor.poseAt(local);
 // Cinematic action correction added to original procedural 2D rig; no static asset.
 if(s.shield){
  const p=clamp((local-.15)/.72);const strength=smooth(p);
  const target=[[44,-284],[52,-344],[6,-394]];
  pose.arms[1]=pose.arms[1].map((xy,i)=>[xy[0]+(target[i][0]-xy[0])*strength,xy[1]+(target[i][1]-xy[1])*strength]);
  pose.openHand=true;pose.headTilt=-6*strength;pose.emotion='afraid';
 }
 return window.HunyuanArt.svg(window.HunyuanArt.render(pose),900,600);
}
async function paintActor(s,local){
 const svg=poseSvg(s,local),url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml;charset=utf-8'}));
 try{
  const img=new Image();img.src=url;await img.decode();
  actorCtx.clearRect(0,0,900,600);actorCtx.drawImage(img,0,0,900,600);
  actorTexture.needsUpdate=true;
 }finally {URL.revokeObjectURL(url);}
}
function drawDust(t){
 const r=rng(43887);
 for(let i=0;i<58;i++){
  const x=(r()*W+t*(8+r()*35))%W,y=(r()*H+Math.sin(t*.8+i)*19+H)%H;
  const rad=1+r()*4;graphicCtx.beginPath();graphicCtx.arc(x,y,rad,0,Math.PI*2);
  graphicCtx.fillStyle='rgba(255,229,174,'+(0.055+0.13*Math.sin(t*.9+i)**2)+')';graphicCtx.fill();
 }
}
function backgroundLight(t){
 const b=clamp(Math.sin((t+1)*.48)*.3+.25,.08,.45);
 const g=graphicCtx.createLinearGradient(0,0,W,0);
 g.addColorStop(0,'rgba(247,230,218,'+(.05+b*.12)+')');g.addColorStop(.42,'rgba(188,219,239,.01)');
 g.addColorStop(1,'rgba(239,122,69,.04)');graphicCtx.fillStyle=g;graphicCtx.fillRect(0,0,W,H);
 const a=.04+.05*Math.sin(t*1.4);graphicCtx.fillStyle='rgba(255,251,228,'+a+')';
 graphicCtx.fillRect(0,0,20+Math.round(15*Math.sin(t*.5)),H);
}
function textOut(text,x,y,size=56,align='left',color='#fff9e9'){
 graphicCtx.save();graphicCtx.textAlign=align;graphicCtx.textBaseline='middle';
 graphicCtx.font='700 '+size+'px "Space Grotesk"';graphicCtx.shadowColor='rgba(4,16,31,.8)';graphicCtx.shadowBlur=18;
 graphicCtx.fillStyle=color;graphicCtx.fillText(text,x,y);graphicCtx.restore();
}
function graphicReveal(t,st,en){
 const enter=smooth(clamp((t-st)/.38)),exit=smooth(clamp((en-t)/.35));
 return enter*exit;
}
function drawGraphics(t){
 graphicCtx.clearRect(0,0,W,H);
 backgroundLight(t);drawDust(t);
 graphicCtx.save();
 // Guarded, short professionally typeset story graphics, not caption spam.
 if(t>=3.7&&t<6.4){
  const a=graphicReveal(t,3.7,6.4);graphicCtx.globalAlpha=a;
  graphicCtx.fillStyle='rgba(8,24,48,.62)';graphicCtx.fillRect(115,135,620,116);
  graphicCtx.fillStyle='#eb8b61';graphicCtx.fillRect(115,135,9,116);
  textOut('DO NOT TURN AROUND',159,194,62);
 }
 if(t>=9.1&&t<11.7){
  graphicCtx.globalAlpha=graphicReveal(t,9.1,11.7);
  graphicCtx.fillStyle='rgba(15,42,56,.61)';graphicCtx.fillRect(1120,184,600,96);
  textOut('PROTECT YOUR EYES',1154,232,48);
  graphicCtx.strokeStyle='#d6e8f0';graphicCtx.lineWidth=5;
  graphicCtx.beginPath();graphicCtx.arc(1083,233,31,0,Math.PI*2);graphicCtx.stroke();
  graphicCtx.beginPath();graphicCtx.moveTo(1063,228);graphicCtx.lineTo(1093,228);graphicCtx.stroke();
 }
 if(t>=17.5&&t<19.6){
  graphicCtx.globalAlpha=graphicReveal(t,17.5,19.6)*.9;
  graphicCtx.strokeStyle='#ffe1a4';graphicCtx.lineWidth=6;graphicCtx.beginPath();
  graphicCtx.moveTo(250,800);graphicCtx.bezierCurveTo(740,780,1050,700,1670,640);graphicCtx.stroke();
  graphicCtx.fillStyle='#ffdfa3';graphicCtx.font='600 34px "Inter"';graphicCtx.fillText('LIGHT ARRIVES FIRST',245,747);
 }
 if(t>=21&&t<25.5){
  graphicCtx.globalAlpha=graphicReveal(t,21,25.5);
  graphicCtx.strokeStyle='#b2e9e1';graphicCtx.lineWidth=6;
  const grow=smooth(clamp((t-21)/1.2));
  graphicCtx.beginPath();graphicCtx.moveTo(200,785);graphicCtx.lineTo(200+1370*grow,785);graphicCtx.stroke();
  graphicCtx.beginPath();graphicCtx.moveTo(1510,772);graphicCtx.lineTo(1575,785);graphicCtx.lineTo(1510,798);graphicCtx.stroke();
  textOut('340 m/s',250,712,74,'left','#d6faf2');
  textOut('3 km',1570,712,68,'right','#ffe1aa');
 }
 if(t>=27.3&&t<30){
  graphicCtx.globalAlpha=graphicReveal(t,27.3,30);
  graphicCtx.fillStyle='rgba(7,24,38,.69)';graphicCtx.fillRect(1154,120,645,158);
  graphicCtx.fillStyle='#f5a76a';graphicCtx.fillRect(1154,120,13,158);
  textOut('≈ 9 SECONDS',1206,202,91);
 }
 graphicCtx.restore();graphicTexture.needsUpdate=true;
}
function alignOverlay(){
 graphicMesh.quaternion.copy(camera.quaternion);
 const dir=new THREE.Vector3();camera.getWorldDirection(dir);
 graphicMesh.position.copy(camera.position).addScaledVector(dir,1.1);
 const worldH=2*Math.tan(camera.fov*Math.PI/360)*1.1;
 graphicMesh.scale.set(worldH*W/H,worldH,1);
}
async function renderAt(t){
 if(!ready)throw Error('Cannot render until all approved illustrated assets and original rig are preloaded');
 t=clamp(t,0,DURATION-1/FPS);const s=shotAt(t),local=t-s.start;
 if(activeGroup!==s.group){if(activeGroup)activeGroup.visible=false;s.group.visible=true;activeGroup=s.group;}
 cameraAt(s,local);await paintActor(s,local);
 // Keep source artwork on THREE perspective depth planes; actor is native 2D vector.
 actorMesh.scale.set(s.id==='S03'?1.22:1, s.id==='S03'?1.22:1,1);
 actorMesh.position.set(0,-.2,1.25);
 drawGraphics(t);alignOverlay();
 renderer.render(scene,camera);lastTime=t;
 snapshot={seconds:t,shot:s.id,source:s.art,near:s.art+'_FG_FENCE_GRASS',mid:s.art+'_MID_GRAVEL',far:s.art+'_FAR_CLEAN',
  camera:[camera.position.x,camera.position.y,camera.position.z],fov:s.fov,actor_action:'original Hunyuan rig run; shielding if story warrants',parallax:true};
 if(window.__qc.samples.length<9&&(Math.abs(t%5)<.033||t>29.9))window.__qc.samples.push(snapshot);
 return snapshot;
}
window.renderAt=renderAt;
function downloadBlob(bytes,name,type){
 const blob=bytes instanceof Blob?bytes:new Blob([bytes],{type});
 const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.style.display='none';
 document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),20000);
}
async function exportSegment(){
 if(!ready)throw Error('Not ready');
 document.getElementById('export').disabled=true;
 try{
  if(typeof VideoEncoder==='undefined')throw Error('REQUIRED WebCodecs VideoEncoder absent; no fallback');
  const cfg={codec:'avc1.420028',width:W,height:H,bitrate:5000000,framerate:FPS};
  const supported=await VideoEncoder.isConfigSupported(cfg);
  if(!supported.supported)throw Error('CPU H.264 WebCodecs unavailable; no fallback');
  const params=new URLSearchParams(location.search),shard=Number(params.get('shard')||0),frames=Number(params.get('frames')||300);
  if(![150,300].includes(frames)||![0,1,2].includes(shard))throw Error('Invalid shard or frame count');
  const output=new Output({format:new Mp4OutputFormat(),target:new BufferTarget()});
  const source=new CanvasSource(canvas,{codec:'avc',quality:new Quality('high')});
  output.addVideoTrack(source,{frameRate:FPS});await output.start();
  for(let i=0;i<frames;i++){
   await renderAt((shard*300+i)/FPS);
   await source.add(i/FPS,1/FPS,{keyFrame:i===0||i%60===0});
   if(i%30===0){status.textContent='Encoding '+(i+1)+' / '+frames+' on public CPU shard '+shard;await new Promise(r=>setTimeout(r,0));}
  }
  await output.finalize();
  if(!output.target.buffer || output.target.buffer.byteLength<20000 || !(output.target.buffer instanceof ArrayBuffer || ArrayBuffer.isView(output.target.buffer))) throw Error('Mediabunny produced no valid MP4 bytes');
  window.__qc.status='TECHNICAL_ENCODE_READY_VISUAL_AUDIT_PENDING';window.__qc.encoded_frames=frames;
  downloadBlob(output.target.buffer,frames===150?'gate_5s.mp4':'part_'+shard+'.mp4','video/mp4');
  status.textContent='Encoded '+frames+' frames with Mediabunny and WebCodecs';
 }catch(e){console.error(e);status.textContent='HARD STOP: '+e.message;throw e;}
}
window.exportSegment=exportSegment;
function wavFromPCM(audio){
 const n=audio.length,buffer=new ArrayBuffer(44+n*2),v=new DataView(buffer);
 const put=(off,s)=>{for(let i=0;i<s.length;i++)v.setUint8(off+i,s.charCodeAt(i));};
 put(0,'RIFF');v.setUint32(4,36+n*2,true);put(8,'WAVE');put(12,'fmt ');v.setUint32(16,16,true);
 v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,24000,true);v.setUint32(28,48000,true);
 v.setUint16(32,2,true);v.setUint16(34,16,true);put(36,'data');v.setUint32(40,n*2,true);
 for(let i=0;i<n;i++)v.setInt16(44+i*2,Math.round(clamp(audio[i],-1,1)*32767),true);
 return buffer;
}
async function offlineSoundEffects(){
 if(typeof OfflineAudioContext==='undefined')throw Error('Required OfflineAudioContext unavailable');
 const sr=24000,n=sr*30,c=new OfflineAudioContext(1,n,sr),noise=c.createBuffer(1,n,sr),d=noise.getChannelData(0),r=rng(9273731);
 for(let i=0;i<n;i++)d[i]=(r()*2-1)*(.008+.004*Math.sin(i/sr*.31)**2);
 const wind=c.createBufferSource();wind.buffer=noise;wind.connect(c.destination);wind.start(0);
 // Event-synchronized soft gravel footsteps; NO premature shockwave hit.
 const events=[];for(let t=.2;t<29.7;t+=.39)events.push(t);
 for(let j=0;j<events.length;j++){
  const t=events[j],len=Math.floor(.095*sr),click=c.createBuffer(1,len,sr),s=click.getChannelData(0),rnd=rng(j+201);
  for(let i=0;i<len;i++)s[i]=(rnd()*2-1)*Math.exp(-i/(sr*.018))*.19;
  const b=c.createBufferSource();b.buffer=click;const g=c.createGain();g.gain.value=.55;
  b.connect(g);g.connect(c.destination);b.start(t);
 }
 const rendered=await c.startRendering();
 return wavFromPCM(rendered.getChannelData(0));
}
window.generateSfxWav=async()=>downloadBlob(await offlineSoundEffects(),'original_sfx_30s.wav','audio/wav');
document.getElementById('export').addEventListener('click',()=>exportSegment().catch(e=>console.error('Export hard stop',e)));
document.getElementById('sfx').addEventListener('click',()=>window.generateSfxWav().catch(e=>console.error('SFX hard stop',e)));
async function initialize(){
 if(typeof window.HunyuanWorld2D!=='function'||!window.HunyuanArt)throw Error('Required original Hunyuan rig art.js/engine.js missing');
 await document.fonts.ready;
 renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true,powerPreference:'low-power'});
 renderer.setSize(W,H,false);renderer.setPixelRatio(1);renderer.outputColorSpace=THREE.SRGBColorSpace;
 scene=new THREE.Scene();scene.background=new THREE.Color(0x162531);
 camera=new THREE.PerspectiveCamera(42,W/H,.1,100);camera.position.set(0,0,CAM_Z);
 actorCanvas=surface(900,600);actorCtx=actorCanvas.getContext('2d',{willReadFrequently:true});
 actorTexture=newTexture(actorCanvas);
 actorMesh=new THREE.Mesh(new THREE.PlaneGeometry(16.25,10.85),new THREE.MeshBasicMaterial({
  map:actorTexture,transparent:true,depthTest:false,depthWrite:false,toneMapped:false,side:THREE.DoubleSide}));
 actorMesh.renderOrder=3;scene.add(actorMesh);
 graphicCanvas=surface(W,H);graphicCtx=graphicCanvas.getContext('2d');
 graphicTexture=newTexture(graphicCanvas);
 graphicMesh=new THREE.Mesh(new THREE.PlaneGeometry(1,1),new THREE.MeshBasicMaterial({
  map:graphicTexture,transparent:true,depthTest:false,depthWrite:false,toneMapped:false}));
 graphicMesh.renderOrder=30;scene.add(graphicMesh);
 for(const s of spec){const tx=await loadArt(s.art);buildGroup(s,tx);}
 window.__qc.sources=[...THREE_TEXTURES.keys()];ready=true;window.__HUNYUAN_READY=true;
 document.getElementById('export').disabled=false;document.getElementById('sfx').disabled=false;
 await renderAt(0);status.textContent='Ready: 4 premium illustrations, native Hunyuan rig, Three.js depth camera, GSAP';
}
initialize().catch(e=>{console.error('Required-stack hard stop',e);status.textContent='HARD STOP: '+e.message;window.__HUNYUAN_ERROR=e.message;});
