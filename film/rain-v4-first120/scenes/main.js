import * as THREE from 'three';
import gsap from 'gsap';
// V4 immutable 30-120s sequence. No human/actor performance animation.
// Each frame is a pure function of absolute story time: seed, camera, event and FX.
const W=1920,H=1080,FPS=30,FROM=30,END=120,ASPECT=W/H;
const canvas=document.getElementById('stage');
if(!canvas||canvas.width!==W||canvas.height!==H)throw Error('Missing 1920x1080 canvas');
const renderer=new THREE.WebGLRenderer({canvas,alpha:false,antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(1);renderer.setSize(W,H,false);renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.NoToneMapping;renderer.autoClear=false;
const world=new THREE.Scene();world.background=new THREE.Color('#0d1b2a');
const camera=new THREE.PerspectiveCamera(55,ASPECT,.1,150);
const foregroundUI=new THREE.Scene();
const uiCamera=new THREE.OrthographicCamera(-W/2,W/2,H/2,-H/2,.1,10);uiCamera.position.z=5;
const cuts=[
 {id:'R01_TUESDAY',t0:30.0,t1:33.8,art:'apartment',a:[.46,-.12,10.65],b:[-.23,.10,9.71],look:[-.15,0],mood:'warm'},
 {id:'R02_24TH_FLOOR',t0:33.8,t1:37.6,art:'harbor',a:[-.42,-.25,10.55],b:[.24,.24,9.57],look:[.15,0],mood:'blue'},
 {id:'R03_TWO_BLOCKS',t0:37.6,t1:41.7,art:'harbor',a:[.47,.12,10.43],b:[-.35,-.18,9.70],look:[-.26,.08],mood:'blue'},
 {id:'R04_HARBOR_VIEW',t0:41.7,t1:45.2,art:'office',a:[-.35,.13,10.22],b:[.25,-.13,9.51],look:[.06,-.10],mood:'cool'},
 {id:'R05_LEL_OFFICE',t0:45.2,t1:48.0,art:'harbor',a:[.30,-.08,9.97],b:[.49,.08,9.12],look:[.34,0],mood:'blue'},
 {id:'R06_WORK_FROM_HOME',t0:48.0,t1:51.6,art:'apartment',a:[-.36,-.02,10.17],b:[.20,.06,9.48],look:[-.19,0],mood:'warm'},
 {id:'R07_COFFEE',t0:51.6,t1:55.0,art:'apartment',a:[.22,-.06,9.79],b:[-.10,-.10,9.29],look:[-.23,-.10],mood:'warm'},
 {id:'R08_CLOSE_WINDOW',t0:55.0,t1:58.5,art:'apartment',a:[-.04,.05,10.18],b:[-.26,.12,9.66],look:[-.18,.02],mood:'warm'},
 {id:'R09_DAY_TWO',t0:58.5,t1:61.0,art:'apartment',a:[.30,.04,9.97],b:[-.02,-.04,9.56],look:[0,0],mood:'warm'},
 {id:'R10_PHONE_WARNING',t0:61.0,t1:64.3,art:'apartment',a:[-.11,.03,10.0],b:[.09,-.04,9.45],look:[0,0],mood:'alert'},
 {id:'R11_MUDDY_RIVER',t0:64.3,t1:67.6,art:'street',a:[-.42,-.06,10.34],b:[.34,-.15,9.38],look:[-.09,-.15],mood:'mud'},
 {id:'R12_SCHOOLS_CLOSE',t0:67.6,t1:70.8,art:'street',a:[.21,.12,9.93],b:[-.30,-.16,9.56],look:[.10,0],mood:'mud'},
 {id:'R13_LONG_WEEKEND',t0:70.8,t1:73.9,art:'apartment',a:[.02,.04,10.18],b:[.24,-.04,9.55],look:[.04,-.08],mood:'warm'},
 {id:'R14_FIRST_TEN_FORECAST',t0:73.9,t1:77.3,art:'apartment',a:[-.20,.08,10.04],b:[.08,-.03,9.74],look:[0,0],mood:'cool'},
 {id:'R15_NEXT_TEN_FORECAST',t0:77.3,t1:81.4,art:'apartment',a:[.12,.02,10.03],b:[-.20,.02,9.62],look:[0,0],mood:'cool'},
 {id:'R16_RADIO',t0:81.4,t1:85.0,art:'apartment',a:[-.38,.07,10.16],b:[-.08,-.06,9.53],look:[-.05,0],mood:'warm'},
 {id:'R17_ATMOS_RIVER',t0:85.0,t1:90.0,art:'atmos',a:[.39,.08,10.55],b:[-.36,-.12,9.74],look:[-.09,.02],mood:'storm'},
 {id:'R18_WATER_VAPOR',t0:90.0,t1:94.5,art:'atmos',a:[-.53,.14,10.43],b:[.23,-.10,9.45],look:[.08,.02],mood:'storm'},
 {id:'R19_CALIFORNIA_1861',t0:94.5,t1:99.7,art:'historic',a:[.37,.06,10.52],b:[-.31,-.12,9.71],look:[0,0],mood:'historic'},
 {id:'R20_SACRAMENTO_10FT',t0:99.7,t1:104.2,art:'historic',a:[-.33,-.16,10.16],b:[.18,.14,9.53],look:[0,-.07],mood:'historic'},
 {id:'R21_INLAND_SEA',t0:104.2,t1:107.3,art:'historic',a:[.37,.10,10.32],b:[-.15,-.09,9.69],look:[0,0],mood:'historic'},
 {id:'R22_NORMAL_RIVERS',t0:107.3,t1:111.0,art:'atmos',a:[-.40,.04,10.46],b:[.30,.08,9.64],look:[.06,0],mood:'storm'},
 {id:'R23_THIS_ONE_STOPS',t0:111.0,t1:114.0,art:'atmos',a:[.04,.09,9.84],b:[.02,.08,9.65],look:[.03,0],mood:'storm',locked:true},
 {id:'R24_OCEAN_FEEDS',t0:114.0,t1:118.0,art:'atmos',a:[.45,.16,10.48],b:[-.46,-.10,9.42],look:[-.08,0],mood:'storm'},
 {id:'R25_WHAT_IF',t0:118.0,t1:120.0,art:'atmos',a:[-.04,-.05,9.73],b:[-.04,-.05,9.71],look:[0,0],mood:'storm',locked:true}
];
if(cuts[0].t0!==FROM||cuts[cuts.length-1].t1!==END||cuts.some((c,i)=>i&&Math.abs(c.t0-cuts[i-1].t1)>1e-6))throw Error('Noncanonical shot timeline');
const position={u:0},track=gsap.timeline({paused:true});
for(const sh of cuts){track.set(position,{u:0},sh.t0);track.to(position,{u:1,duration:sh.t1-sh.t0,ease:'power2.inOut'},sh.t0);}
const clamp=x=>Math.max(0,Math.min(1,x)),smooth=x=>{x=clamp(x);return x*x*(3-2*x)};
const rnd=i=>((Math.imul(i+17821,1664525)+1013904223)>>>0)/4294967295;
async function img(name){const o=new Image();o.src='assets/'+name;await o.decode();return o;}
const texture=o=>{const t=new THREE.Texture(o);t.needsUpdate=true;t.colorSpace=THREE.SRGBColorSpace;t.minFilter=THREE.LinearFilter;return t;};
const material=t=>new THREE.MeshBasicMaterial({map:t,transparent:true,depthWrite:false,depthTest:false,toneMapped:false,side:THREE.DoubleSide});
function layer(tex,z,order,overscan=1.20){
 const d=10-z,w=2*d*Math.tan(55*Math.PI/360)*ASPECT*overscan;
 const mesh=new THREE.Mesh(new THREE.PlaneGeometry(w,w/ASPECT),material(tex));
 mesh.position.z=z;mesh.renderOrder=order;world.add(mesh);return mesh;
}
const sets={};
for(const key of ['harbor','apartment','street','atmos','office','historic']){
 const images=await Promise.all(['far','mid','front'].map(n=>img(`${key}_${n}.webp`)));
 sets[key]=[layer(texture(images[0]),-4.0,0),layer(texture(images[1]),-.72,1),layer(texture(images[2]),2.17,3)];
}
const propImgs={};
for(const key of ['laptop','mug','phone','radio','clock'])propImgs[key]=await img(`prop_${key}.webp`);
propImgs.person=await img('protagonist_day1_still.webp');
const props={};
for(const [key,o] of Object.entries(propImgs)){
 const h=3.2,w=h*(o.width/o.height),mesh=new THREE.Mesh(new THREE.PlaneGeometry(w,h),material(texture(o)));
 mesh.position.set(1,-.58,2.42);mesh.renderOrder=5;mesh.visible=false;world.add(mesh);props[key]=mesh;
}
const atmosphereCanvas=document.createElement('canvas');atmosphereCanvas.width=W;atmosphereCanvas.height=H;
const ac=atmosphereCanvas.getContext('2d',{alpha:true});const atmosphereTex=new THREE.CanvasTexture(atmosphereCanvas);atmosphereTex.colorSpace=THREE.SRGBColorSpace;
const atmosphere=layer(atmosphereTex,2.61,7,1.21);
const eventCanvas=document.createElement('canvas');eventCanvas.width=W;eventCanvas.height=H;
const ec=eventCanvas.getContext('2d',{alpha:true});const eventTex=new THREE.CanvasTexture(eventCanvas);eventTex.colorSpace=THREE.SRGBColorSpace;
const eventLayer=layer(eventTex,2.81,8,1.22);
const titleCanvas=document.createElement('canvas');titleCanvas.width=W;titleCanvas.height=H;
const g=titleCanvas.getContext('2d',{alpha:true});const titleTex=new THREE.CanvasTexture(titleCanvas);titleTex.colorSpace=THREE.SRGBColorSpace;
const titleMesh=new THREE.Mesh(new THREE.PlaneGeometry(W,H),material(titleTex));titleMesh.renderOrder=999;foregroundUI.add(titleMesh);
function paintAtmosphere(t,shot){
 ac.clearRect(0,0,W,H);
 const indoor=['apartment','office'].includes(shot.art);const severe=shot.mood==='storm',historic=shot.mood==='historic';
 if(indoor){
  ac.save();ac.beginPath();
  if(shot.art==='apartment')ac.rect(380,55,960,650);
  else ac.rect(990,28,820,745);
  ac.clip();
 }
 const amount=severe?190:historic?155:indoor?52:115;
 const dx=severe?-105:historic?55:31;
 ac.lineCap='round';
 for(let i=0;i<amount;i++){
  const a=rnd(i+339),b=rnd(i+899),x=((rnd(i+91)*2400+t*(dx*(.6+a))+8000)%2280)-140;
  const y=((rnd(i+566)*1440+t*(severe?365:240)*(.50+b))%1400)-150;
  ac.strokeStyle=severe?'#b8d9f4':'#d4eafa';ac.globalAlpha=(.085+.20*a)*(indoor?.43:severe?.94:.73);
  ac.lineWidth=.7+a*1.7;ac.beginPath();ac.moveTo(x,y);ac.lineTo(x+dx*.12,y+(severe?30:20)+a*21);ac.stroke();
 }
 ac.globalAlpha=1;
 if(indoor)ac.restore();
 // Environmental motion and light: each effect depends on absolute time, never wall clock.
 if(shot.art==='atmos'&&(['R17_ATMOS_RIVER','R18_WATER_VAPOR','R24_OCEAN_FEEDS'].includes(shot.id))){
  for(let k=0;k<10;k++){
   const v=t-85,yy=156+k*28+10*Math.sin(v*.7+k),x=-500+(v*(32+k*5)+k*163)%(W+1000);
   ac.strokeStyle=k%3===0?'rgba(132,204,231,.10)':'rgba(180,216,235,.075)';ac.lineWidth=21+8*(k%3);
   ac.beginPath();ac.moveTo(x,yy);ac.bezierCurveTo(x+300,yy-50,x+620,yy+25,x+970,yy-65);ac.stroke();
  }
 }
 if(shot.art==='historic'){
  // Water is already present in the historical approved illustration. This adds ripples, not a false new flood.
  for(let i=0;i<26;i++){let x=rnd(100+i)*W,y=650+rnd(300+i)*400;const a=.11+.08*Math.sin(i+t*3);ac.strokeStyle=`rgba(200,234,235,${a})`;
   ac.lineWidth=1.1;ac.beginPath();ac.ellipse(x,y,15+45*rnd(i+800),2.3,0,0,6.28);ac.stroke();}
 }
 atmosphereTex.needsUpdate=true;
}
function paintEvents(t,s){
 ec.clearRect(0,0,W,H);const u=t-s.t0;
 if(s.id==='R07_COFFEE'){
  for(let i=0;i<5;i++){const x=1190+14*i+17*Math.sin(t*.8+i),y=472-((u*23+i*41)%205);
   ec.strokeStyle=`rgba(255,233,201,${.06+.11*(1-y/710)})`;ec.lineWidth=7;
   ec.beginPath();ec.moveTo(x,y+38);ec.bezierCurveTo(x-28,y+12,x+22,y-10,x,y-38);ec.stroke();}
 }
 if(s.id==='R11_MUDDY_RIVER'){
  // Subtle independently moving brown reflected water over river/muddy street only.
  let f=smooth(u/2.8);ec.fillStyle=`rgba(95,63,47,${.08*f})`;ec.fillRect(0,715,W,365);
  for(let i=0;i<25;i++){const x=(rnd(i+400)*W+t*12)%(W+100),y=790+rnd(i+500)*210;
   ec.strokeStyle=`rgba(185,147,99,${.09*f})`;ec.lineWidth=1.5;ec.beginPath();ec.ellipse(x,y,35,1.9,0,0,6.28);ec.stroke();}
 }
 if(['R17_ATMOS_RIVER','R18_WATER_VAPOR','R22_NORMAL_RIVERS','R23_THIS_ONE_STOPS','R24_OCEAN_FEEDS'].includes(s.id)){
  const moving=s.id!=='R23_THIS_ONE_STOPS';
  const v=moving?((t-85)*28):0;
  ec.save();ec.lineWidth=s.id==='R24_OCEAN_FEEDS'?15:11;ec.lineCap='round';
  for(let i=0;i<5;i++){
   const yy=280+i*31+16*Math.sin(t*.45+i),x=60+((v+i*227)%380);
   ec.strokeStyle=`rgba(128,211,244,${.07+i*.015})`;
   ec.beginPath();ec.moveTo(x,yy);ec.bezierCurveTo(x+260,yy-30,x+660,yy+42,x+1080,yy-65);ec.stroke();
  }
  ec.restore();
 }
 if(s.id==='R16_RADIO'){
  const a=.5+.5*Math.sin(t*10);ec.strokeStyle=`rgba(239,209,166,${.23*a})`;
  for(let i=0;i<3;i++){ec.lineWidth=4;ec.beginPath();ec.arc(1310,390,70+i*54,-.9,.9);ec.stroke();}
 }
 if(s.id==='R19_CALIFORNIA_1861'||s.id==='R20_SACRAMENTO_10FT'){
  const l=Math.max(0,1-Math.abs(t-98.85)/.22)*.11;
  if(l){ec.fillStyle=`rgba(224,229,239,${l})`;ec.fillRect(0,0,W,H);}
 }
 eventTex.needsUpdate=true;
}
function resetProps(s,t){
 for(const mesh of Object.values(props))mesh.visible=false;
 const set=(name,x,y,w,rot=0)=>{
  const m=props[name];m.visible=true;const aspect=m.geometry.parameters.width/m.geometry.parameters.height;
  // Mutating mesh scale never deforms a person; actor remains fixed with no pose/lip/gaze changes.
  m.scale.set(w/m.geometry.parameters.width,(w/aspect)/m.geometry.parameters.height,1);
  m.position.set(x,y,2.42);m.rotation.z=rot;
 };
 if(s.id==='R06_WORK_FROM_HOME')set('laptop',-2.70,-1.44,4.4,-.05);
 if(s.id==='R07_COFFEE')set('mug',2.60,-1.25,2.9);
 if(s.id==='R10_PHONE_WARNING')set('phone',2.3,-.70,2.30,.012*Math.sin(t*17));
 if(s.id==='R16_RADIO')set('radio',2.22,-1.10,4.0);
 if(s.id==='R13_LONG_WEEKEND')set('person',2.90,-1.35,2.45);
}
const font=(sz,weight=700)=>`${weight} ${sz}px Inter, system-ui, sans-serif`;
function pill(text,x,y,a=1,red=false){
 if(a<=0)return;g.save();g.globalAlpha=clamp(a);g.font=font(25,720);
 const w=Math.max(230,g.measureText(text).width+68);
 g.fillStyle=red?'rgba(83,27,32,.82)':'rgba(7,28,44,.78)';
 g.strokeStyle=red?'rgba(255,147,117,.70)':'rgba(187,225,233,.47)';g.lineWidth=2;
 g.beginPath();g.roundRect(x,y,w,66,13);g.fill();g.stroke();g.fillStyle=red?'#ffe6d9':'#dff5fd';g.fillText(text,x+34,y+43);g.restore();
}
function header(eyebrow,large,small,alpha=1){
 if(alpha<=0)return;g.save();g.globalAlpha=clamp(alpha);g.textAlign='center';
 g.shadowBlur=38;g.shadowColor='rgba(2,11,21,.95)';g.fillStyle='#f4f1e8';g.font=font(91,860);g.fillText(large,960,575);
 g.font=font(29,630);g.fillStyle='#b7e3ef';g.fillText(small,960,626);g.shadowBlur=0;
 if(eyebrow){g.font=font(20,700);g.fillStyle='#f0c88f';g.fillText(eyebrow.toUpperCase(),960,455);}g.restore();
}
function cloud(cx,cy,scale=1,color='#dbe9f5',rain=true){
 g.save();g.translate(cx,cy);g.scale(scale,scale);g.fillStyle=color;
 g.beginPath();g.arc(-16,2,14,0,Math.PI*2);g.arc(0,-9,20,0,Math.PI*2);g.arc(21,-2,16,0,Math.PI*2);g.roundRect(-30,-3,68,21,9);g.fill();
 if(rain){g.strokeStyle='rgba(122,197,231,.90)';g.lineWidth=3;for(let i=-1;i<=1;i++){g.beginPath();g.moveTo(i*17-5,26);g.lineTo(i*17-12,41);g.stroke();}}
 g.restore();
}
function forecast(t,second=false){
 g.save();const x=180,y=165,w=1560,h=680;
 g.fillStyle='rgba(4,18,34,.86)';g.strokeStyle='rgba(171,223,232,.60)';g.lineWidth=2;
 g.shadowBlur=28;g.shadowColor='rgba(2,9,15,.60)';g.beginPath();g.roundRect(x,y,w,h,32);g.fill();g.stroke();g.shadowBlur=0;
 g.fillStyle='#eff8ff';g.font=font(43,800);g.fillText(second?'NEXT 10 DAYS':'10-DAY FORECAST',x+60,y+94);
 g.fillStyle='#b2d9e9';g.font=font(21,530);g.fillText('COASTAL CITY  •  DAILY OUTLOOK',x+64,y+136);
 const colW=270,rowH=220;const baseX=x+102,baseY=y+200;
 const reveal=smooth((t-(second?77.3:73.9))/.55);
 for(let i=0;i<10;i++){
  let row=Math.floor(i/5),col=i%5,xx=baseX+col*291,yy=baseY+row*220;
  const a=smooth(reveal*12-i*.58);g.globalAlpha=a;
  g.fillStyle='rgba(21,53,73,.78)';g.strokeStyle='rgba(128,193,214,.43)';g.lineWidth=2;
  g.beginPath();g.roundRect(xx,yy,260,191,18);g.fill();g.stroke();
  g.fillStyle='#daeef3';g.font=font(22,650);g.fillText('DAY '+(i+1+(second?10:0)),xx+19,yy+43);
  cloud(xx+131,yy+79,1.03,'#dae6eb',true);
  g.font=font(18,620);g.fillStyle='#b8dfed';g.fillText('RAIN',xx+92,yy+166);
 }
 g.globalAlpha=1;
 if(second){g.fillStyle='rgba(237,149,117,.90)';g.fillRect(x+60,y+635,w-120,3);}
 g.restore();
}
function gadgetPhone(t){
 // Phone alert is an illustrated inset, not a moving human operating the phone.
 const x=180,y=187,w=1000,h=585;
 g.save();g.fillStyle='rgba(5,21,35,.85)';g.strokeStyle='rgba(190,227,237,.59)';g.lineWidth=2;
 g.beginPath();g.roundRect(x,y,w,h,27);g.fill();g.stroke();
 g.font=font(27,760);g.fillStyle='#c6e8f1';g.fillText('DAY 02   /   EMERGENCY ALERT',x+56,y+81);
 const pulse=.55+.45*Math.sin((t-61)*12);
 g.fillStyle=`rgba(191,60,58,${.75+.2*pulse})`;g.beginPath();g.roundRect(x+55,y+138,w-110,204,23);g.fill();
 g.fillStyle='#fff2e6';g.font=font(66,880);g.fillText('FLOOD WATCH',x+98,y+246);
 g.font=font(27,550);g.fillText('Coastal and river areas',x+105,y+307);
 const dismissed=t>=63.2;
 if(!dismissed){pill('DISMISS',x+85,y+426,1,false);} else {
  // Screen changes after an implied offscreen swipe. No hand animation.
  g.fillStyle='rgba(7,25,40,.90)';g.fillRect(x+35,y+135,w-65,250);
  g.fillStyle='#bad6e7';g.font=font(40,650);g.fillText('ALERT DISMISSED',x+105,y+278);
 }
 g.restore();
}
function graphic(t,s){
 g.clearRect(0,0,W,H);const u=t-s.t0;
 const vign=g.createRadialGradient(960,500,260,960,530,1150);
 vign.addColorStop(0,'rgba(2,7,15,0)');vign.addColorStop(1,'rgba(2,9,17,.43)');
 g.fillStyle=vign;g.fillRect(0,0,W,H);
 // Motivated scene lighting painted in exported pixels.
 if(s.mood==='warm'){
  const glow=g.createRadialGradient(1530,270,50,1480,330,810);
  glow.addColorStop(0,'rgba(250,179,87,.14)');glow.addColorStop(1,'rgba(240,143,60,0)');
  g.fillStyle=glow;g.fillRect(0,0,W,H);
 }
 if(s.mood==='alert'){
  const red=Math.max(0,1-Math.abs(u-.52)/.22)*.06;g.fillStyle=`rgba(255,81,76,${red})`;g.fillRect(0,0,W,H);
 }
 if(s.mood==='historic'){
  g.fillStyle='rgba(85,45,26,.12)';g.fillRect(0,0,W,H);
 }
 switch(s.id){
 case 'R01_TUESDAY':
  header('01 / BACK TO THE BEGINNING','TUESDAY','Nothing about the morning seems unusual.',smooth((u-.5)/.5)*smooth((3.60-u)/.5));
  break;
 case 'R02_24TH_FLOOR':
  pill('THE MERIDIAN  /  30 STORIES',104,90,smooth(u/.3));
  for(let i=0;i<30;i++){
   const yy=183+i*19.4,gone=i!==23,alpha=smooth((u-.3)/.8)*(gone?.18:.98);
   g.fillStyle=gone?`rgba(181,218,235,${alpha})`:`rgba(255,192,93,${alpha})`;
   g.fillRect(1755,yy,54,11);
  }
  pill('FLOOR 24',1611,880,smooth((u-.6)/.6),true);
  break;
 case 'R03_TWO_BLOCKS':
  pill('TWO BLOCKS FROM THE BAY',105,90,smooth(u/.4));
  g.strokeStyle='rgba(248,218,159,.70)';g.lineWidth=8;g.lineCap='round';
  g.beginPath();g.moveTo(268,874);g.lineTo(412,874);g.lineTo(412+201*smooth(u/2.6),874);g.stroke();
  g.fillStyle='#f1dec1';g.font=font(21,680);g.fillText('SCHEMATIC  /  BAY DISTANCE',286,838);
  break;
 case 'R04_HARBOR_VIEW':
  pill('HARBOR   /   RIVER MOUTH',105,90,smooth(u/.3));
  // Unobtrusive coordinate-style indicators; do not assert measured distances.
  break;
 case 'R05_LEL_OFFICE':
  pill('HARBOR AVENUE',105,90,smooth(u/.22));
  pill('GLASS OFFICE TOWER: LEL',106,166,smooth((u-.8)/.35));
  break;
 case 'R06_WORK_FROM_HOME':
  pill('WORK FROM HOME',107,86,smooth((u-.2)/.3));
  break;
 case 'R07_COFFEE':
  pill('DAY ONE   /   COFFEE & RAIN',105,86,smooth((u-.25)/.32));
  break;
 case 'R08_CLOSE_WINDOW':
  pill('YOU CLOSE THE WINDOW',105,86,smooth((u-.10)/.2));
  // Window appears to shut through an editorial shutter-like before/after reveal;
  // no moving arms or unseen-character puppet animation.
  if(u>1.6){g.fillStyle=`rgba(7,25,40,${.10*smooth((u-1.6)/.7)})`;g.fillRect(240,80,1190,600);}
  break;
 case 'R09_DAY_TWO':
  header('ONE NORMAL DAY PASSES','DAY TWO','The first warning arrives.',smooth(u/.25)*smooth((2.44-u)/.2));
  break;
 case 'R10_PHONE_WARNING':
  gadgetPhone(t);
  break;
 case 'R11_MUDDY_RIVER':
  pill('DAY THREE   /   THE RIVER CHANGES',100,86,smooth((u-.10)/.3),true);
  pill('BROWN AS CHOCOLATE MILK',101,168,smooth((u-1.1)/.32));
  break;
 case 'R12_SCHOOLS_CLOSE':
  pill('SCHOOLS CLOSED',104,93,smooth(u/.22),true);
  break;
 case 'R13_LONG_WEEKEND':
  header('YOUR FIRST REACTION','LONG WEEKEND','It still feels like somebody else’s problem.',smooth((u-.35)/.4)*smooth((2.9-u)/.38));
  break;
 case 'R14_FIRST_TEN_FORECAST':forecast(t,false);break;
 case 'R15_NEXT_TEN_FORECAST':forecast(t,true);break;
 case 'R16_RADIO':
  pill('THE RADIO EXPLAINS IT',105,85,smooth(u/.23));
  pill('ATMOSPHERIC RIVER',105,164,smooth((u-1.30)/.29));
  break;
 case 'R17_ATMOS_RIVER':
  header('A REAL PHENOMENON','ATMOSPHERIC RIVER','An immense band of water vapor in the sky.',smooth((u-.3)/.6)*smooth((4.6-u)/.32));
  break;
 case 'R18_WATER_VAPOR':
  pill('WARM OCEAN   →   COAST',104,86,smooth(u/.3));
  g.save();g.globalAlpha=.56*smooth((u-.4)/1.1);g.strokeStyle='#99d5e8';g.lineWidth=9;g.lineCap='round';
  g.beginPath();g.moveTo(190,795);g.bezierCurveTo(510,610,870,492,1560,307);g.stroke();g.restore();
  break;
 case 'R19_CALIFORNIA_1861':
  header('HISTORICAL EXAMPLE','CALIFORNIA · 1861','A storm rains for 43 days.',smooth((u-.5)/.5)*smooth((5.02-u)/.4));
  break;
 case 'R20_SACRAMENTO_10FT':
  pill('SACRAMENTO  /  HISTORICAL FLOOD',100,87,smooth(u/.27));
  g.save();g.globalAlpha=smooth((u-.5)/.5);g.font=font(108,900);g.textAlign='center';g.fillStyle='#f1dfb8';
  g.shadowBlur=28;g.shadowColor='rgba(4,10,16,.9)';g.fillText('10 FEET',960,645);g.restore();
  break;
 case 'R21_INLAND_SEA':
  header('THE CENTRAL VALLEY','INLAND SEA','The flood spreads across the valley.',smooth((u-.25)/.4)*smooth((2.9-u)/.25));
  break;
 case 'R22_NORMAL_RIVERS':
  pill('NORMALLY: MOVE ON IN A FEW DAYS',104,90,smooth(u/.3));
  break;
 case 'R23_THIS_ONE_STOPS':
  header('BUT THIS STORM','DOESN’T MOVE','The atmospheric river stalls over the coast.',smooth((u-.2)/.33)*smooth((2.9-u)/.23));
  break;
 case 'R24_OCEAN_FEEDS':
  pill('STORM STUCK OVER THE COAST',104,90,smooth(u/.32));
  pill('THE OCEAN KEEPS FEEDING IT',104,168,smooth((u-1.1)/.35),true);
  break;
 case 'R25_WHAT_IF':
  header('THE QUESTION','WHAT IF?','What happens when the rain never moves?',smooth(u/.38));
  break;
 }
 // Professional, restrained show-identity footer.
 const a=smooth((t-30.12)/.36)*smooth((119.84-t)/.26);
 g.fillStyle=`rgba(181,226,239,${.32*a})`;g.fillRect(105,991,97,3);
 g.font=font(20,590);g.fillStyle=`rgba(228,241,246,${.72*a})`;g.fillText('WHAT IF IT NEVER STOPPED RAINING?',104,1037);
 // Precise editorial cut accent never masks actor or location.
 const edge=Math.min(t-s.t0,s.t1-t);const hit=(1-smooth(edge/.13))*.17;
 if(hit>0){g.fillStyle=`rgba(9,18,31,${hit})`;g.fillRect(0,0,W,H);}
 titleTex.needsUpdate=true;
}
window.renderFrame=async t=>{
 if(!Number.isFinite(t)||t<FROM||t>=END)throw Error('Canonical 30 to 120 seconds only: '+t);
 const shot=cuts.find(s=>t>=s.t0&&t<s.t1);if(!shot)throw Error('Timeline gap '+t);
 track.seek(t,false);
 const p=position.u;
 camera.position.set(shot.a[0]+(shot.b[0]-shot.a[0])*p,shot.a[1]+(shot.b[1]-shot.a[1])*p,shot.a[2]+(shot.b[2]-shot.a[2])*p);
 const target=new THREE.Vector3(shot.look[0]+camera.position.x*.07,shot.look[1]+Math.sin(p*Math.PI)*.035,0);
 camera.lookAt(target);
 for(const [key,ls] of Object.entries(sets))for(let i=0;i<ls.length;i++){
  ls[i].visible=key===shot.art;
  if(ls[i].visible){ls[i].position.x=i===0?0:i===1?.024*Math.sin(t*.43):.043*Math.sin(t*.51);ls[i].position.y=i===2?.015*Math.sin(t*.9):0;}
 }
 resetProps(shot,t);paintAtmosphere(t,shot);paintEvents(t,shot);graphic(t,shot);
 renderer.clear();renderer.render(world,camera);renderer.clearDepth();renderer.render(foregroundUI,uiCamera);
 return {t,shot:shot.id,category:shot.mood,three_layer_depth:true,static_characters:true,camera_x:camera.position.x,camera_z:camera.position.z,source_art:shot.art};
};
// Deterministic Web Audio OfflineAudioContext ambience. Mono PCM 24 kHz, exact 90s.
window.exportRainSfx=async()=>{
 const rate=24000,n=90*rate,off=new OfflineAudioContext(1,n,rate);
 const buf=off.createBuffer(1,n,rate),data=buf.getChannelData(0);
 let seed=37811;for(let i=0;i<n;i++){seed=(Math.imul(seed,1664525)+1013904223)>>>0;data[i]=(seed/4294967295*2-1)*.20;}
 const src=off.createBufferSource();src.buffer=buf;
 const low=off.createBiquadFilter();low.type='lowpass';low.frequency.value=2000;
 const gain=off.createGain();gain.gain.value=.22;
 for(const [abs,level] of [[30,.17],[48,.09],[58,.12],[64,.19],[74,.11],[85,.20],[95,.24],[107,.17],[118,.23],[120,.12]])gain.gain.linearRampToValueAtTime(level,Math.max(0,abs-30));
 src.connect(low);low.connect(gain);gain.connect(off.destination);src.start(0);
 function ping(abs,freq,vol,duration){const t=abs-30,o=off.createOscillator(),v=off.createGain();o.type='sine';o.frequency.setValueAtTime(freq,t);o.frequency.exponentialRampToValueAtTime(Math.max(35,freq*.55),t+duration);
 v.gain.setValueAtTime(.0001,t);v.gain.exponentialRampToValueAtTime(vol,t+.016);v.gain.exponentialRampToValueAtTime(.0001,t+duration);
 o.connect(v);v.connect(off.destination);o.start(t);o.stop(t+duration+.001);}
 ping(53.22,420,.035,.16); // ceramic coffee cup on table, no visible human motion
 ping(61.35,740,.09,.24);ping(61.68,880,.07,.22); // phone warning
 ping(75.35,300,.022,.23);ping(79.30,400,.025,.22); // weather page changes
 ping(82.90,155,.034,.48); // radio warming up
 ping(99.2,58,.17,1.2); // thunder over historical water
 ping(111.2,53,.13,.9); // stalled atmospheric river
 const rendered=await off.startRendering(),pcm=rendered.getChannelData(0);
 const out=new ArrayBuffer(44+n*2),v=new DataView(out),u=new Uint8Array(out);
 function chars(i,s){for(let k=0;k<s.length;k++)u[i+k]=s.charCodeAt(k)}
 chars(0,'RIFF');v.setUint32(4,36+n*2,true);chars(8,'WAVEfmt ');
 v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,rate,true);v.setUint32(28,rate*2,true);v.setUint16(32,2,true);v.setUint16(34,16,true);
 chars(36,'data');v.setUint32(40,n*2,true);
 for(let i=0;i<n;i++)v.setInt16(44+i*2,Math.round(Math.max(-1,Math.min(1,pcm[i]))*32767),true);
 let str='';for(let i=0;i<u.length;i+=8192)str+=String.fromCharCode(...u.subarray(i,i+8192));
 return btoa(str);
};
await window.renderFrame(30);
window.ready=true;
