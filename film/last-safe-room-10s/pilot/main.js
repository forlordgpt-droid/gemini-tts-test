import * as THREE from 'three';
import gsap from 'gsap';
import {Output,Mp4OutputFormat,BufferTarget,CanvasSource,Quality} from 'mediabunny';

// FIRST TEN SECONDS ONLY. Same required stack as original Hunyuan source.
// Hunyuan native rig is loaded and tested, not mistaken for a female actor.
const W=1920,H=1080,FPS=30,LENGTH=10;
const cuts=[
 {id:'STREET',start:0,end:3.25,image:0,x0:-.57,x1:.64,y0:.12,y1:-.075,z0:10.60,z1:10.12},
 {id:'FLEE',start:3.25,end:6.8,image:1,x0:.54,x1:-.60,y0:-.07,y1:.075,z0:10.40,z1:9.66},
 {id:'REACTION',start:6.8,end:9.15,image:2,x0:-.34,x1:.38,y0:.06,y1:-.05,z0:10.30,z1:9.58},
 {id:'PHONE',start:9.15,end:10,image:2,x0:.41,x1:.11,y0:.08,y1:-.06,z0:9.84,z1:8.83}
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
for(let i=0;i<3;i++){
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
 // Story-appropriate drifting contaminated gas, at a distinct plane.
 for(let k=0;k<15;k++){
  const y=120+k*67+18*Math.sin(t*.8+k);
  const x=-550+(t*(90+k%4*21)+k*161)%(W+800);
  ag.globalAlpha=.035+((k%5)/5)*.031;
  ag.strokeStyle=k%3===0?'#fff5b4':'#d7d74e';ag.lineWidth=37+k%4*18;ag.lineCap='round';
  ag.beginPath();ag.moveTo(x-150,y+35);ag.bezierCurveTo(x+45,y-100,x+120,y+105,x+330,y-25);ag.stroke();
 }
 ag.globalAlpha=1;
 for(let k=0;k<41;k++){
  let x=(rnd(k)*2070+t*(23+20*rnd(k+70)))%2070-100;
  let y=95+rnd(k+41)*900+13*Math.sin(t*.8+k);
  ag.fillStyle='rgba(249,225,135,'+(.09+rnd(k+91)*.16)+')';
  ag.beginPath();ag.ellipse(x,y,1.5+rnd(k+3)*2.2,1+rnd(k+8)*1.2,.4,0,6.29);ag.fill();
 }
 const fade=g.createLinearGradient(0,H*.64,0,H);
 fade.addColorStop(0,'rgba(15,26,43,0)');fade.addColorStop(1,'rgba(6,10,20,.20)');
 g.fillStyle=fade;g.fillRect(0,0,W,H);
 if(s.id==='STREET'){
  let alpha=Math.min(1,u/.30,Math.max(0,(2.2-u)/.5));
  if(alpha>0)pill('EXPOSURE ZONE / DOWNTOWN',108,92,alpha);
 }
 if(s.id==='FLEE'){
  g.save();g.strokeStyle='rgba(235,234,80,.23)';g.lineWidth=9;
  for(let k=0;k<4;k++){const x=200+Math.sin(u*2.7+k*.7)*32+k*55;g.beginPath();g.moveTo(x,780);g.bezierCurveTo(x-200,400,x+190,300,x-60,120);g.stroke()}
  g.restore();
 }
 if(s.id==='REACTION'){
  const alpha=Math.min(1,(u-.38)*2,Math.max(0,(2.05-u)*2));
  if(alpha>0)pill('AIR QUALITY / CRITICAL',112,95,alpha);
 }
 if(s.id==='PHONE'){
  const p=ease(u/.36),wiggle=Math.sin(u*68)*7;
  g.save();g.translate(wiggle,0);g.globalAlpha=p;
  const xx=1225,yy=260;g.shadowColor='rgba(12,18,23,.65)';g.shadowBlur=36;
  g.fillStyle='rgba(12,26,41,.91)';g.beginPath();g.roundRect(xx,yy,550,220,35);g.fill();g.shadowBlur=0;
  g.lineWidth=2;g.strokeStyle='#c5e6b3';g.stroke();
  text('INCOMING CALL',xx+37,yy+52,26,'#d0efd1',730);text('NOAH',xx+37,yy+130,65,'#f4f8f5',810);
  g.strokeStyle='rgba(140,244,185,.82)';g.lineWidth=5;
  for(let k=0;k<2;k++){g.beginPath();g.arc(xx+482,yy+142,46+k*27+Math.sin(t*21)*4,-1.08,1.1);g.stroke()}
  g.restore();
 }
 ambientTex.needsUpdate=true;gfxTex.needsUpdate=true;
}
async function renderFrame(t){
 if(!Number.isFinite(t)||t<0||t>=LENGTH)throw Error('Outside 0–10 second review '+t);
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
await renderFrame(0);window.ready=true;window.renderFrame=renderFrame;
window.exportShard=async start=>{
 if(start!==0&&start!==5)throw Error('Only 0–5 and 5–10 approved');
 const src=new CanvasSource(stage,{codec:'avc',quality:new Quality({bitrate:9500000})});
 const out=new Output({format:new Mp4OutputFormat(),target:new BufferTarget()});
 out.addVideoTrack(src,{frameRate:FPS});await out.start();
 for(let f=0;f<150;f++){await renderFrame(start+f/FPS);await src.add(f/FPS,1/FPS)}
 await out.finalize();const buf=out.target.buffer;if(!buf||buf.byteLength<100000)throw Error('Empty shard');
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([buf],{type:'video/mp4'}));a.download='part_'+(start/5)+'.mp4';document.body.appendChild(a);a.click();a.remove();
 return {start,frames:150,bytes:buf.byteLength};
};
window.exportSfx=async()=>{
 const rate=24000,n=10*rate,offline=new OfflineAudioContext(1,n,rate),master=offline.createGain();master.gain.value=.20;master.connect(offline.destination);
 let seed=18371;const next=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296*2-1};
 const noise=offline.createBuffer(1,n,rate),samples=noise.getChannelData(0);
 for(let i=0;i<n;i++)samples[i]=next()*.17;
 const nsrc=offline.createBufferSource();nsrc.buffer=noise;
 const filter=offline.createBiquadFilter();filter.type='lowpass';filter.frequency.value=420;nsrc.connect(filter);filter.connect(master);nsrc.start();
 const tone=(at,len,f1,f2,vol,type)=>{
  const osc=offline.createOscillator(),v=offline.createGain();osc.type=type;osc.frequency.setValueAtTime(f1,at);osc.frequency.exponentialRampToValueAtTime(Math.max(1,f2),at+len);
  v.gain.setValueAtTime(.0001,at);v.gain.linearRampToValueAtTime(vol,at+Math.min(.045,len/3));v.gain.exponentialRampToValueAtTime(.0001,at+len);
  osc.connect(v);v.connect(master);osc.start(at);osc.stop(at+len);
 };
 for(let i=0;i<11;i++)tone(.9+i*.76,.18,96,46,.47,'triangle');
 tone(0,9.5,67,48,.12,'sawtooth');
 for(let i=0;i<5;i++){const at=9.12+i*.16;tone(at,.12,670,760,.46,'triangle');tone(at,.12,480,530,.19,'sine')}
 const pcm=(await offline.startRendering()).getChannelData(0),wav=new ArrayBuffer(44+pcm.length*2),d=new DataView(wav),o=new Uint8Array(wav);
 const ss=(pos,s)=>{for(let j=0;j<s.length;j++)o[pos+j]=s.charCodeAt(j)};
 ss(0,'RIFF');d.setUint32(4,36+pcm.length*2,true);ss(8,'WAVE');ss(12,'fmt ');
 d.setUint32(16,16,true);d.setUint16(20,1,true);d.setUint16(22,1,true);d.setUint32(24,rate,true);d.setUint32(28,rate*2,true);
 d.setUint16(32,2,true);d.setUint16(34,16,true);ss(36,'data');d.setUint32(40,pcm.length*2,true);
 for(let i=0;i<pcm.length;i++)d.setInt16(44+i*2,Math.round(Math.max(-1,Math.min(1,pcm[i]))*32767),true);
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([wav],{type:'audio/wav'}));a.download='sfx_10.wav';document.body.appendChild(a);a.click();a.remove();return {seconds:10,bytes:wav.byteLength};
};
const status=document.getElementById('status');status.textContent='THE LAST SAFE ROOM | first 10 seconds | cinematic 2.5D';
let raf=null,epoch=0;
document.getElementById('play').onclick=()=>{if(raf)return;epoch=performance.now();const next=async now=>{if(!raf)return;try{await renderFrame(((now-epoch)/1000)%10)}catch(e){status.textContent=e.message;raf=null;return}raf=requestAnimationFrame(next)};raf=requestAnimationFrame(next)};
document.getElementById('pause').onclick=()=>{if(raf)cancelAnimationFrame(raf);raf=null};
