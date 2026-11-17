import * as THREE from 'three';
import gsap from 'gsap';
import {Output,Mp4OutputFormat,BufferTarget,CanvasSource,Quality} from 'mediabunny';

// FIRST TEN SECONDS ONLY. Same required stack as original Hunyuan source.
// Hunyuan native rig is loaded and tested, not mistaken for a female actor.
const W=1920,H=1080,FPS=30,LENGTH=30;
const cuts=[
 {id:'SUBWAY_GATEWAY',start:10,end:13.05,image:0,x0:-.68,x1:.66,y0:.07,y1:-.10,z0:10.55,z1:9.90},
 {id:'SUBWAY_DESCENT',start:13.05,end:15,image:0,x0:.55,x1:-.22,y0:.08,y1:-.20,z0:10.16,z1:8.86},
 {id:'STAIRS',start:15,end:19.10,image:1,x0:.54,x1:-.55,y0:.18,y1:-.18,z0:10.62,z1:9.49},
 {id:'GATE',start:19.10,end:22.55,image:2,x0:-.58,x1:.43,y0:-.02,y1:.07,z0:10.35,z1:9.53},
 {id:'LOCKED',start:22.55,end:25.70,image:2,x0:.43,x1:-.41,y0:.05,y1:.08,z0:10.27,z1:9.40},
 {id:'TUNNEL',start:25.70,end:30,image:3,x0:-.43,x1:.29,y0:.02,y1:-.08,z0:10.59,z1:9.10}
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
  const a=Math.min(1,(u+.1)*2,Math.max(0,(3.0-u)*2));
  if(a>0)pill('NOAH  /  CALL CONNECTED',105,92,a);
  // Sound-pressure gas lines are distinct editorial graphics, not stock effects.
  g.save();g.strokeStyle='rgba(247,229,111,.19)';g.lineWidth=7;
  for(let k=0;k<3;k++){const x=1450+(k*65)-u*100;g.beginPath();g.moveTo(x,80);g.bezierCurveTo(x-125,380,x+60,670,x-90,1050);g.stroke()}
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
  const a=Math.min(1,u*2,Math.max(0,(3-u)*1.8));
  if(a>0)pill(s.id==='GATE'?'LOCK ENGAGED / NO ACCESS':'ANOTHER ROUTE / BEHIND YOU',112,92,a);
  // Each gate shake has short, restrained metallic-collision ripples.
  const tt=t-19.42;
  const impact=Math.max(0,1-Math.abs((tt%1.12)-.10)/.25);
  if(impact>0){
   g.save();g.globalAlpha=.17*impact;g.strokeStyle='#f5bec5';g.lineWidth=5;
   for(let k=0;k<3;k++){g.beginPath();g.ellipse(964,565,70+k*40+impact*16,150+k*35,0,0,6.283);g.stroke()}
   g.restore();
  }
 }
 if(tunnel){
  const bang=[26.7,27.65,28.4,29.12,29.65];
  for(const at of bang){
   const d=t-at;
   if(d>=0&&d<.55){
    const a=(1-d/.55)*(.18+.10*(at>28));
    g.strokeStyle='rgba(255,119,90,'+a+')';
    for(let k=0;k<3;k++){g.lineWidth=2.5+k;g.beginPath();g.ellipse(1080,530,175+d*570+k*72,160+d*430+k*60,0,0,6.283);g.stroke()}
   }
  }
  const breath=.05+.05*Math.pow(Math.sin((t-25)*1.4),2);
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
 // Menacing offscreen metal bangs at 26.7–30 absolute.
 for(const at of [16.70,17.65,18.4,19.12,19.65]){
  tone(at,.28,130,39,.95,'sawtooth');
  tone(at,.43,62,22,.70,'triangle');
  tone(at+.06,.25,890,126,.16,'sine');
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
const status=document.getElementById('status');status.textContent='THE LAST SAFE ROOM | continuation 10–30 seconds | cinematic 2.5D';
let raf=null,epoch=0;
document.getElementById('play').onclick=()=>{if(raf)return;epoch=performance.now();const next=async now=>{if(!raf)return;try{await renderFrame(10+((now-epoch)/1000)%20)}catch(e){status.textContent=e.message;raf=null;return}raf=requestAnimationFrame(next)};raf=requestAnimationFrame(next)};
document.getElementById('pause').onclick=()=>{if(raf)cancelAnimationFrame(raf);raf=null};
