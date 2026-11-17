import * as THREE from 'three';
import gsap from 'gsap';
import {Output,Mp4OutputFormat,BufferTarget,CanvasSource,Quality} from 'mediabunny';

// Story5 authored narration-first 10–30s continuation; use unchanged approved 0–10 master.
// Hunyuan native rig is loaded and tested, not mistaken for a female actor.
const W=1920,H=1080,FPS=30,LENGTH=30;
const cuts=[
 {id:'CITY_ESCAPE',start:10,end:13.45,image:0,x0:-.57,x1:.54,y0:.13,y1:-.09,z0:10.62,z1:9.96},
 {id:'CALL_RING',start:13.45,end:15,image:0,x0:.38,x1:-.19,y0:-.04,y1:.12,z0:9.97,z1:9.22},
 {id:'DESCENT',start:15,end:18.85,image:1,x0:.53,x1:-.46,y0:.18,y1:-.16,z0:10.56,z1:9.34},
 {id:'LOCKED_GATE',start:18.85,end:22.45,image:2,x0:-.56,x1:.38,y0:-.01,y1:.08,z0:10.42,z1:9.53},
 {id:'DARK_FOOTSTEPS',start:22.45,end:25.45,image:3,x0:.45,x1:-.36,y0:.06,y1:-.11,z0:10.54,z1:9.82},
 {id:'SERVICE_TUNNEL',start:25.45,end:30,image:3,x0:-.32,x1:.39,y0:-.09,y1:.11,z0:9.91,z1:9.12}
]
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
for(let i=0;i<4;i++){
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
 const street=s.image===0,stairs=s.image===1,gate=s.image===2,tunnel=s.image===3;
 const yell=street?1:stairs?.30:.05;
 // Story-motivated atmospheric depth, painted imagery remains primary.
 for(let k=0;k<14;k++){
  const phase=(t-10)*(.6+(k%3)*.15)+k*.92;
  const y=160+k*63+11*Math.sin(phase*.7),x=-550+(phase*105+k*205)%(W+900);
  ag.globalAlpha=yell*(.025+.02*(k%4));
  ag.strokeStyle=k%3===0?'#f9df68':'#e8e7b2';ag.lineWidth=30+(k%5)*18;ag.lineCap='round';
  ag.beginPath();ag.moveTo(x-240,y+35);ag.bezierCurveTo(x+50,y-92,x+100,y+85,x+470,y-20);ag.stroke();
 }
 ag.globalAlpha=1;
 for(let k=0;k<46;k++){
  const x=(rnd(k)*2110+(t-10)*(24+32*rnd(k+70)))%2110-100;
  const y=80+rnd(k+40)*940+12*Math.sin(t*.7+k);
  const a=(street?.16:stairs?.12:gate?.10:.07)*(.4+rnd(k+82)*.7);
  ag.fillStyle=street?'rgba(244,234,130,'+a+')':'rgba(174,223,230,'+a+')';
  ag.beginPath();ag.ellipse(x,y,1.1+rnd(k+5)*2.6,1.4+rnd(k+7)*1.8,0,0,6.283);ag.fill();
 }
 if(!street){
  const pulse=.04+.12*Math.pow(Math.max(0,Math.cos(t*5.6)),14);
  const beam=g.createLinearGradient(W*.12,0,W*.88,H);
  beam.addColorStop(0,'rgba(237,44,50,0)');
  beam.addColorStop(.48,'rgba(230,34,57,'+pulse+')');
  beam.addColorStop(1,'rgba(237,44,50,0)');
  g.fillStyle=beam;g.fillRect(0,0,W,H);
 }
 if(street){
  const alpha=Math.min(1,(u+.13)*1.8,Math.max(0,(s.end-t)*2));
  if(s.id==='CITY_ESCAPE' && alpha>.05)pill('EVACUATION / EXIT ROUTE',109,91,alpha*.78);
  // A real phone rings ONLY at the original story beat around 13.45 seconds, caller identity unknown.
  if(s.id==='CALL_RING'){
   const a=Math.min(1,Math.max(0,u*2.3),Math.max(0,(15-t)*2.8));
   if(a>0){
    g.save();g.globalAlpha=a;
    g.fillStyle='rgba(6,22,37,.83)';g.strokeStyle='rgba(190,241,218,.54)';g.lineWidth=2;
    g.beginPath();g.roundRect(115,95,410,126,20);g.fill();g.stroke();
    text('INCOMING CALL',145,140,24,'#c3e3d8',690);
    text('UNKNOWN',145,195,42,'#ffffff',790);
    g.strokeStyle='rgba(168,252,218,.67)';
    for(let k=0;k<3;k++){g.lineWidth=3.1-k*.55;g.beginPath();g.arc(970,483,35+k*24+4*Math.sin(30*t),-.95,1.0);g.stroke();}
    g.restore();
   }
  }
  // Gas creep is tied to the road texture and perspective, not a decorative slideshow.
  g.save();g.strokeStyle='rgba(247,229,111,.15)';g.lineWidth=5;
  for(let k=0;k<3;k++){const x=1300+k*62-u*66;g.beginPath();g.moveTo(x,120);g.bezierCurveTo(x-130,350,x+65,670,x-120,1020);g.stroke()}
  g.restore();
 }
 if(stairs){
  let a=Math.min(1,u*3,Math.max(0,(2.4-u)*2));
  if(a>0)pill('EMERGENCY LIGHTING / LOWER LEVEL',112,92,a);
  // Moving sweep from alarms across illustrated walls and stair treads.
  g.fillStyle='rgba(249,52,58,'+(.025+.035*Math.pow(Math.max(0,Math.sin(t*11)),10))+')';
  g.fillRect(0,0,W,H);
 }
 if(gate){
  const a=Math.min(1,u*2.1,Math.max(0,(s.end-t)*2.1));
  if(a>.04)pill('MAIN SECURITY GATE / LOCKED',108,90,a);
  // A restrained impact ring follows Emma's desperate pull, not imaginary spoken dialogue.
  const p=19.46;
  const impact=Math.max(0,1-Math.abs(t-p)/.46);
  if(impact>0){
   g.save();g.globalAlpha=.16*impact;g.strokeStyle='#f5bec5';g.lineWidth=4;
   for(let k=0;k<3;k++){g.beginPath();g.ellipse(1030,590,95+k*39+impact*15,140+k*34,0,0,6.283);g.stroke()}
   g.restore();
  }
 }
 if(tunnel){
  // Mysterious HEAVY FOOTSTEPS advance from the darkness before Emma escapes.
  // Metallic banging from the OLD story4 must never appear here.
  if(s.id==='DARK_FOOTSTEPS'){
   for(const at of [22.7,23.24,23.74,24.18,24.59,25.0]){
    const delta=t-at;
    if(delta>=0&&delta<.43){
     const a=(1-delta/.43)*.21;
     g.save();g.strokeStyle='rgba(176,216,228,'+a+')';g.lineWidth=3;
     for(let j=0;j<3;j++){g.beginPath();g.ellipse(965,542,50+delta*220+j*34,76+delta*125+j*26,0,0,6.283);g.stroke()}
     g.restore();
    }
   }
  }else{
   const a=Math.min(.35,(t-s.start)*.10);
   g.save();g.globalAlpha=a;g.strokeStyle='rgba(178,244,219,.76)';g.lineWidth=5;
   for(let j=0;j<3;j++){const y=712+j*62;g.beginPath();g.moveTo(300,y+20);g.lineTo(380+(t-s.start)*31,y);g.stroke()}
   g.restore();
  }
  // Directional darkness, red hazard lamps and slow moving smoke throughout the tunnel.
  const breath=.04+.06*Math.pow(Math.sin((t-22)*1.38),2);
  g.fillStyle='rgba(0,7,20,'+breath+')';g.fillRect(0,0,W,H);
 }
 // Subtle editorial grade/dimensional vignette for focus.
 const grad=g.createRadialGradient(930,480,440,930,480,1270);
 grad.addColorStop(0,'rgba(2,9,22,0)');grad.addColorStop(1,'rgba(2,9,22,.18)');
 g.fillStyle=grad;g.fillRect(0,0,W,H);
 ambientTex.needsUpdate=true;gfxTex.needsUpdate=true;
}
async function renderFrame(t){
 if(!Number.isFinite(t)||t<10||t>=LENGTH)throw Error('Outside 10–30 second continuation '+t);
 const s=cuts.find(c=>t>=c.start&&t<c.end);if(!s)throw Error('Shot missing');
 track.seek(t,false);camera.lookAt(0,0,0);
 for(let i=0;i<objects.length;i++)for(let j=0;j<3;j++){
  const o=objects[i][j];o.visible=i===s.image;
  if(o.visible){o.position.x=j===0?0:j===1?.07*Math.sin(t*1.34+.35):.12*Math.sin(t*1.93+.6);
   o.position.y=j===1?.02*Math.sin(t*9):j===2?.038*Math.sin(t*1.14):0;}
 }
 ambientMesh.position.x=.04*Math.sin(t*.35);overlay(t,s);
 graphicsMesh.position.x=camera.position.x;graphicsMesh.position.y=camera.position.y;
 renderer.render(scene,camera);
 return {t,shot:s.id,cameraX:camera.position.x,cameraZ:camera.position.z,farX:objects[s.image][0].position.x,midX:objects[s.image][1].position.x,frontX:objects[s.image][2].position.x};
}
await renderFrame(10);window.ready=true;window.renderFrame=renderFrame;
window.exportShard=async start=>{
 if(![10,15,20,25].includes(start))throw Error('Expected 10–15, 15–20, 20–25, or 25–30');
 const src=new CanvasSource(stage,{codec:'avc',quality:new Quality({bitrate:9500000})});
 const out=new Output({format:new Mp4OutputFormat(),target:new BufferTarget()});
 out.addVideoTrack(src,{frameRate:FPS});await out.start();
 for(let f=0;f<150;f++){await renderFrame(start+f/FPS);await src.add(f/FPS,1/FPS)}
 await out.finalize();const buf=out.target.buffer;if(!buf||buf.byteLength<100000)throw Error('Empty shard');
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([buf],{type:'video/mp4'}));a.download='part_'+((start-10)/5)+'.mp4';document.body.appendChild(a);a.click();a.remove();
 return {start,frames:150,bytes:buf.byteLength};
};
window.exportSfx=async()=>{
 const rate=24000,n=20*rate,offline=new OfflineAudioContext(1,n,rate),master=offline.createGain();
 master.gain.value=.24;master.connect(offline.destination);
 let seed=91351;const next=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296*2-1};
 const noise=offline.createBuffer(1,n,rate),samples=noise.getChannelData(0);
 for(let i=0;i<n;i++)samples[i]=next()*.095;
 const ns=offline.createBufferSource();ns.buffer=noise;
 const filt=offline.createBiquadFilter();filt.type='lowpass';filt.frequency.value=340;
 ns.connect(filt);filt.connect(master);ns.start();
 const tone=(at,len,f1,f2,vol,type='triangle')=>{
  if(at<0||at>=20)throw Error('Out of audio bounds');
  const end=Math.min(at+len,19.998),duration=end-at;
  const osc=offline.createOscillator(),v=offline.createGain();osc.type=type;
  osc.frequency.setValueAtTime(f1,at);osc.frequency.exponentialRampToValueAtTime(Math.max(1,f2),end);
  v.gain.setValueAtTime(.0001,at);v.gain.linearRampToValueAtTime(vol,at+Math.min(.025,duration/3));
  v.gain.exponentialRampToValueAtTime(.0001,end);
  osc.connect(v);v.connect(master);osc.start(at);osc.stop(end);
 };
 // Sidewalk and subway footsteps accelerate with perspective.
 for(let i=0;i<29;i++){
  const at=.30+i*.43;if(at>10.9)break;
  tone(at,.084,104,40,(i<13?.35:.45),'triangle');
  tone(at,.058,55,36,.22,'sine');
 }
 // Caution alarms at underground threshold; no generic music-loop substitute.
 for(let at=5.0;at<14.8;at+=1.08)tone(at,.17,360,432,.16,'sine');
 // Gate hand pull and mechanical rattle around 9.5–13.2 relative to 10s.
 for(const at of [9.60,9.79,10.30,10.51,11.0,11.29,12.1]){
  tone(at,.13,160,44,.75,'sawtooth');tone(at+.07,.12,570,130,.26,'triangle');
 }
 // The phone rings, then subsides when the mysterious caller is reported by the narrator.
 for(let i=0;i<6;i++){
  const at=3.55+i*.18;
  tone(at,.112,724,800,.45,'triangle');
  tone(at,.112,480,535,.19,'sine');
 }
 // Unseen heavy footsteps approach from the station darkness, not metallic banging.
 for(let i=0;i<8;i++){
  const at=12.76+i*.385;
  tone(at,.19,115-(i%3)*7,36,.52+i*.031,'triangle');
  tone(at+.05,.11,61,29,.24+i*.012,'sine');
 }
 // Emma bolts down the maintenance tunnel as the footsteps follow.
 for(let i=0;i<10;i++){
  const at=15.7+i*.41;
  if(at>=19.7)break;
  tone(at,.10,145,43,.42,'triangle');
  tone(at+.03,.08,60,34,.23,'sine');
 }
 const pcm=(await offline.startRendering()).getChannelData(0),wav=new ArrayBuffer(44+pcm.length*2);
 const d=new DataView(wav),o=new Uint8Array(wav);const ss=(pos,s)=>{for(let j=0;j<s.length;j++)o[pos+j]=s.charCodeAt(j)};
 ss(0,'RIFF');d.setUint32(4,36+pcm.length*2,true);ss(8,'WAVE');ss(12,'fmt ');
 d.setUint32(16,16,true);d.setUint16(20,1,true);d.setUint16(22,1,true);d.setUint32(24,rate,true);
 d.setUint32(28,rate*2,true);d.setUint16(32,2,true);d.setUint16(34,16,true);ss(36,'data');d.setUint32(40,pcm.length*2,true);
 for(let i=0;i<pcm.length;i++)d.setInt16(44+i*2,Math.round(Math.max(-1,Math.min(1,pcm[i]))*32767),true);
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([wav],{type:'audio/wav'}));
 a.download='sfx_20.wav';document.body.appendChild(a);a.click();a.remove();
 return {seconds:20,bytes:wav.byteLength};
};
const status=document.getElementById('status');status.textContent='EMMA STORY5 / NARRATED 10–30 / CINEMATIC 2.5D';
let raf=null,epoch=0;
document.getElementById('play').onclick=()=>{if(raf)return;epoch=performance.now();const next=async now=>{if(!raf)return;try{await renderFrame(10+((now-epoch)/1000)%20)}catch(e){status.textContent=e.message;raf=null;return}raf=requestAnimationFrame(next)};raf=requestAnimationFrame(next)};
document.getElementById('pause').onclick=()=>{if(raf)cancelAnimationFrame(raf);raf=null};
