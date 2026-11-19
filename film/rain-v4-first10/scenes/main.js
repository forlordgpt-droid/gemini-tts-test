import * as THREE from 'three';
import gsap from 'gsap';
const W=1920,H=1080,D=10,canvas=document.getElementById('stage');
if(!canvas||canvas.width!==W||canvas.height!==H)throw Error('Missing 1080p canvas');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(1);renderer.setSize(W,H,false);renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.NoToneMapping;renderer.autoClear=false;
const scene=new THREE.Scene();scene.background=new THREE.Color('#0f1e30');
const camera=new THREE.PerspectiveCamera(55,W/H,.1,100);
const uiScene=new THREE.Scene(),uiCamera=new THREE.OrthographicCamera(-W/2,W/2,H/2,-H/2,.1,10);
uiCamera.position.z=5;
const shots=[
 {id:'S01_HARBOR',start:0,end:3.35,art:'harbor',a:[-.55,.14,10.52],b:[.40,-.10,9.88]},
 {id:'S02_APARTMENT',start:3.35,end:6.65,art:'apartment',a:[.53,-.13,10.27],b:[-.39,.11,9.78]},
 {id:'S03_STORM',start:6.65,end:10,art:'coast',a:[-.62,.11,10.42],b:[.25,-.14,9.70]}
];
const anim={progress:0},timeline=gsap.timeline({paused:true});
for(const s of shots){timeline.set(anim,{progress:0},s.start);timeline.to(anim,{progress:1,duration:s.end-s.start,ease:'power2.inOut'},s.start);}
function makeTexture(im){const t=new THREE.Texture(im);t.colorSpace=THREE.SRGBColorSpace;t.minFilter=THREE.LinearFilter;t.needsUpdate=true;return t;}
function mat(t){return new THREE.MeshBasicMaterial({map:t,transparent:true,depthTest:false,depthWrite:false,side:THREE.DoubleSide,toneMapped:false});}
async function image(path){const im=new Image();im.src=path;await im.decode();return im;}
function stagePlane(t,z,order,overscan=1.115){
 const distance=10-z,width=2*distance*Math.tan(55*Math.PI/360)*W/H*overscan;
 const mesh=new THREE.Mesh(new THREE.PlaneGeometry(width,width*H/W),mat(t));mesh.position.z=z;mesh.renderOrder=order;scene.add(mesh);return mesh;
}
const sets={};
for(const n of ['harbor','apartment','coast']){
 const [bg,mid,fg]=await Promise.all(['far','mid','front'].map(c=>image('assets/'+n+'_'+c+'.webp')));
 sets[n]=[stagePlane(makeTexture(bg),-4,0),stagePlane(makeTexture(mid),-1.35,1),stagePlane(makeTexture(fg),1.22,3)];
}
const figure=await image('assets/protagonist_day1_still.webp');
const actor=new THREE.Mesh(new THREE.PlaneGeometry(2.38,2.38*figure.height/figure.width),mat(makeTexture(figure)));
actor.position.set(4.05,-1.20,1.45);actor.renderOrder=4;scene.add(actor);
// Separated atmospheric depth plane: environment motion is not camera motion.
const rainC=document.createElement('canvas');rainC.width=W;rainC.height=H;
const rainCtx=rainC.getContext('2d');const rainT=new THREE.CanvasTexture(rainC);
rainT.colorSpace=THREE.SRGBColorSpace;const rainPlane=stagePlane(rainT,2.05,5,1.13);
// Screen-space UI is composited as actual WebGL pixels, not as a DOM overlay.
const textC=document.createElement('canvas');textC.width=W;textC.height=H;
const g=textC.getContext('2d'),textT=new THREE.CanvasTexture(textC);textT.colorSpace=THREE.SRGBColorSpace;
const textPlane=new THREE.Mesh(new THREE.PlaneGeometry(W,H),mat(textT));uiScene.add(textPlane);
function smooth(v){v=Math.max(0,Math.min(1,v));return v*v*(3-2*v);}
function rand(k){return ((Math.imul(k+123,1664525)+1013904223)>>>0)/4294967295;}
function drawRain(t,sh){
 rainCtx.clearRect(0,0,W,H);
 if(sh.id==='S02_APARTMENT')return;
 const storm=sh.id==='S03_STORM',dx=storm?-69:38,seed=storm?1111:4444;
 rainCtx.lineCap='round';
 for(let i=0;i<(storm?150:105);i++){
  const d=rand(i+seed),speed=storm?325:235;
  const x=(rand(i+seed+330)*2110+t*(dx*(.5+d))+5000)%2110-95;
  const y=(rand(i+seed+661)*1310+t*speed*(.65+d))%1300-120;
  rainCtx.strokeStyle=storm?'#b9e5ef':'#e0effd';rainCtx.lineWidth=.7+d*1.5;
  rainCtx.globalAlpha=(.10+d*.23)*(storm?.70:.54);
  rainCtx.beginPath();rainCtx.moveTo(x,y);rainCtx.lineTo(x+dx*.14,y+(storm?29:18)+d*24);rainCtx.stroke();
 }
 rainCtx.globalAlpha=1;
 if(storm){for(let i=0;i<15;i++){
  const x=200+rand(1000+i)*1500,y=750+rand(2100+i)*220;
  rainCtx.fillStyle='rgba(173,229,243,'+(.05+.09*(.5+.5*Math.sin(t*1.7+i)))+')';
  rainCtx.fillRect(x,y,20+45*rand(2400+i),1.5);
 }}
}
function pill(s,x,y,a,warning=false){
 if(a<=0)return;g.save();g.globalAlpha=Math.min(1,a);g.font='700 25px system-ui,sans-serif';
 const w=Math.max(210,g.measureText(s).width+57);g.fillStyle=warning?'rgba(70,24,29,.80)':'rgba(5,23,42,.78)';
 g.strokeStyle=warning?'rgba(248,131,113,.74)':'rgba(171,222,232,.45)';g.lineWidth=2;
 g.beginPath();g.roundRect(x,y,w,67,14);g.fill();g.stroke();g.fillStyle=warning?'#ffe7da':'#e0f5fc';
 g.fillText(s,x+28,y+42);g.restore();
}
function drawUI(t,sh){
 g.clearRect(0,0,W,H);const u=t-sh.start;
 const v=g.createRadialGradient(960,500,260,960,520,1110);
 v.addColorStop(0,'rgba(4,9,20,0)');v.addColorStop(1,'rgba(4,9,20,.30)');g.fillStyle=v;g.fillRect(0,0,W,H);
 if(sh.id==='S01_HARBOR'){
  pill('DAY ONE  /  THE COAST',100,91,smooth(t/.3)*smooth((2.1-t)/.3));
  if(t>=2.2)pill('THE WATER IS THE DANGER?',100,91,smooth((t-2.2)/.25));
 }else if(sh.id==='S02_APARTMENT'){
  pill('THE DANGER SEEMS OBVIOUS',100,91,smooth((u-.12)/.23)*smooth((1.4-u)/.3));
  pill("YOU'RE WRONG.",100,91,smooth((u-1.25)/.23)*smooth((3.1-u)/.25),true);
  const flicker=.065*(.6+.4*Math.sin(t*4.5));
  const glow=g.createRadialGradient(470,400,40,470,400,600);
  glow.addColorStop(0,'rgba(255,202,122,'+flicker+')');glow.addColorStop(1,'rgba(255,202,122,0)');
  g.fillStyle=glow;g.fillRect(0,0,W,H);
 }else{
  pill('THE RAIN WILL NOT STOP',100,91,smooth((u-.10)/.25)*smooth((2.4-u)/.22));
  if(u>2.20)pill('NEVER RUN OUT.',100,91,smooth((u-2.2)/.28));
  const lightning=Math.max(0,1-Math.abs(u-1.50)/.14)*.072;
  if(lightning){g.fillStyle='rgba(218,236,250,'+lightning+')';g.fillRect(0,0,W,H);}
 }
 const alpha=Math.max(0,Math.min(1,(t-.2)/.5,(9.85-t)/.25));
 g.fillStyle='rgba(192,232,240,'+(.35*alpha)+')';g.fillRect(100,986,95,2);
 g.font='500 20px system-ui,sans-serif';g.fillStyle='rgba(241,248,251,'+(.76*alpha)+')';
 g.fillText('WHAT IF IT NEVER STOPPED RAINING?',100,1031);
}
window.renderFrame=t=>{
 if(!Number.isFinite(t)||t<0||t>=D)throw Error('Invalid canonical preview time '+t);
 const sh=shots.find(s=>t>=s.start&&t<s.end);if(!sh)throw Error('Shot gap');
 timeline.seek(t,false);const p=anim.progress;
 camera.position.set(sh.a[0]+(sh.b[0]-sh.a[0])*p,sh.a[1]+(sh.b[1]-sh.a[1])*p,sh.a[2]+(sh.b[2]-sh.a[2])*p);
 camera.lookAt(camera.position.x*.06,Math.sin(p*Math.PI)*.045-.03,0);
 for(const [name,layers] of Object.entries(sets))for(const plane of layers)plane.visible=name===sh.art;
 actor.visible=sh.id==='S02_APARTMENT';rainPlane.visible=sh.id!=='S02_APARTMENT';
 drawRain(t,sh);rainT.needsUpdate=true;drawUI(t,sh);textT.needsUpdate=true;
 renderer.clear();renderer.render(scene,camera);renderer.clearDepth();renderer.render(uiScene,uiCamera);
 return {shot:sh.id,t,camera_x:camera.position.x,camera_z:camera.position.z,layers:3,still_character:true};
};
// Deterministic ambience from the required Web Audio OfflineAudioContext; no external APIs.
window.exportRainSfx=async()=>{
 const sampleRate=24000,n=sampleRate*10,offline=new OfflineAudioContext(1,n,sampleRate);
 const noise=offline.createBuffer(1,n,sampleRate),s=noise.getChannelData(0);
 let seed=30791;for(let i=0;i<n;i++){seed=(Math.imul(seed,1664525)+1013904223)>>>0;s[i]=(seed/4294967295*2-1)*.17;}
 const src=offline.createBufferSource();src.buffer=noise;
 const filter=offline.createBiquadFilter();filter.type='lowpass';filter.frequency.value=2200;
 const gain=offline.createGain();gain.gain.value=.23;src.connect(filter);filter.connect(gain);gain.connect(offline.destination);src.start(0);
 for(const at of [3.72,6.74]){
  const o=offline.createOscillator(),v=offline.createGain();o.type='sine';
  o.frequency.setValueAtTime(62,at);o.frequency.exponentialRampToValueAtTime(34,at+.44);
  v.gain.setValueAtTime(.0001,at);v.gain.exponentialRampToValueAtTime(.115,at+.04);v.gain.exponentialRampToValueAtTime(.0001,at+.68);
  o.connect(v);v.connect(offline.destination);o.start(at);o.stop(at+.7);
 }
 const result=await offline.startRendering(),floats=result.getChannelData(0),data=new ArrayBuffer(44+n*2),u=new Uint8Array(data),v=new DataView(data);
 function chars(off,str){for(let j=0;j<str.length;j++)u[off+j]=str.charCodeAt(j);}
 chars(0,'RIFF');v.setUint32(4,36+n*2,true);chars(8,'WAVEfmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);
 v.setUint16(22,1,true);v.setUint32(24,sampleRate,true);v.setUint32(28,sampleRate*2,true);v.setUint16(32,2,true);v.setUint16(34,16,true);
 chars(36,'data');v.setUint32(40,n*2,true);for(let i=0;i<n;i++)v.setInt16(44+i*2,Math.round(Math.max(-1,Math.min(1,floats[i]))*32767),true);
 let str='';for(let i=0;i<u.length;i+=8192)str+=String.fromCharCode(...u.subarray(i,i+8192));return btoa(str);
};
await window.renderFrame(0);window.ready=true;
