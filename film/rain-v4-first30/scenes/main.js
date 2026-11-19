import * as THREE from 'three';
import gsap from 'gsap';

// V4 10–30-second continuation. Canonical time is ABSOLUTE seconds, not shard-local.
// Human figures never move: this segment deliberately uses environment, geometry,
// typographic storytelling, and independently animated nonhuman rope + knife.
const W=1920,H=1080,FPS=30,FIRST=10,END=30;
const stage=document.getElementById('stage');
if(!stage||stage.width!==W||stage.height!==H)throw Error('Approved 1920x1080 canvas missing');
const renderer=new THREE.WebGLRenderer({canvas:stage,antialias:true,alpha:false,preserveDrawingBuffer:true});
renderer.setPixelRatio(1);renderer.setSize(W,H,false);renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.NoToneMapping;renderer.autoClear=false;
const world=new THREE.Scene();world.background=new THREE.Color('#0b1725');
const camera=new THREE.PerspectiveCamera(55,W/H,.1,200);
const ui=new THREE.Scene(),uiCamera=new THREE.OrthographicCamera(-W/2,W/2,H/2,-H/2,.1,10);
uiCamera.position.z=5;
const shots=[
 {id:'S04_STREET_YEARS',art:'street',t0:10.00,t1:12.10,a:[-.42,.11,10.49],b:[.39,-.08,9.88],kind:'establishing',intent:'Decade-long persistence shocks a familiar walkable street'},
 {id:'S05_ATMOS_EVERY_DAY',art:'atmos',t0:12.10,t1:14.48,a:[.48,.17,10.32],b:[-.44,-.08,9.78],kind:'wide infographic',intent:'Atmospheric rain bands do not relent; successive day indicators'},
 {id:'S06_FLOOD_MONTH_ONE',art:'flood',t0:14.48,t1:17.56,a:[-.42,-.11,10.38],b:[.29,.11,9.61],kind:'flooding street',intent:'First-month water threatens survival; independent water overlay rises'},
 {id:'S07_COLD',art:'cold',t0:17.56,t1:18.90,a:[.24,-.05,10.18],b:[-.13,-.02,9.83],kind:'cold insert',intent:'Future cold threatens as a slower consequence'},
 {id:'S08_HUNGER',art:'hunger',t0:18.90,t1:20.17,a:[.23,.04,10.12],b:[-.23,-.06,9.64],kind:'food scarcity insert',intent:'Shelves emptied; slow hunger pressure'},
 {id:'S09_SEA',art:'atmos',t0:20.17,t1:21.52,a:[-.47,.09,10.36],b:[.08,-.10,9.81],kind:'sea insert',intent:'Storm-fed coastline is a long-term threat'},
 {id:'S10_TOWER',art:'tower',t0:21.52,t1:23.84,a:[.43,-.17,10.28],b:[-.31,.14,9.66],kind:'rising tower',intent:'The building stays standing while vulnerability is foreshadowed'},
 {id:'S11_ROPE_YEAR_SIX',art:'rope',t0:23.84,t1:30.00,a:[-.30,.13,10.37],b:[.16,-.04,9.73],kind:'independent object close-up',intent:'Five-year lifeline is cut by a knife whose unseen operator remains offscreen'}
];
const progress={u:0},timeline=gsap.timeline({paused:true});
for(const sh of shots){timeline.set(progress,{u:0},sh.t0);timeline.to(progress,{u:1,duration:sh.t1-sh.t0,ease:'power2.inOut'},sh.t0);}
const clamp=v=>Math.max(0,Math.min(1,v));
const smooth=v=>{v=clamp(v);return v*v*(3-2*v)};
const rand=i=>((Math.imul(i+29,1664525)+1013904223)>>>0)/4294967295;
function basic(tex){return new THREE.MeshBasicMaterial({map:tex,transparent:true,depthTest:false,depthWrite:false,toneMapped:false,side:THREE.DoubleSide});}
function tex(image){const t=new THREE.Texture(image);t.needsUpdate=true;t.colorSpace=THREE.SRGBColorSpace;t.minFilter=THREE.LinearFilter;return t;}
async function load(s){const i=new Image();i.src='assets/'+s;await i.decode();return i;}
function plane(texture,z,order,overscan=1.24){
 const d=10-z,w=2*d*Math.tan(55*Math.PI/360)*(W/H)*overscan;
 const m=new THREE.Mesh(new THREE.PlaneGeometry(w,w*H/W),basic(texture));m.position.z=z;m.renderOrder=order;world.add(m);return m;
}
const sets={};
for(const a of ['street','atmos','flood','cold','hunger','tower','rope']){
 const [far,mid,front]=await Promise.all(['far','mid','front'].map(j=>load(a+'_'+j+'.webp')));
 sets[a]=[plane(tex(far),-3.9,0),plane(tex(mid),-.65,1),plane(tex(front),2.2,3)];
}
const [ropeIntact,ropeBroken,knife]=await Promise.all(['rope_intact.webp','rope_broken.webp','knife.webp'].map(load));
// Atmosphere and independent-object planes have distinct real-world Z.
const envC=document.createElement('canvas');envC.width=W;envC.height=H;
const envCtx=envC.getContext('2d',{alpha:true});const envTex=new THREE.CanvasTexture(envC);envTex.colorSpace=THREE.SRGBColorSpace;
const envPlane=plane(envTex,2.75,5,1.24);
const waterC=document.createElement('canvas');waterC.width=W;waterC.height=H;
const waterCtx=waterC.getContext('2d',{alpha:true});const waterTex=new THREE.CanvasTexture(waterC);waterTex.colorSpace=THREE.SRGBColorSpace;
const waterPlane=plane(waterTex,2.95,6,1.24);
const ropeC=document.createElement('canvas');ropeC.width=W;ropeC.height=H;
const ropeCtx=ropeC.getContext('2d',{alpha:true});const ropeTex=new THREE.CanvasTexture(ropeC);ropeTex.colorSpace=THREE.SRGBColorSpace;
const ropePlane=plane(ropeTex,3.33,7,1.18);
const graphicsC=document.createElement('canvas');graphicsC.width=W;graphicsC.height=H;
const g=graphicsC.getContext('2d',{alpha:true});const graphicsTex=new THREE.CanvasTexture(graphicsC);graphicsTex.colorSpace=THREE.SRGBColorSpace;
const graphic=new THREE.Mesh(new THREE.PlaneGeometry(W,H),basic(graphicsTex));graphic.renderOrder=999;ui.add(graphic);

function storm(t,sh){
 envCtx.clearRect(0,0,W,H);
 const snow=sh.id==='S07_COLD',indoor=sh.id==='S08_HUNGER',strong=sh.id==='S06_FLOOD_MONTH_ONE'||sh.id==='S11_ROPE_YEAR_SIX';
 if(indoor){ // Keep supermarket interior dry: rain is ONLY visible beyond glass entrance.
  envCtx.save();envCtx.beginPath();envCtx.rect(1180,120,550,650);envCtx.clip();
 }
 const amount=snow?95:indoor?50:strong?182:125;
 const vx=snow?12:strong?-91:47;
 envCtx.lineCap='round';
 for(let i=0;i<amount;i++){
  const a=rand(i+1019+(sh.id==='S09_SEA'?443:0)),b=rand(i+2021);
  const x=((rand(i+19)*2200+t*(vx*(.4+a))+5000)%2200)-130;
  const y=((rand(i+333)*1300+t*(snow?74:280)*(.55+a))%1350)-150;
  envCtx.globalAlpha=snow?(.17+a*.35):(.05+a*.20);
  if(snow){
   envCtx.fillStyle='#f0f7ff';envCtx.beginPath();envCtx.ellipse(x,y,1.8+a*3,1.2+a*2,.2,0,Math.PI*2);envCtx.fill();
  }else{
   envCtx.strokeStyle=strong?'#bedbe8':'#d7e8f2';envCtx.lineWidth=.8+a*1.45;
   envCtx.beginPath();envCtx.moveTo(x,y);envCtx.lineTo(x+vx*.12,y+18+30*a);envCtx.stroke();
  }
 }
 envCtx.globalAlpha=1;if(indoor)envCtx.restore();
 if(strong||sh.id==='S09_SEA'){
  for(let i=0;i<15;i++){
   const x=140+rand(i+500)*1630,y=770+rand(i+540)*214;
   envCtx.fillStyle='rgba(160,230,242,'+(.04+.1*(.5+.5*Math.sin(t*2+i)))+')';
   envCtx.fillRect(x,y,18+rand(i+600)*70,1.4);
  }
 }
 envTex.needsUpdate=true;
}
function risingWater(t,sh){
 waterCtx.clearRect(0,0,W,H);
 if(sh.id!=='S06_FLOOD_MONTH_ONE'){waterTex.needsUpdate=true;waterPlane.visible=false;return;}
 waterPlane.visible=true;
 const u=smooth((t-sh.t0)/(sh.t1-sh.t0));
 const top=791-104*u;
 const grad=waterCtx.createLinearGradient(0,top,0,H);
 grad.addColorStop(0,'rgba(114,187,193,.00)');grad.addColorStop(.06,'rgba(97,170,185,.19)');grad.addColorStop(1,'rgba(10,55,77,.10)');
 waterCtx.fillStyle=grad;waterCtx.fillRect(0,top,W,H-top);
 for(let i=0;i<22;i++){
  const x=100+rand(i+222)*1680,y=top+8+rand(i+401)*(H-top-17);
  const shimmer=.08+.1*(.5+.5*Math.sin(i*2.7+t*3.5));
  waterCtx.strokeStyle='rgba(179,221,218,'+shimmer+')';waterCtx.lineWidth=1.6;
  waterCtx.beginPath();waterCtx.ellipse(x,y,24+u*18+rand(i)*45,2.2+rand(i+11)*3,0,0,Math.PI*2);waterCtx.stroke();
 }
 waterTex.needsUpdate=true;
}
function drawRope(t,sh){
 ropeCtx.clearRect(0,0,W,H);ropePlane.visible=sh.id==='S11_ROPE_YEAR_SIX';
 if(!ropePlane.visible){ropeTex.needsUpdate=true;return;}
 const cut=27.60,progress=smooth((t-cut)/.48),y=520+3*Math.sin(t*1.6);
 ropeCtx.save();ropeCtx.shadowColor='rgba(3,7,15,.73)';ropeCtx.shadowBlur=19;ropeCtx.shadowOffsetY=10;
 if(t<cut){
  ropeCtx.drawImage(ropeIntact,455,y,1350,52);
 }else{
  // Object-state action: authored frayed source evolves from taut rope into two
  // separate recoiling segments; NO human is moved or deformed.
  const drift=22*progress;
  ropeCtx.save();ropeCtx.translate(-drift,-12*progress);ropeCtx.rotate(-.01*progress);
  ropeCtx.drawImage(ropeBroken,455,y,1350,69);ropeCtx.restore();
 }
 ropeCtx.restore();
 // Knife originates off the right edge (unseen hand), approaches taut rope,
 // makes contact at cut time, then stops. This is the action of an offscreen
 // operator, not a magically moving knife or a moving character puppet.
 if(t>=26.0&&t<28.5){
  const q=smooth((t-26.0)/1.65),x=1915-(720*q);
  ropeCtx.save();ropeCtx.globalAlpha=smooth((t-26)/.14)*(1-smooth((t-28.14)/.36));
  ropeCtx.translate(x,395+18*q);ropeCtx.rotate(-.016*q);
  ropeCtx.drawImage(knife,0,0,860,493);ropeCtx.restore();
 }
 if(t>=cut&&t<cut+.18){
  const q=1-(t-cut)/.18;
  ropeCtx.strokeStyle='rgba(255,225,181,'+(.5*q)+')';ropeCtx.lineWidth=2;
  for(let k=0;k<12;k++){
   const a=k*Math.PI*2/12,range=19+(1-q)*41;
   ropeCtx.beginPath();ropeCtx.moveTo(1125+Math.cos(a)*10,538+Math.sin(a)*9);
   ropeCtx.lineTo(1125+Math.cos(a)*range,538+Math.sin(a)*range);ropeCtx.stroke();
  }
 }
 ropeTex.needsUpdate=true;
}
function label(s,x,y,opacity=1,emph=false){
 if(opacity<=0)return;
 g.save();g.globalAlpha=clamp(opacity);
 g.font=(emph?'800 29px':'650 26px')+' system-ui, Inter, sans-serif';
 const w=Math.max(225,g.measureText(s).width+66);
 g.fillStyle=emph?'rgba(85,26,28,.81)':'rgba(7,28,49,.72)';
 g.strokeStyle=emph?'rgba(254,173,147,.70)':'rgba(189,224,232,.43)';
 g.lineWidth=2;g.beginPath();g.roundRect(x,y,w,68,13);g.fill();g.stroke();
 g.fillStyle=emph?'#ffefdc':'#e8f8fd';g.fillText(s,x+32,y+43);g.restore();
}
function big(s,y,alpha,extra=''){
 if(alpha<=0)return;
 g.save();g.globalAlpha=clamp(alpha);
 g.shadowColor='rgba(2,10,22,.78)';g.shadowBlur=44;
 g.textAlign='center';g.font='900 154px system-ui, Inter, sans-serif';
 g.fillStyle='#f6eace';g.fillText(s,960,y);g.shadowBlur=0;
 if(extra){g.font='650 31px system-ui, Inter, sans-serif';g.fillStyle='#b9e9f0';g.fillText(extra,960,y+59);}
 g.restore();
}
function motionGraphic(t,sh){
 g.clearRect(0,0,W,H);const u=t-sh.t0;
 const vign=g.createRadialGradient(960,500,250,960,520,1130);
 vign.addColorStop(0,'rgba(7,12,24,0)');vign.addColorStop(1,'rgba(4,10,23,.32)');g.fillStyle=vign;g.fillRect(0,0,W,H);
 if(sh.id==='S04_STREET_YEARS'){
  label('DAY ONE / THE RAIN BEGINS',104,84,smooth((u-.14)/.26)*smooth((.85-u)/.2));
  big('10 YEARS',745,smooth((u-.63)/.37)*smooth((2.04-u)/.3),'OF UNBROKEN RAIN');
 }else if(sh.id==='S05_ATMOS_EVERY_DAY'){
  label('NO BREAKS.  NO DRY DAYS.',105,86,smooth((u-.1)/.24)*smooth((2.25-u)/.25));
  g.save();g.globalAlpha=.84;
  for(let i=0;i<10;i++){
   const xx=295+i*138,yy=867;
   g.fillStyle='rgba(2,20,37,.67)';g.strokeStyle='rgba(166,221,235,.37)';g.lineWidth=2;
   g.beginPath();g.roundRect(xx,yy,113,74,10);g.fill();g.stroke();
   g.font='600 16px system-ui,sans-serif';g.textAlign='center';g.fillStyle='#b9ddec';g.fillText('YEAR '+(i+1),xx+56,yy+19);
   const lit=smooth((u-(.2+i*.16))/.18);g.fillStyle='rgba(148,217,234,'+(.18+.75*lit)+')';
   for(let j=0;j<4;j++)g.fillRect(xx+26+j*14,yy+37+(j%2)*7,3,19);
  }
  g.restore();
 }else if(sh.id==='S06_FLOOD_MONTH_ONE'){
  label('MONTH ONE  /  THE FLOOD',105,86,smooth((u-.12)/.32));
  if(u>1.65)label('THE STREET DISAPPEARS',105,169,smooth((u-1.65)/.26),true);
 }else if(sh.id==='S07_COLD')label('THE COLD',105,86,smooth(u/.14));
 else if(sh.id==='S08_HUNGER')label('THE HUNGER',105,86,smooth(u/.14),true);
 else if(sh.id==='S09_SEA')label('THE SEA',105,86,smooth(u/.14));
 else if(sh.id==='S10_TOWER'){
  label('AND THE BUILDING...',105,86,smooth((u-.05)/.27));
  if(u>1.40)label('THEY TAKE THEIR TIME',105,168,smooth((u-1.40)/.25),true);
 }else if(sh.id==='S11_ROPE_YEAR_SIX'){
  label('YEAR SIX  /  FLASH FORWARD',103,85,smooth((u-.12)/.28)*smooth((3.1-u)/.35));
  if(u>2.55&&u<4.4)label('FIVE YEARS OF SURVIVAL',103,85,smooth((u-2.55)/.28)*smooth((4.45-u)/.25));
  if(t>27.85){
   g.save();g.globalAlpha=smooth((t-27.85)/.28);g.font='900 81px system-ui,Inter,sans-serif';
   g.fillStyle='#f7eadc';g.shadowColor='rgba(20,7,6,.87)';g.shadowBlur=22;
   g.fillText('ON PURPOSE.',104,871);g.restore();
  }
  // Motivated lightning just BEFORE the cut and its consequences.
  const flash=Math.max(0,1-Math.abs(t-27.45)/.11)*.1;
  if(flash){g.fillStyle='rgba(214,235,250,'+flash+')';g.fillRect(0,0,W,H);}
 }
 // Modern editorial footer, deliberately low visual dominance.
 const a=Math.min(1,smooth((t-10.15)/.3)*smooth((29.82-t)/.22));
 g.fillStyle='rgba(172,225,235,'+(.37*a)+')';g.fillRect(104,1002,94,2);
 g.font='500 20px system-ui, Inter, sans-serif';g.fillStyle='rgba(230,241,246,'+(.67*a)+')';
 g.fillText('WHAT IF IT NEVER STOPPED RAINING?',104,1045);
 graphicsTex.needsUpdate=true;
}
window.renderFrame=async t=>{
 if(!Number.isFinite(t)||t<FIRST||t>=END)throw Error('Canonical 10–30s boundary violated '+t);
 const sh=shots.find(s=>t>=s.t0&&t<s.t1);if(!sh)throw Error('Shot-gap or overlap '+t);
 timeline.seek(t,false);const p=progress.u;
 camera.position.set(sh.a[0]+(sh.b[0]-sh.a[0])*p,sh.a[1]+(sh.b[1]-sh.a[1])*p,sh.a[2]+(sh.b[2]-sh.a[2])*p);
 const target=new THREE.Vector3(camera.position.x*.06,Math.sin(p*Math.PI)*.035,0);
 camera.lookAt(target);
 for(const [id,ls] of Object.entries(sets))ls.forEach((m,j)=>{
  m.visible=id===sh.art;
  // Different depth plane offsets come from actual perspective, not flat Ken Burns.
  if(m.visible){m.position.x=j===0?0:j===1?.025*Math.sin(t*.55):.045*Math.sin(t*.47);}
 });
 storm(t,sh);risingWater(t,sh);drawRope(t,sh);motionGraphic(t,sh);
 renderer.clear();renderer.render(world,camera);renderer.clearDepth();renderer.render(ui,uiCamera);
 return {t,shot:sh.id,still_character:true,independent_layers:3,environment_motion:true,
   rope_object_action:sh.id==='S11_ROPE_YEAR_SIX'&&t>=27.60,cam_x:camera.position.x,cam_z:camera.position.z};
};
// Required fully deterministic Web Audio OfflineAudioContext: 20s, WAV 24k mono.
window.exportRainSfx=async()=>{
 const rate=24000,n=20*rate,offline=new OfflineAudioContext(1,n,rate);
 const buffer=offline.createBuffer(1,n,rate),samples=buffer.getChannelData(0);
 let seed=23119;for(let i=0;i<n;i++){seed=(Math.imul(seed,1664525)+1013904223)>>>0;samples[i]=(seed/4294967296*2-1)*.19;}
 const src=offline.createBufferSource();src.buffer=buffer;
 const low=offline.createBiquadFilter();low.type='lowpass';low.frequency.value=1800;
 const gain=offline.createGain();gain.gain.setValueAtTime(.20,0);gain.gain.setValueAtTime(.22,5);
 gain.gain.linearRampToValueAtTime(.32,7);gain.gain.linearRampToValueAtTime(.13,9.5);gain.gain.setValueAtTime(.22,15);
 src.connect(low);low.connect(gain);gain.connect(offline.destination);src.start(0);
 for(const at of [4.6,7.3,13.9]){
  const os=offline.createOscillator(),og=offline.createGain();os.type='sine';
  os.frequency.setValueAtTime(64,at);os.frequency.exponentialRampToValueAtTime(32,at+.48);
  og.gain.setValueAtTime(.0001,at);og.gain.exponentialRampToValueAtTime(.08,at+.035);og.gain.exponentialRampToValueAtTime(.0001,at+.86);
  os.connect(og);og.connect(offline.destination);os.start(at);os.stop(at+.87);
 }
 // A short low acoustic hit and crack are placed on the visible blade contact.
 const hit=17.60,os=offline.createOscillator(),og=offline.createGain();
 os.type='triangle';os.frequency.setValueAtTime(133,hit);os.frequency.exponentialRampToValueAtTime(32,hit+.3);
 og.gain.setValueAtTime(.0001,hit);og.gain.exponentialRampToValueAtTime(.28,hit+.011);og.gain.exponentialRampToValueAtTime(.0001,hit+.49);
 os.connect(og);og.connect(offline.destination);os.start(hit);os.stop(hit+.51);
 const b=await offline.startRendering(),a=b.getChannelData(0),out=new ArrayBuffer(44+n*2),u8=new Uint8Array(out),v=new DataView(out);
 const chars=(offset,str)=>{for(let j=0;j<str.length;j++)u8[offset+j]=str.charCodeAt(j)};
 chars(0,'RIFF');v.setUint32(4,36+n*2,true);chars(8,'WAVEfmt ');v.setUint32(16,16,true);
 v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,rate,true);v.setUint32(28,rate*2,true);v.setUint16(32,2,true);v.setUint16(34,16,true);
 chars(36,'data');v.setUint32(40,n*2,true);for(let i=0;i<n;i++)v.setInt16(44+i*2,Math.round(Math.max(-1,Math.min(1,a[i]))*32767),true);
 let binary='';for(let i=0;i<u8.length;i+=8192)binary+=String.fromCharCode(...u8.subarray(i,i+8192));
 return btoa(binary);
};
await window.renderFrame(10);window.ready=true;
