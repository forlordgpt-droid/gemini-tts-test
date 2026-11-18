import * as THREE from 'three';
import gsap from 'gsap';
import {Output,Mp4OutputFormat,BufferTarget,CanvasSource,Quality} from 'mediabunny';
// MARKET SIX 15-MINUTE FULL FILM - chapter-specific ORIGINAL PAINTINGS, 2.5D depth, author-approved model/rig locks.
// Browser only renders one chapter at a time: no generic flat background. Real multi-plane reconstructed story art.
// Story world character portraits are AI-generated 2D illustrations, NOT native Hunyuan impersonations.
const W=1920,H=1080,FPS=30,stage=document.getElementById('stage');
const config=await (await fetch('scene_manifest.json')).json();
if(config.image_model!=='gpt-image-2.5-lower'||config.speech_model!=='google/gemini-3-8-flash-tts')throw Error('MANDATORY model lock mismatch');
if(!Array.isArray(config.shots)||config.shots.length<5||config.shots.length>10)throw Error('Chapter scene manifest invalid');
const SHOTS=config.shots,START=config.start_sec,END=config.end_sec;
const renderer=new THREE.WebGLRenderer({canvas:stage,antialias:true,preserveDrawingBuffer:true,alpha:false});
renderer.setPixelRatio(1);renderer.setSize(W,H,false);renderer.setClearColor(0x051323);
renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.NoToneMapping;
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(2*Math.atan(.45)*180/Math.PI,16/9,.1,100);
const cine=gsap.timeline({paused:true});
const paths=[
 [-.57,.40,.09,-.12,10.65,9.48], [.49,-.61,-.09,.10,10.43,9.35],
 [-.41,.43,.12,-.11,10.68,9.18], [.61,-.35,-.12,.08,10.36,9.35],
 [-.63,.53,-.11,.07,10.59,9.31], [.42,-.45,.14,-.10,10.73,9.16],
 [-.32,.61,.08,-.13,10.40,9.24], [.47,-.56,-.08,.13,10.57,9.38],
 [-.52,.37,.10,-.07,10.61,9.22]
];
for(let i=0;i<SHOTS.length;i++){
 const shot=SHOTS[i],v=paths[(i+config.chapter*2)%paths.length];
 const duration=shot.end_sec-shot.start_sec;
 if(!(duration>1.9))throw Error('Shot duration invalid '+shot.key);
 const midpoint=duration*.54;
 const pos={x0:v[0],x1:v[1],y0:v[2],y1:v[3],z0:v[4],z1:v[5]};
 cine.set(camera.position,{x:pos.x0,y:pos.y0,z:pos.z0},shot.start_sec);
 cine.to(camera.position,{x:.21*pos.x0+.79*pos.x1,y:pos.y0*.31+pos.y1*.69,z:(pos.z0+pos.z1)/2+.07,duration:midpoint,ease:'power2.inOut'},shot.start_sec);
 cine.to(camera.position,{x:pos.x1,y:pos.y1,z:pos.z1,duration:duration-midpoint,ease:'power3.inOut'},shot.start_sec+midpoint);
}
const depths=[{z:-4,order:0},{z:-.35,order:2},{z:2.2,order:4}];
function makePlane(tex,z,w,order){
 const mat=new THREE.MeshBasicMaterial({map:tex,transparent:true,depthTest:false,depthWrite:false,toneMapped:false,side:THREE.DoubleSide});
 const mesh=new THREE.Mesh(new THREE.PlaneGeometry(w,w*9/16),mat);mesh.position.z=z;mesh.renderOrder=order;scene.add(mesh);return mesh;
}
async function loadImage(url){const img=new Image();img.decoding='async';img.src=url;await img.decode();return img;}
function tex(img){const t=new THREE.Texture(img);t.needsUpdate=true;t.colorSpace=THREE.SRGBColorSpace;t.minFilter=THREE.LinearFilter;return t;}
const objects=[];
for(let i=0;i<SHOTS.length;i++){
 const layer=[];
 for(let j=0;j<3;j++){
  const name=['far','mid','front'][j],ext=j===0?'jpg':'webp';
  const image=await loadImage('assets/'+name+'_'+i+'.'+ext),z=depths[j].z;
  const m=makePlane(tex(image),z,(10-z)*1.6*1.22,depths[j].order);
  layer.push(m);
 }
 objects.push(layer);
}
if(typeof window.Hunyuan2D!=='function'||typeof window.HunyuanArt?.svg!=='function')throw Error('MANDATORY ORIGINAL art.js + engine.js missing');
const verifyOnly=new window.Hunyuan2D({id:'Hunyuan',x:850,y:820,scale:.75,view:'quarterRight'});
if(!verifyOnly.poseAt(0)||!verifyOnly.svgAt(0))throw Error('Original 2D authored rig failed integration regression');
const ambient=document.createElement('canvas');ambient.width=W;ambient.height=H;
const ag=ambient.getContext('2d',{alpha:true}),at=new THREE.CanvasTexture(ambient);at.colorSpace=THREE.SRGBColorSpace;
const mistPlane=makePlane(at,-.80,(10.8)*1.6*1.22,3);
const gfx=document.createElement('canvas');gfx.width=W;gfx.height=H;
const g=gfx.getContext('2d',{alpha:true}),gt=new THREE.CanvasTexture(gfx);gt.colorSpace=THREE.SRGBColorSpace;
const graphicsPlane=makePlane(gt,4.1,(10-4.1)*1.6*1.22,9);
const clamp=x=>Math.max(0,Math.min(1,x)),smooth=x=>{x=clamp(x);return x*x*(3-2*x)};
const rnd=i=>((Math.imul(i+619,1664525)+1013904223)>>>0)/4294967295;
const xmlSanitize=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const graphics=[];
for(let i=0;i<SHOTS.length;i++){
  const sh=SHOTS[i],keyword=(sh.editorial_label||'SURVIVAL / BELLPORT').toUpperCase();
  const title=String(sh.day||config.day||'MARKET SIX').slice(0,43).toUpperCase();
  // The SVG is meaningful editorial information, never used as a background painting.
  const svg='<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080"><rect x="97" y="88" rx="11" width="520" height="49" fill="#06152b" fill-opacity=".77" stroke="#b5d6e2" stroke-opacity=".59"/><path d="M 117 115 L 150 115 M 167 115 L 198 115" stroke="#ffb281" stroke-width="4" stroke-linecap="round"/><text x="217" y="120" font-size="21" font-weight="700" font-family="Inter,Arial,sans-serif" fill="#f5e4cc">'+xmlSanitize(title)+'</text><text x="115" y="170" font-size="19" font-weight="600" font-family="Inter,Arial,sans-serif" fill="#b9e3e6">'+xmlSanitize(keyword.slice(0,50))+'</text></svg>';
  const img=new Image();img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);await img.decode();graphics.push(img);
}
function motif(shot){const d=(shot.description+' '+shot.day).toLowerCase();
 if(/rain|flood|water|river|storm|barrier|container|wave|roof|bridge|puddle/.test(d))return 'WATER';
 if(/radio|signal|camera|screen|monitor|light|flash|alert|phone|clock|torch/.test(d))return 'SIGNAL';
 if(/fire|generator|smoke|heat|freeze|freezer|ice|flicker/.test(d))return 'ENERGY';
 if(/shelf|ration|can|count|food|bean|ledger|bottle|number|inventory/.test(d))return 'RESOURCE';
 if(/clara|jonah|mason|hand|face|fear|brother|survivor|help|sick/.test(d))return 'PEOPLE';
 return 'MYSTERY';
}
function over(t,shot,index){
 ag.clearRect(0,0,W,H);g.clearRect(0,0,W,H);
 const u=t-shot.start_sec,life=clamp(Math.min(u/.22,(shot.end_sec-t)/.22));
 const d=motif(shot);
 const outside=d==='WATER';
 // Near-mid ambient wind and rain: absolute-time deterministic. Distinct from three original painted planes.
 const count=outside?84:40;
 for(let k=0;k<count;k++){
  const x=((rnd(k+index*331)*2430+t*(outside?155:43)*(1+rnd(k+73)))%2420)-190;
  const y=((rnd(k+23+index*103)*1320+t*(outside?487:91)*(1+rnd(k+25)))%1320)-130;
  ag.strokeStyle=outside?'rgba(175,220,247,.19)':'rgba(201,225,231,.056)';
  ag.lineWidth=outside?2.1:1.25;ag.beginPath();ag.moveTo(x,y);ag.lineTo(x-19,y+(outside?67:23));ag.stroke();
 }
 for(let k=0;k<9;k++){
  const x=((t*(22+k*3)+k*239)%(W+1100))-540, y=82+k*115+24*Math.sin(t*.47+k);
  ag.globalAlpha=.017+(k%4)*.008;
  ag.strokeStyle=k%2?'#70d3dc':'#ffe0bd';ag.lineWidth=28+k%5*9;ag.lineCap='round';
  ag.beginPath();ag.moveTo(x-220,y);ag.bezierCurveTo(x+50,y-65,x+240,y+90,x+510,y-17);ag.stroke();
 }
 ag.globalAlpha=1;
 // Branded, modern, brief editorial SVG information, fade away rather than persistent subtitles.
 const titleAlpha=Math.min(1,u*3,Math.max(0,(2.06-u)*2.6));
 if(titleAlpha>.01){g.save();g.globalAlpha=titleAlpha*.88;g.drawImage(graphics[index],0,0);g.restore();}
 const pulse=Math.pow(.5+.5*Math.sin(t*4.7+index),5);
 if(d==='WATER'){
  const bottom=875-22*Math.sin(t*.85+index),phase=u/(shot.end_sec-shot.start_sec);
  g.strokeStyle='rgba(101,216,249,'+(.15+life*.17)+')';g.lineWidth=2.3;
  for(let j=0;j<10;j++){
   const x=(rnd(j+index*67)*2100+t*(41+j*4))%2150-130;
   g.beginPath();g.ellipse(x,bottom+Math.sin(t+j)*19,45+j%5*19,7,0,0,6.283);g.stroke();
  }
  if(/danger|crack|flood|high water|surge|under|failure/.test(shot.description.toLowerCase())){
   g.save();g.globalAlpha=life*.22;g.strokeStyle='#fb8f78';g.lineWidth=5;
   const xx=1610+12*Math.sin(t*1.0);g.beginPath();g.moveTo(xx,680);g.lineTo(xx,480);g.stroke();
   g.beginPath();g.moveTo(xx-13,500);g.lineTo(xx,480);g.lineTo(xx+13,500);g.stroke();g.restore();
  }
 }
 if(d==='SIGNAL'){
  const x=1560,y=785,r=50+29*pulse;
  g.save();g.globalAlpha=.10+.18*pulse;g.strokeStyle='#84e5ef';g.lineWidth=4;
  for(let j=0;j<3;j++){g.beginPath();g.arc(x,y,r+j*58,Math.PI*.95,Math.PI*1.95);g.stroke();}
  g.restore();
  if(/radio|warning|alert/.test(shot.description.toLowerCase())){
   g.save();g.globalAlpha=.25*life;g.strokeStyle='#f3b18d';g.lineWidth=3;
   for(let j=0;j<45;j++){const v=30*Math.sin(t*5+j*.8)*Math.sin(j*.3);g.beginPath();g.moveTo(1400+j*7,941-v);g.lineTo(1400+j*7,941+v);g.stroke();}
   g.restore();
  }
 }
 if(d==='RESOURCE'){
  const x=1440,y=895;g.save();g.globalAlpha=.31*life;
  g.strokeStyle='#ffd597';g.lineWidth=3;
  for(let j=0;j<5;j++){g.beginPath();g.roundRect(x+j*46,y+12+(j%2)*10,24,42,4);g.stroke();}
  g.restore();
 }
 if(d==='ENERGY'){
  const a=.025+.10*pulse;g.fillStyle='rgba(250,145,91,'+a+')';g.fillRect(0,0,W,H);
  for(let k=0;k<21;k++){const x=(rnd(k+index*111)*W+t*39)%W;const y=(rnd(k+9)*H-t*77)%H;
   g.fillStyle='rgba(243,214,169,'+(.08+(k%4)*.033)+')';g.beginPath();g.ellipse(x,y,2.6,7,.2,0,6.283);g.fill();}
 }
 if(d==='PEOPLE'&&/help|survivor|hurt|water|bottle/.test(shot.description.toLowerCase())){
  g.save();g.globalAlpha=.11*life;g.strokeStyle='#f2cb92';g.lineWidth=3;g.beginPath();g.arc(1620,806,110,Math.PI*1.1,Math.PI*1.9);g.stroke();g.restore();
 }
 // Character prop reactions and purposeful camera-aligned light sweeps. Never whole-image uniform zoom.
 const vign=g.createRadialGradient(950,490,300,950,490,1280);
 vign.addColorStop(0,'rgba(4,10,22,0)');vign.addColorStop(1,'rgba(3,9,18,.24)');
 g.fillStyle=vign;g.fillRect(0,0,W,H);
 if(/banging|impact|explode|crack|slam|horn|alarm/.test(shot.description.toLowerCase())){
  const hit=Math.max(0,1-Math.abs((u%2.3)-.16)/.22);
  if(hit>.01){g.fillStyle='rgba(244,227,204,'+(.13*hit)+')';g.fillRect(0,0,W,H);}
 }
 at.needsUpdate=true;gt.needsUpdate=true;
}
async function renderFrame(t){
 if(!Number.isFinite(t)||t<START||t>=END)throw Error('Outside chapter absolute story time: '+t);
 const ix=SHOTS.findIndex(s=>t>=s.start_sec&&t<s.end_sec),s=SHOTS[ix];
 if(ix<0||!s)throw Error('No original user story image at '+t);
 cine.seek(t,false);
 const v=s.description.toLowerCase(),u=(t-s.start_sec)/(s.end_sec-s.start_sec);
 const shock=/crack|hit|bang|glass|slam|scream|impact|thunder|alert|horn/.test(v)?Math.max(0,1-Math.abs(u-.5)/.14):0;
 camera.position.x+=shock*.024*Math.sin(t*99);
 camera.position.y+=shock*.015*Math.sin(t*130);
 camera.lookAt(0,0,0);
 for(let i=0;i<objects.length;i++){
  for(let j=0;j<3;j++){
   const p=objects[i][j];p.visible=i===ix;
   if(!p.visible)continue;
   p.position.x=j===0?.011*Math.sin(t*.27):j===1?.045*Math.sin(t*1.11+ix):.16*Math.sin(t*1.22+ix*.4)+.06*u;
   p.position.y=j===0?0:j===1?.030*Math.sin(t*.74+ix):.041*Math.sin(t*.94+ix);
   p.rotation.z=j===1?.0018*Math.sin(t*1.72+ix):j===2?.0022*Math.sin(t*1.04+ix):0;
   if(/run|rush|grip|signal|point|reel|climb|jump|pound|fall|wave|reach|turn|push|count|help|gasp/.test(v)&&j===1){
     p.position.x+=.052*Math.sin(t*2.8+ix*1.3);
     p.rotation.z+=.004*Math.sin(t*2.3+ix);
   }
  }
 }
 mistPlane.position.x=.03*Math.sin(t*.34);over(t,s,ix);
 graphicsPlane.position.x=camera.position.x;graphicsPlane.position.y=camera.position.y;
 renderer.render(scene,camera);
 return {chapter:config.chapter,time:t,shot:s.key,cameraX:camera.position.x,cameraZ:camera.position.z,nearX:objects[ix][2].position.x,midX:objects[ix][1].position.x,farX:objects[ix][0].position.x};
}
await renderFrame(START);window.ready=true;window.renderFrame=renderFrame;
const status=document.getElementById('status');status.textContent='MARKET SIX V3 / CHAPTER '+String(config.chapter)+' / ORIGINAL 2.5D ILLUSTRATED CINEMA';
let raf=null,epoch=0;
document.getElementById('play').onclick=()=>{if(raf!==null)return;epoch=performance.now();const update=async now=>{if(raf===null)return;try{await renderFrame(START+((now-epoch)/1000)%(END-START))}catch(e){status.textContent=e.message;raf=null;return}raf=requestAnimationFrame(update)};raf=requestAnimationFrame(update)};
document.getElementById('pause').onclick=()=>{if(raf!==null)cancelAnimationFrame(raf);raf=null};
