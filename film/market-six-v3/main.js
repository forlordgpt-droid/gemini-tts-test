import * as THREE from 'three';
import gsap from 'gsap';
import {Output,Mp4OutputFormat,BufferTarget,CanvasSource,Quality} from 'mediabunny';

// Market Six first 30s authored survival-thriller 2D illustrated real-depth footage; only user-locked models. Original native Hunyuan rig retained but never used as Mason, Clara or Jonah.
const W=1920,H=1080,FPS=30,LENGTH=30;
const cuts=[
{id:'THE_FIRST_BANG',start:0,end:1.8,image:0,x0:-.56,x1:.28,y0:.12,y1:-.11,z0:10.25,z1:9.58},
{id:'THE_SHELTER',start:1.8,end:5.4,image:1,x0:.68,x1:-.49,y0:.11,y1:-.095,z0:10.34,z1:9.38},
{id:'NINETEEN_OUTSIDE',start:5.4,end:9.2,image:2,x0:-.64,x1:.51,y0:.10,y1:-.12,z0:10.34,z1:9.28},
{id:'THE_RISING_FLOOD',start:9.2,end:12.5,image:3,x0:.43,x1:-.49,y0:-.14,y1:.13,z0:10.1,z1:9.26},
{id:'ELEVEN_INSIDE',start:12.5,end:16.2,image:4,x0:-.56,x1:.55,y0:.16,y1:-.04,z0:10.32,z1:9.48},
{id:'THE_RED_LATCH',start:16.2,end:20.2,image:5,x0:-.37,x1:.42,y0:.05,y1:-.15,z0:10.3,z1:9.20},
{id:'IMAGINED_FLOOD',start:20.2,end:24.6,image:6,x0:.51,x1:-.46,y0:-.14,y1:.10,z0:10.05,z1:9.18},
{id:'THE_TEN_MINUTE_CHOICE',start:24.6,end:30,image:7,x0:-.49,x1:.34,y0:.11,y1:-.08,z0:10.29,z1:9.16}
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
  const z=depths[j].z;const im=await load('assets/'+names[j]+'_'+i+(j===0?'.jpg':'.webp'));
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
 const u=t-s.start;const life=Math.max(0,Math.min(1,u/.35,(s.end-t)/.3));
 const isExterior=s.image===2||s.image===3;
 const warn=s.image===0||s.image===2||s.image===5||s.image===7;
 // Deterministic story-specific multidepth driving rain, moving wet air and dust.
 for(let k=0;k<63;k++){
  const ox=(rnd(k+188)*2380-130+(t*(isExterior?180:39)*(1+.4*rnd(k+45))))%2380-200;
  const oy=(rnd(k+75)*1310+(t*(isExterior?475:79)*(1+.3*rnd(k+68))))%1310-140;
  ag.strokeStyle=isExterior?'rgba(183,225,249,.21)':'rgba(138,211,237,.065)';
  ag.lineWidth=isExterior?2.3:1.3;
  ag.beginPath();ag.moveTo(ox,oy);ag.lineTo(ox-13,oy+(isExterior?58:19));ag.stroke();
 }
 for(let k=0;k<11;k++){
  const x=-410+((t*(27+k*2)+k*225)%(W+850));
  const y=96+k*91+22*Math.sin(t*.35+k*.67);
  ag.globalAlpha=.016+.013*(k%4);ag.strokeStyle=k%2?'#95d3da':'#ceede5';
  ag.lineWidth=26+6*(k%5);ag.lineCap='round';
  ag.beginPath();ag.moveTo(x-190,y);ag.bezierCurveTo(x+105,y-100,x+240,y+100,x+590,y-22);ag.stroke();
 }
 ag.globalAlpha=1;
 const pulse=Math.pow(.5+.5*Math.sin(t*4.9),6);
 if(warn){
  const grad=g.createLinearGradient(0,0,W,420);
  grad.addColorStop(0,'rgba(245,41,70,'+(.035+.13*pulse)+')');
  grad.addColorStop(1,'rgba(8,199,229,'+(.025+.045*(1-pulse))+')');
  g.fillStyle=grad;g.fillRect(0,0,W,H);
 }
 if(s.image===0){
   const a=Math.min(1,u*3,Math.max(0,(1.7-u)*5));
   if(a>.05)pill('DAY 100  /  MARKET SIX',104,91,a);
   const hit=Math.max(0,1-Math.abs(t-.31)/.21);
   g.fillStyle='rgba(238,246,246,'+(.10*hit)+')';g.fillRect(0,0,W,H);
   g.strokeStyle='rgba(240,111,102,'+(.42*hit)+')';g.lineWidth=10;
   for(let i=0;i<3;i++){g.beginPath();g.ellipse(1160,520,80+i*100+150*hit,80+i*70,0,0,6.283);g.stroke();}
 }
 if(s.image===1){
   // Frosty flood reflection glides up foreground architecture as Mason gauges danger.
   const height=820+Math.sin(t*1.4)*14;
   g.fillStyle='rgba(48,190,217,.055)';g.fillRect(0,height,W,H-height);
   const x=1110+160*Math.sin(t*.6);
   g.strokeStyle='rgba(252,201,119,.33)';g.lineWidth=4;g.beginPath();g.moveTo(x,695);g.lineTo(x+105,660);g.stroke();
 }
 if(s.image===2){
   const a=Math.min(1,(u-.22)*3,Math.max(0,(3.1-u)*2.7));
   if(a>.02)pill('19  /  OUTSIDE',111,91,a);
   for(const at of [6.05,7.12,8.58]){
    const h=Math.max(0,1-Math.abs(t-at)/.22);
    if(h>.001){g.strokeStyle='rgba(250,224,185,'+(h*.42)+')';g.lineWidth=2.5;
      for(let i=0;i<3;i++){g.beginPath();g.ellipse(400,595,70+i*54+(1-h)*62,105+i*60,0,0,6.283);g.stroke();}
    }
   }
 }
 if(s.image===3){
   // Meaningful physically rising imaginary screen-space waterline at exterior.
   const level=1000-Math.min(1,u/(s.end-s.start))*110;
   for(let j=0;j<8;j++){
    const x=(rnd(j+308)*W+t*(60+j*11))%W;
    g.strokeStyle='rgba(132,224,250,'+(.19+.09*(j%3))+')';g.lineWidth=2+(j%3);
    g.beginPath();g.arc(x,level+27*Math.sin(t*1.4+j),30+j*5,Math.PI*1.03,Math.PI*1.93);g.stroke();
   }
   g.save();g.globalAlpha=.7*life;g.strokeStyle='rgba(255,210,144,.55)';g.setLineDash([13,10]);g.lineWidth=2;g.beginPath();g.moveTo(1490,730);g.lineTo(1490,600);g.stroke();g.setLineDash([]);g.restore();
 }
 if(s.image===4){
   const a=Math.min(1,(u-.30)*2.8,Math.max(0,(3.25-u)*2));
   if(a>.03)pill('11  /  INSIDE',110,90,a);
   g.save();g.globalAlpha=.33*a;g.strokeStyle='#f7c471';g.lineWidth=2.5;
   for(let j=0;j<5;j++){g.beginPath();g.roundRect(1440+j*55,143,36,73,7);g.stroke();}
   g.restore();
 }
 if(s.image===5){
   const a=Math.min(1,(u-.3)*2,Math.max(0,(3.8-u)*2.5));
   if(a>.02)pill('RED LATCH  /  FLOOD RISK',101,88,a);
   const cx=1518,cy=460,rad=180+18*Math.sin(t*5);
   g.save();g.globalAlpha=.13+.23*pulse;g.strokeStyle='#ff8580';g.lineWidth=5;
   for(let i=0;i<3;i++){g.beginPath();g.arc(cx,cy,rad+i*75,-.8,1.05);g.stroke();}
   g.restore();
 }
 if(s.image===6){
   // A FLASH-FORWARD OF AN IMAGINED CONSEQUENCE; actual lower shutter is never opened.
   const a=Math.min(1,(u-.35)*2.3,Math.max(0,(4.05-u)*2.7));
   if(a>.04)pill('IF OPENED  /  LOWER STOCKROOM',105,90,a);
   g.save();g.globalAlpha=.26*a;g.strokeStyle='#f99d8b';g.lineWidth=8;g.lineCap='round';
   for(let j=0;j<3;j++){
    const dx=310+j*270+u*59;
    g.beginPath();g.moveTo(dx,770);g.bezierCurveTo(dx+170,620,dx+215,380,dx+440,220);g.stroke();
    g.beginPath();g.moveTo(dx+440,220);g.lineTo(dx+406,228);g.moveTo(dx+440,220);g.lineTo(dx+428,256);g.stroke();
   }
   g.restore();
 }
 if(s.image===7){
   const a=Math.min(1,(u-.55)*1.6,Math.max(0,(5.2-u)*1.9));
   if(a>.04)pill('TEN MINUTES  /  NO SAFE LOWER EXIT',106,89,a);
   const w=420;
   g.save();g.globalAlpha=.28*a;g.fillStyle='rgba(7,27,48,.75)';g.fillRect(1250,875,w,88);
   g.font='700 27px Inter,system-ui,sans-serif';g.fillStyle='#ffe3b0';g.fillText('19 OUTSIDE  |  11 INSIDE',1275,930);
   g.restore();
   // End on the true dilemma, not a claimed resolved rescue.
   if(t>29.55){g.fillStyle='rgba(2,8,17,'+(.60*ease((t-29.55)/.45))+')';g.fillRect(0,0,W,H);}
 }
 const vign=g.createRadialGradient(980,510,290,980,510,1300);
 vign.addColorStop(0,'rgba(2,7,17,0)');vign.addColorStop(1,'rgba(2,7,17,.22)');
 g.fillStyle=vign;g.fillRect(0,0,W,H);
 ambientTex.needsUpdate=true;gfxTex.needsUpdate=true;
}
async function renderFrame(t){
 if(!Number.isFinite(t)||t<0||t>=LENGTH)throw Error('Outside actual first 30s Market Six film: '+t);
 const s=cuts.find(c=>t>=c.start&&t<c.end);if(!s)throw Error('Shot missing at '+t);
 track.seek(t,false);
 let impact=0;for(const at of [.31,6.05,7.12,8.58,15.74,24.60])impact=Math.max(impact,Math.max(0,1-Math.abs(t-at)/.18));
 camera.position.x+=impact*.025*Math.sin(t*94);
 camera.position.y+=impact*.016*Math.cos(t*103);
 camera.lookAt(0,0,0);
 for(let i=0;i<objects.length;i++)for(let j=0;j<3;j++){
  const o=objects[i][j];o.visible=i===s.image;
  if(o.visible){const u=(t-s.start)/(s.end-s.start);
   o.position.x=j===0?.015*Math.sin(t*.31):j===1?.065*Math.sin(t*1.05+.2):.14*Math.sin(t*1.55+.4)+.045*u;
   o.position.y=j===0?0:j===1?.021*Math.sin(t*.78):.035*Math.sin(t*1.14+.2);
   if(s.image===2&&j===1)o.position.x+=.025*Math.sin(t*10);
   if(s.image===4&&j===1)o.position.y+=.015*Math.sin(t*3.2);
   if(s.image===5&&j===1)o.position.x+=.035*Math.sin(t*2.9);
   if(s.image===6&&j===1)o.position.x+=.15*u;
  }
 }
 ambientMesh.position.x=.05*Math.sin(t*.33);overlay(t,s);
 graphicsMesh.position.x=camera.position.x;graphicsMesh.position.y=camera.position.y;
 renderer.render(scene,camera);
 return {time:t,shot:s.id,cameraX:camera.position.x,cameraZ:camera.position.z,farX:objects[s.image][0].position.x,midX:objects[s.image][1].position.x,frontX:objects[s.image][2].position.x};
}
await renderFrame(0);window.ready=true;window.renderFrame=renderFrame;
window.exportSfx=async()=>{
 // User-locked Web Audio OfflineAudioContext: original 30-second story-reactive score.
 const rate=24000,n=30*rate,ctx=new OfflineAudioContext(1,n,rate),master=ctx.createGain();
 master.gain.value=.22;master.connect(ctx.destination);
 let seed=47853;const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return ((seed/4294967296)*2)-1};
 const noise=ctx.createBuffer(1,n,rate),a=noise.getChannelData(0);
 for(let i=0;i<n;i++)a[i]=rand()*.15;
 const ns=ctx.createBufferSource();ns.buffer=noise;
 const low=ctx.createBiquadFilter();low.type='lowpass';low.frequency.value=670;
 ns.connect(low);low.connect(master);ns.start(0);
 const tone=(at,len,f1,f2,v,kind='triangle')=>{
  if(at>=30||at<0)return;
  const end=Math.min(29.999,at+len),o=ctx.createOscillator(),g=ctx.createGain();
  o.type=kind;o.frequency.setValueAtTime(f1,at);o.frequency.exponentialRampToValueAtTime(Math.max(1,f2),end);
  g.gain.setValueAtTime(.0001,at);g.gain.linearRampToValueAtTime(v,at+Math.min(.016,(end-at)/3));g.gain.exponentialRampToValueAtTime(.0001,end);
  o.connect(g);g.connect(master);o.start(at);o.stop(end);
 };
 // Shutter impacts, rain resonance, rising flood pressure, emotional count beats.
 for(const at of [.35,1.24,6.02,7.15,8.61,15.74,25.2]){tone(at,.41,210,27,.72,'sawtooth');tone(at+.035,.59,90,23,.34,'triangle');}
 for(let k=0;k<14;k++){const t=9.15+k*.39;tone(t,.33,109+(k%5)*21,43,.12,'sine');}
 tone(16.35,2.9,64,31,.17,'sawtooth');tone(19.5,1.8,117,45,.15,'triangle');
 for(let k=0;k<19;k++){const t=20.4+k*.19;tone(t,.27,250+rand()*18,37,.12,'sawtooth');}
 for(let k=0;k<8;k++){const t=25.2+k*.53;tone(t,.15,380,240,.11,'sine');}
 tone(28.3,1.69,61,24,.25,'sawtooth');
 const pcm=(await ctx.startRendering()).getChannelData(0),wav=new ArrayBuffer(44+pcm.length*2);
 const dv=new DataView(wav),bytes=new Uint8Array(wav);
 const ss=(pos,s)=>{for(let j=0;j<s.length;j++)bytes[pos+j]=s.charCodeAt(j)};
 ss(0,'RIFF');dv.setUint32(4,36+pcm.length*2,true);ss(8,'WAVE');ss(12,'fmt ');
 dv.setUint32(16,16,true);dv.setUint16(20,1,true);dv.setUint16(22,1,true);dv.setUint32(24,rate,true);dv.setUint32(28,rate*2,true);dv.setUint16(32,2,true);dv.setUint16(34,16,true);ss(36,'data');dv.setUint32(40,pcm.length*2,true);
 for(let i=0;i<pcm.length;i++)dv.setInt16(44+i*2,Math.round(Math.max(-1,Math.min(1,pcm[i]))*32767),true);
 const aTag=document.createElement('a');aTag.href=URL.createObjectURL(new Blob([wav],{type:'audio/wav'}));aTag.download='MARKET_SIX_OFFLINE_WEBAUDIO_SFX.wav';document.body.appendChild(aTag);aTag.click();aTag.remove();
 return {seconds:30,frames:720000,source:'OfflineAudioContext',paid_calls:0};
};
const status=document.getElementById('status');status.textContent='MARKET SIX / DAY 100 / REAL 2.5D';
let raf=null,epoch=0;
document.getElementById('play').onclick=()=>{if(raf!==null)return;epoch=performance.now();const next=async now=>{if(raf===null)return;try{await renderFrame(((now-epoch)/1000)%30)}catch(e){status.textContent=e.message;raf=null;return}raf=requestAnimationFrame(next)};raf=requestAnimationFrame(next)};
document.getElementById('pause').onclick=()=>{if(raf!==null)cancelAnimationFrame(raf);raf=null};
