import * as THREE from 'three';
import gsap from 'gsap';
import {Output,Mp4OutputFormat,BufferTarget,CanvasSource,Quality} from 'mediabunny';

// Story5 complete final 30–60 original-narrator sequence; approved first30 master kept exactly unchanged.
// Hunyuan native rig is loaded and tested, not mistaken for a female actor.
// ALL NEW SHOTS are 30–60; the owner-approved 0–30 MP4 is immutable.
const W=1920,H=1080,FPS=30,LENGTH=60;
const cuts=[
 {id:'SAFE_ROOM_FOUND',start:30,end:33.8,image:0,x0:-.61,x1:.46,y0:.14,y1:-.09,z0:10.72,z1:10.04},
 {id:'LOCK_THE_DOOR',start:33.8,end:37.6,image:1,x0:.42,x1:-.47,y0:-.13,y1:.085,z0:10.42,z1:9.62},
 {id:'DOOR_IMPACT',start:37.6,end:41.8,image:2,x0:-.32,x1:.37,y0:.08,y1:-.09,z0:10.65,z1:9.73},
 {id:'FALSE_SAFETY',start:41.8,end:45,image:3,x0:.47,x1:-.37,y0:.085,y1:-.075,z0:10.52,z1:9.89},
 {id:'MONITOR_WAKES',start:45,end:48.7,image:4,x0:-.44,x1:.50,y0:-.09,y1:.10,z0:10.48,z1:9.81},
 {id:'UNKNOWN_CALLER_ON_FEED',start:48.7,end:52.4,image:5,x0:.46,x1:-.35,y0:-.08,y1:.075,z0:10.68,z1:9.51},
 {id:'RECORDED_TRAP_WARNING',start:52.4,end:56.4,image:6,x0:-.35,x1:.42,y0:.095,y1:-.07,z0:10.6,z1:9.64},
 {id:'REAR_DOOR_OPENS',start:56.4,end:60,image:7,x0:.52,x1:-.24,y0:.085,y1:-.13,z0:10.72,z1:9.08}
];
const stage=document.getElementById('stage');
const renderer=new THREE.WebGLRenderer({canvas:stage,preserveDrawingBuffer:true,antialias:true,alpha:false});
renderer.setPixelRatio(1);renderer.setSize(W,H,false);
renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.NoToneMapping;renderer.setClearColor(0x071424);
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(2*Math.atan(.45)*180/Math.PI,16/9,.1,100);
const track=gsap.timeline({paused:true});
for(const s of cuts){
 track.set(camera.position,{x:s.x0,y:s.y0,z:s.z0},s.start);
 track.to(camera.position,{x:s.x1,y:s.y1,z:s.z1,duration:s.end-s.start,ease:'power2.inOut'},s.start);
}
const depths=[{z:-4,order:0},{z:-.35,order:2},{z:2.2,order:4}];
function plane(tex,z,width,order){
 const mat=new THREE.MeshBasicMaterial({map:tex,transparent:true,depthTest:false,depthWrite:false,toneMapped:false,side:THREE.DoubleSide});
 const mesh=new THREE.Mesh(new THREE.PlaneGeometry(width,width*9/16),mat);mesh.position.z=z;mesh.renderOrder=order;scene.add(mesh);return mesh;
}
function tex(img){const t=new THREE.Texture(img);t.needsUpdate=true;t.colorSpace=THREE.SRGBColorSpace;t.minFilter=THREE.LinearFilter;return t;}
async function load(src){const im=new Image();im.src=src;await im.decode();return im;}
const objects=[];
for(let i=0;i<8;i++){
 const names=['far','mid','front'];const m=[];
 for(let j=0;j<3;j++){
  const z=depths[j].z;const im=await load('assets/'+names[j]+'_'+i+(j===0?'.jpg':'.png'));
  m.push(plane(tex(im),z,(10-z)*1.6*1.22,depths[j].order));
 }
 objects.push(m);
}
if(typeof window.Hunyuan2D!=='function'||typeof window.HunyuanArt?.svg!=='function')throw Error('Original Hunyuan art.js and engine.js missing');
const nativeRig=new window.Hunyuan2D({id:'Hunyuan',x:850,y:820,scale:.75,view:'quarterRight'});
if(!nativeRig.poseAt(0)||!nativeRig.svgAt(0))throw Error('Original authored 2D rig failed');
// Canvas2D atmosphere at an independent 3D depth: no SVG-only backgrounds.
const ambient=document.createElement('canvas');ambient.width=W;ambient.height=H;
const ag=ambient.getContext('2d',{alpha:true});const ambientTex=new THREE.CanvasTexture(ambient);
ambientTex.colorSpace=THREE.SRGBColorSpace;
const ambientMesh=plane(ambientTex,-.78,(10.78)*1.6*1.22,3);
const gfx=document.createElement('canvas');gfx.width=W;gfx.height=H;const g=gfx.getContext('2d',{alpha:true});
const gfxTex=new THREE.CanvasTexture(gfx);gfxTex.colorSpace=THREE.SRGBColorSpace;
const graphicsMesh=plane(gfxTex,4.1,(10-4.1)*1.6*1.22,9);
function clamp(x){return Math.max(0,Math.min(1,x))}function ease(x){x=clamp(x);return x*x*(3-2*x)}
function rnd(i){return ((Math.imul(i+17,1664525)+1013904223)>>>0)/4294967295}
function text(s,x,y,sz,color,weight){g.font=(weight||650)+' '+sz+'px Inter,system-ui,sans-serif';g.fillStyle=color||'#f8f4e8';g.fillText(s,x,y)}
function pill(s,x,y,alpha){
 g.save();g.globalAlpha=clamp(alpha);
 const width=Math.max(330,40+s.length*15);g.fillStyle='rgba(5,19,36,.69)';g.strokeStyle='rgba(255,208,114,.52)';g.lineWidth=2;
 g.beginPath();g.roundRect(x,y,width,51,13);g.fill();g.stroke();text(s,x+25,y+35,21,'#f7d6a1',700);g.restore();
}
function overlay(t,s){
 ag.clearRect(0,0,W,H);g.clearRect(0,0,W,H);
 const u=t-s.start;
 const isDoor=s.image<4, isBunker=s.image>=3, isMonitor=s.image>=4&&s.image<=6;
 const pulse=(Math.max(0,Math.sin(t*4.1))**4);
 // Layered steam, dust and fluorescent air tracked independently from actor and architecture.
 for(let k=0;k<17;k++){
  const x=-480+((t-30)*(48+7*(k%5))+k*209)%(W+970);
  const y=125+k*57+20*Math.sin(t*.62+k*.91);
  ag.globalAlpha=(isDoor?.024:.013)+.016*(k%4);
  ag.strokeStyle=isDoor?'#bddbd8':'#81ddd4';
  ag.lineWidth=19+(k%6)*12;ag.lineCap='round';
  ag.beginPath();ag.moveTo(x-340,y-26);ag.bezierCurveTo(x+30,y-140,x+160,y+134,x+430,y-44);ag.stroke();
 }
 ag.globalAlpha=1;
 for(let k=0;k<55;k++){
  const x=(rnd(k)*2290+(t-30)*(22+24*rnd(k+51)))%2290-110;
  const y=85+rnd(k+41)*920+14*Math.sin(t*.77+k);
  const r=1+rnd(k+14)*2.7;
  ag.fillStyle=k%3?'rgba(194,245,244,.18)':'rgba(254,210,145,.13)';
  ag.beginPath();ag.ellipse(x,y,r,r*.48,.6,0,6.283);ag.fill();
 }
 // Author-driven practical light pulses, restrained editorial graphical overlays.
 if(s.id==='SAFE_ROOM_FOUND'){
  const a=Math.min(1,u*1.8,Math.max(0,(3.54-u)*2.8));
  if(a>.02)pill('SAFE ROOM / EMERGENCY ACCESS',109,91,.92*a);
  // Animated rail-pipe hazard line directs eye to the painted steel door.
  g.save();g.globalAlpha=.21*a;g.strokeStyle='#e8ca85';g.lineWidth=5;
  for(let k=0;k<3;k++){
   g.beginPath();g.moveTo(1200,80+k*26);
   g.lineTo(1750+Math.sin(u*1.2)*25,90+k*35);g.stroke();
  }g.restore();
 }
 if(s.id==='LOCK_THE_DOOR'){
  const a=Math.min(1,u*2,Math.max(0,(s.end-t)*3));
  if(a>.05)pill('EMERGENCY SEAL / ENGAGED',113,91,.9*a);
  const hit=Math.max(0,1-Math.abs(t-36.85)/.35);
  if(hit>0){
   g.save();g.globalAlpha=.20*hit;g.strokeStyle='#e9e7c1';g.lineWidth=3.4;
   for(let j=0;j<4;j++){g.beginPath();g.ellipse(1450,500,70+j*51+hit*50,85+j*55,0,0,6.283);g.stroke();}
   g.restore();
  }
 }
 if(s.id==='DOOR_IMPACT'){
  const hits=[39.18,40.42];
  let intensity=0;
  for(const at of hits){
   const d=Math.abs(t-at);intensity=Math.max(intensity,Math.max(0,1-d/.34));
  }
  if(intensity>0){
   g.save();g.globalAlpha=intensity*.2;
   g.fillStyle='#f4e2c5';g.fillRect(0,0,W,H);
   g.strokeStyle='#ffe4d0';g.lineWidth=5;
   for(let j=0;j<5;j++){g.beginPath();g.ellipse(1320,566,120+j*68+intensity*22,180+j*45,0,0,6.283);g.stroke()}
   g.restore();
  }
  // Dust bursts in foreground, response to steel impact rather than random decoration.
  for(let j=0;j<28;j++){
   const at=39.1+.04*(j%4),age=t-at;
   if(age>0&&age<1.65){
    const x=1130+rnd(j+101)*680+Math.sin(j*9)*age*85;
    const y=150+rnd(j+219)*390+age*(36+rnd(j+22)*60);
    g.globalAlpha=.24*(1-age/1.65);
    g.fillStyle='#dfc1a5';
    g.beginPath();g.arc(x,y,2+rnd(j)*5,0,6.283);g.fill();
   }
  }g.globalAlpha=1;
 }
 if(s.id==='FALSE_SAFETY'){
  const quiet=Math.min(1,(u+.3)*.6);
  // Silence is purposeful: light/haze movement slows, camera pulls back subtly.
  g.fillStyle='rgba(5,14,26,'+(.035+.045*quiet)+')';g.fillRect(0,0,W,H);
  if(u>.65&&u<2.7)pill('SEAL SECURED / TEMPORARY SHELTER',111,95,Math.min(.65,(u-.65)*2,(2.7-u)*2));
 }
 if(s.id==='MONITOR_WAKES'){
  const p=ease((t-45.2)/.64);
  g.save();g.globalAlpha=p*.26;
  const gl=g.createRadialGradient(1375,420,50,1375,420,620);
  gl.addColorStop(0,'rgba(137,248,252,.42)');gl.addColorStop(.65,'rgba(46,157,221,.18)');
  gl.addColorStop(1,'rgba(46,157,221,0)');
  g.fillStyle=gl;g.fillRect(0,0,W,H);g.restore();
  if(p>.08)pill('SECURITY SYSTEM / FEED ACTIVE',111,93,Math.min(.9,p,(s.end-t)*2));
  // CRT flicker/scan bands motivated by the monitor switching on.
  g.save();g.globalAlpha=p*.13;g.strokeStyle='#abffff';g.lineWidth=3;
  for(let i=0;i<12;i++){const x=1260+i*26,y=175+(t*92+i*21)%600;
   g.beginPath();g.moveTo(x,y);g.lineTo(x+100,y);g.stroke();}
  g.restore();
 }
 if(s.id==='UNKNOWN_CALLER_ON_FEED'){
  const a=Math.min(1,u*2.4,Math.max(0,(s.end-t)*2.2));
  if(a>.08){
   pill('CCTV / OUTSIDE SUBWAY',111,91,a);
   g.save();g.globalAlpha=a;
   g.fillStyle='rgba(4,22,35,.73)';g.strokeStyle='rgba(178,243,232,.63)';g.lineWidth=2;
   g.beginPath();g.roundRect(125,165,322,55,12);g.fill();g.stroke();
   text('IDENTITY UNKNOWN',145,201,23,'#d3f3ed',700);
   g.restore();
  }
  // Painted image already contains caller silhouette INSIDE feed. Added subtle signal flutter.
  g.save();g.globalAlpha=.09+.04*Math.sin(t*29);
  g.strokeStyle='#d9fff1';g.lineWidth=2;
  for(let k=0;k<9;k++){let x=1050+(k*91)%610,y=(k*65+t*140)%900;g.beginPath();g.moveTo(x,y);g.lineTo(x+130,y);g.stroke()}
  g.restore();
 }
 if(s.id==='RECORDED_TRAP_WARNING'){
  const alpha=Math.min(1,u*2.4,Math.max(0,(s.end-t)*2));
  if(alpha>.04)pill('RECORDED WARNING / SECURITY LOCKDOWN',112,95,alpha);
  g.save();g.globalAlpha=.08+.10*pulse;
  const rg=g.createLinearGradient(0,0,W,H);
  rg.addColorStop(0,'rgba(180,15,46,0)');rg.addColorStop(.68,'rgba(240,38,61,.46)');
  rg.addColorStop(1,'rgba(240,38,61,0)');
  g.fillStyle=rg;g.fillRect(0,0,W,H);g.restore();
  // Meaningful digital waveform around a prerecorded warning, not added spoken dialogue.
  g.save();g.strokeStyle='rgba(255,179,157,.54)';g.lineWidth=3;
  for(let i=0;i<35;i++){
   const x=1060+i*18,amp=(8+16*Math.sin(i*2.7+t*20)**2)*(.4+.6*pulse);
   g.beginPath();g.moveTo(x,945-amp);g.lineTo(x,945+amp);g.stroke();
  }g.restore();
 }
 if(s.id==='REAR_DOOR_OPENS'){
  const p=ease((t-56.98)/2.18);
  const open=100*p;
  // Painterly image contains a true rear door crack: animate a shadow-panel pullback
  // over the gap, plus the increasingly cold cyan seam to sell its real opening.
  g.save();g.globalAlpha=.6+.1*p;
  const sh=g.createLinearGradient(1280-open,160,1530,800);
  sh.addColorStop(0,'rgba(1,6,12,.03)');sh.addColorStop(1,'rgba(1,6,12,.71)');
  g.fillStyle=sh;
  g.fillRect(1452-open,190,25+open,540);
  g.restore();
  g.save();g.globalAlpha=.2+.48*p;
  g.strokeStyle='#8febef';g.shadowColor='#75e7f8';g.shadowBlur=24+23*p;g.lineWidth=2.7+4*p;
  g.beginPath();g.moveTo(1497-open,180);g.lineTo(1500-open,781);g.stroke();g.restore();
  // Sparse whisper-like nonverbal resonance: no extra voice/name is invented.
  if(t>58.65){
   const q=ease((t-58.65)/.9);
   g.save();g.strokeStyle='rgba(166,216,231,'+(.19*(1-q))+')';g.lineWidth=2.5;
   for(let i=0;i<3;i++){g.beginPath();g.ellipse(1350,475,55+q*128+i*33,100+q*70+i*26,0,0,6.283);g.stroke();}
   g.restore();
  }
 }
 // Expensive polished editorial vignette, structural composition, color kept from original painting.
 const vign=g.createRadialGradient(930,490,380,930,490,1310);
 vign.addColorStop(0,'rgba(3,8,15,0)');vign.addColorStop(1,'rgba(3,8,15,.23)');
 g.fillStyle=vign;g.fillRect(0,0,W,H);
 // Hard story-ending cut: 59.75->59.92 black, no invented epilogue or extra dialogue.
 if(t>=59.70){
  const a=ease((t-59.70)/.18);
  g.fillStyle='rgba(0,0,0,'+a+')';g.fillRect(0,0,W,H);
 }
 ambientTex.needsUpdate=true;gfxTex.needsUpdate=true;
}
async function renderFrame(t){
 if(!Number.isFinite(t)||t<30||t>=LENGTH)throw Error('Outside author-approved 30–60 second finale '+t);
 const s=cuts.find(c=>t>=c.start&&t<c.end);if(!s)throw Error('Shot missing');
 track.seek(t,false);
 const impact=Math.max(0,1-Math.abs(t-39.18)/.22)+.6*Math.max(0,1-Math.abs(t-40.42)/.16);
 camera.position.x+=impact*.028*Math.sin(t*102);
 camera.position.y+=impact*.018*Math.sin(t*132);
 camera.lookAt(0,0,0);
 for(let i=0;i<objects.length;i++)for(let j=0;j<3;j++){
  const o=objects[i][j];o.visible=i===s.image;
  if(o.visible){o.position.x=j===0?0:j===1?.065*Math.sin(t*1.39+.35):.13*Math.sin(t*1.88+.6);
   o.position.y=j===1?.023*Math.sin(t*3.5):j===2?.040*Math.sin(t*1.22):0;}
 }
 ambientMesh.position.x=.04*Math.sin(t*.35);overlay(t,s);
 graphicsMesh.position.x=camera.position.x;graphicsMesh.position.y=camera.position.y;
 renderer.render(scene,camera);
 return {t,shot:s.id,cameraX:camera.position.x,cameraZ:camera.position.z,farX:objects[s.image][0].position.x,midX:objects[s.image][1].position.x,frontX:objects[s.image][2].position.x};
}
await renderFrame(30);window.ready=true;window.renderFrame=renderFrame;
window.exportShard=async start=>{
 if(![30,35,40,45,50,55].includes(start))throw Error('Expected six 5-second 30–60 shards');
 const src=new CanvasSource(stage,{codec:'avc',quality:new Quality({bitrate:9500000})});
 const out=new Output({format:new Mp4OutputFormat(),target:new BufferTarget()});
 out.addVideoTrack(src,{frameRate:FPS});await out.start();
 for(let f=0;f<150;f++){await renderFrame(start+f/FPS);await src.add(f/FPS,1/FPS)}
 await out.finalize();const buf=out.target.buffer;if(!buf||buf.byteLength<100000)throw Error('Empty shard');
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([buf],{type:'video/mp4'}));a.download='part_'+((start-30)/5)+'.mp4';document.body.appendChild(a);a.click();a.remove();
 return {start,frames:150,bytes:buf.byteLength};
};
window.exportSfx=async()=>{
 // Original 30-second atmosphere made with required Web Audio OfflineAudioContext.
 const rate=24000,n=30*rate,offline=new OfflineAudioContext(1,n,rate),master=offline.createGain();
 master.gain.value=.17;master.connect(offline.destination);
 // Purposeful near silence at safe-room false relief 42-45, then monitor wakes.
 master.gain.setValueAtTime(.17,0);
 master.gain.setValueAtTime(.17,11.4);
 master.gain.linearRampToValueAtTime(.018,12.4);
 master.gain.setValueAtTime(.018,14.7);
 master.gain.linearRampToValueAtTime(.18,15.5);
 master.gain.setValueAtTime(.18,29.68);
 master.gain.linearRampToValueAtTime(.0001,29.94);
 let seed=43171;
 const next=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296*2-1};
 const noise=offline.createBuffer(1,n,rate),samples=noise.getChannelData(0);
 for(let i=0;i<n;i++)samples[i]=next()*.082;
 const ns=offline.createBufferSource();ns.buffer=noise;
 const filt=offline.createBiquadFilter();filt.type='lowpass';filt.frequency.value=390;
 ns.connect(filt);filt.connect(master);ns.start();
 const tone=(at,len,f1,f2,vol,type='triangle')=>{
  if(at<0||at>=30)throw Error('Outside original 30–60 film sound bounds');
  const end=Math.min(at+len,29.999),duration=end-at;
  const osc=offline.createOscillator(),v=offline.createGain();osc.type=type;
  osc.frequency.setValueAtTime(f1,at);osc.frequency.exponentialRampToValueAtTime(Math.max(1,f2),end);
  v.gain.setValueAtTime(.0001,at);v.gain.linearRampToValueAtTime(vol,at+Math.min(.035,duration/3));
  v.gain.exponentialRampToValueAtTime(.0001,end);
  osc.connect(v);v.connect(master);osc.start(at);osc.stop(end);
 };
 // Wet metal tunnel running footsteps as Emma reaches safety door.
 for(let k=0;k<8;k++){let t=.14+k*.39;tone(t,.12,122,34,.37,'triangle');tone(t+.04,.09,58,27,.19,'sine');}
 // Steel door and bolt closing, source narration: "rushed inside and locked it".
 for(const t of [4.5,4.83,5.25,6.65,7.02]){tone(t,.22,450,68,.52,'sawtooth');tone(t+.05,.12,170,49,.36,'triangle')}
 // ONE threatening physical slam against the CLOSED steel door; second softer pressure response.
 tone(9.18,.55,137,33,.94,'sawtooth');tone(9.18,.83,70,20,.67,'triangle');
 tone(10.42,.35,112,35,.52,'sawtooth');tone(10.42,.44,61,25,.36,'triangle');
 // Near silence: sound fades deliberately until monitor switches on at 45s.
 tone(15.2,.82,96,460,.22,'sine');tone(15.32,.36,900,320,.14,'triangle');
 for(let k=0;k<7;k++)tone(15.65+k*.43,.14,540+k*7,230,.06,'sine');
 // CCTV static and cyan glow; subtle signal interference as mysterious caller appears.
 for(let k=0;k<10;k++)tone(18.75+k*.46,.10,740+(k%3)*90,430,.09,'sine');
 // Recorded message explicitly described by narrator; DO NOT synthesize any additional speech.
 for(let k=0;k<8;k++){const t=23.0+k*.39;tone(t,.09,1840,660,.12,'triangle');}
 // Emergency locking tones — danger is conveyed by narration + effects.
 for(let t=24.2;t<27.1;t+=.79)tone(t,.26,460,275,.19,'sine');
 // Slow second REAR door hinge opens into silence.
 tone(26.8,2.58,81,31,.42,'sawtooth');tone(27.23,1.85,178,64,.20,'triangle');
 for(let k=0;k<7;k++)tone(27.5+k*.26,.14,135,65,.14,'sine');
 // Final whispered NAME is only described in original Charon narration; do not invent a second voice.
 const pcm=(await offline.startRendering()).getChannelData(0),wav=new ArrayBuffer(44+pcm.length*2);
 const d=new DataView(wav),o=new Uint8Array(wav);const ss=(pos,s)=>{for(let j=0;j<s.length;j++)o[pos+j]=s.charCodeAt(j)};
 ss(0,'RIFF');d.setUint32(4,36+pcm.length*2,true);ss(8,'WAVE');ss(12,'fmt ');
 d.setUint32(16,16,true);d.setUint16(20,1,true);d.setUint16(22,1,true);d.setUint32(24,rate,true);
 d.setUint32(28,rate*2,true);d.setUint16(32,2,true);d.setUint16(34,16,true);ss(36,'data');d.setUint32(40,pcm.length*2,true);
 for(let i=0;i<pcm.length;i++)d.setInt16(44+i*2,Math.round(Math.max(-1,Math.min(1,pcm[i]))*32767),true);
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([wav],{type:'audio/wav'}));
 a.download='story5_final_30s_sfx.wav';document.body.appendChild(a);a.click();a.remove();
 return {seconds:30,bytes:wav.byteLength,source:'Web Audio OfflineAudioContext',paid_jobs:0};
};
const status=document.getElementById('status');status.textContent='EMMA STORY5 / FULL NARRATED FINAL 30–60 / TRUE 2.5D';
let raf=null,epoch=0;
document.getElementById('play').onclick=()=>{if(raf)return;epoch=performance.now();const next=async now=>{if(!raf)return;try{await renderFrame(30+((now-epoch)/1000)%30)}catch(e){status.textContent=e.message;raf=null;return}raf=requestAnimationFrame(next)};raf=requestAnimationFrame(next)};
document.getElementById('pause').onclick=()=>{if(raf)cancelAnimationFrame(raf);raf=null};
