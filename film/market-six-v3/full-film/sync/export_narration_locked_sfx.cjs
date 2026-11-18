#!/usr/bin/env node
/* Original Hunyuan V3 locked Web Audio OfflineAudioContext environmental score.
 * All sounds are authored deterministic synthesis from exact 15-chapter story beats.
 * No music service, no extra credit-spending requests, no dialogue replacements.
 */
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const {chromium}=require('/opt/cinematic/node_modules/playwright');
const blueprint=JSON.parse(fs.readFileSync('film/market-six-v3/full-film/SHOT_IMAGE_BLUEPRINT.json','utf8'));
const aligned=JSON.parse(fs.readFileSync('sync_results/MEASURED_NARRATION_TO_SHOT_CUTS.json','utf8'));
if(aligned.status!=='MEASURED_131_EXACT_USER_SCRIPT_CUES_FROM_EXISTING_KIE_FLASH_SPEECH')throw Error('Required real speech alignment unavailable');
const cues=new Map(aligned.shots.map(s=>[s.key,s]));
if(cues.size!==131)throw Error('Measured original 131 story beats missing');
if(blueprint.image_model!=='gpt-image-2.5-lower'||blueprint.speech_model!=='google/gemini-3-8-flash-tts')throw Error('User specified paid model lock failed');
const out=path.resolve('sfx_sync');fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({channel:'chromium',headless:true,args:['--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
 const page=await browser.newPage({acceptDownloads:true,viewport:{width:600,height:400}});
 try{
  await page.goto('about:blank');
  const parts=[];
  for(let ch=1;ch<=15;ch++){
   const shots=blueprint.shots.filter(x=>x.chapter===ch).map(s=>{
     const t=cues.get(s.key);if(!t)throw Error('No actual audible cut for '+s.key);
     return {...s,global_start:t.start_sec,global_end:t.end_sec};
   });
   const origin=ch===1?30:ch*60-60,length=ch===1?30:60;
   if(shots.length!==(ch===1?5:9))throw Error('Original film shot count violated chapter '+ch);
   const pending=page.waitForEvent('download',{timeout:240000});
   const meta=await page.evaluate(async({ch,shots,origin,length})=>{
     const rate=24000,n=rate*length,offline=new OfflineAudioContext(1,n,rate);
     const master=offline.createGain();master.gain.value=.16;master.connect(offline.destination);
     let seed=98321+ch*71361;
     const rnd=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return ((seed/4294967296)*2)-1};
     const noise=offline.createBuffer(1,n,rate),z=noise.getChannelData(0);
     for(let i=0;i<n;i++)z[i]=rnd()*(ch>=12?.19:.13);
     const src=offline.createBufferSource();src.buffer=noise;
     const filter=offline.createBiquadFilter();filter.type='lowpass';filter.frequency.value=(ch===1||ch>=12)?420:650;
     src.connect(filter);filter.connect(master);src.start(0);
     // Slow original dramatic tonal underscoring, no external recorded music.
     const tone=(at,dur,f0,f1,volume,wave='triangle')=>{
       if(at<0||at>=length)return;
       let end=Math.min(length-.004,at+dur);if(end-at<.02)return;
       const o=offline.createOscillator(),a=offline.createGain();o.type=wave;
       o.frequency.setValueAtTime(Math.max(1,f0),at);
       o.frequency.exponentialRampToValueAtTime(Math.max(1,f1),end);
       a.gain.setValueAtTime(.00001,at);
       a.gain.linearRampToValueAtTime(volume,Math.min(end-.01,at+.05));
       a.gain.exponentialRampToValueAtTime(.00001,end);
       o.connect(a);a.connect(master);o.start(at);o.stop(end);
     };
     tone(0,length-.01,ch<=3?55:61,ch<=3?41:48,.09,'sine');
     tone(3,length-3.01,82,75,.055,'triangle');
     let hitCount=0;
     for(const sh of shots){
       const at=sh.global_start-origin,desc=sh.description.toLowerCase();
       if(/flood|water|river|rain|surge|storm|leak|roof/.test(desc)){
         tone(at+.09,Math.min(2.2,length-at-.2),105,32,.19,'triangle');
         for(let j=0;j<4;j++)tone(at+.29+j*.41,.25,250+j*37,50,.044,'sine');
       }
       if(/knock|pound|hit|slam|impact|shutter|door|explode|crack|glass|bang|truck|collapse/.test(desc)){
         for(let j=0;j<2;j++){const d=at+.32+j*.21;tone(d,.31,230-j*42,30,.54,'sawtooth');tone(d+.02,.45,80,24,.34,'triangle');hitCount++;}
       }
       if(/radio|signal|monitor|alert|warning|phone|camera|light|horn|flashes/.test(desc)){
         for(let j=0;j<5;j++)tone(at+.16+j*.25,.13,920+j*35,430,.12,'sine');
       }
       if(/footstep|walk|rush|run|climb|step|carry|push|stair/.test(desc)){
         for(let j=0;j<5;j++)tone(at+.22+j*.48,.13,130,34,.17,'triangle');
       }
       if(/generator|smoke|fire|freezer|power|electric|light/.test(desc)){
         tone(at+.2,Math.min(2.3,length-at-.25),270,75,.095,'sawtooth');
       }
       if(/clara|jonah|water bottle|ledger|sick|cracked|count/.test(desc)){
         tone(at+.45,Math.min(.42,length-at-.50),220,150,.035,'sine');
       }
     }
     const pcm=(await offline.startRendering()).getChannelData(0),wav=new ArrayBuffer(44+pcm.length*2),d=new DataView(wav),bytes=new Uint8Array(wav);
     const s=(o,t)=>{for(let j=0;j<t.length;j++)bytes[o+j]=t.charCodeAt(j)};
     s(0,'RIFF');d.setUint32(4,36+pcm.length*2,true);s(8,'WAVE');s(12,'fmt ');
     d.setUint32(16,16,true);d.setUint16(20,1,true);d.setUint16(22,1,true);d.setUint32(24,rate,true);
     d.setUint32(28,rate*2,true);d.setUint16(32,2,true);d.setUint16(34,16,true);s(36,'data');d.setUint32(40,pcm.length*2,true);
     for(let i=0;i<pcm.length;i++)d.setInt16(44+i*2,Math.round(Math.max(-1,Math.min(1,pcm[i]))*32767),true);
     const file='MARKET_SIX_ORIGINAL_WEBAUDIO_CH'+String(ch).padStart(2,'0')+'.wav';
     const link=document.createElement('a');link.href=URL.createObjectURL(new Blob([wav],{type:'audio/wav'}));link.download=file;
     document.body.appendChild(link);link.click();link.remove();
     return {chapter:ch,seconds:length,events:shots.length,metal_impacts:hitCount,bytes:wav.byteLength,provider:'Web Audio OfflineAudioContext',paid_generation_calls:0};
   },{ch,shots,origin,length});
   const download=await pending;
   const target=path.join(out,'MARKET_SIX_ORIGINAL_WEBAUDIO_CH'+String(ch).padStart(2,'0')+'.wav');
   await download.saveAs(target);
   const probe=JSON.parse(cp.execFileSync('ffprobe',['-v','error','-show_entries','stream=codec_name,sample_rate,channels:format=duration','-of','json',target],{encoding:'utf8'}));
   if(probe.streams[0].codec_name!=='pcm_s16le'||Number(probe.streams[0].sample_rate)!==24000||Math.abs(Number(probe.format.duration)-length)>.005)throw Error('Mandatory offline WebAudio WAV QA failed '+ch);
   parts.push({...meta,file:path.basename(target)});
   console.log('PASS WEBAUDIO STORY CHAPTER',ch,JSON.stringify(meta));
  }
  fs.writeFileSync(path.join(out,'ORIGINAL_15_CHAPTER_OFFLINE_AUDIO_QA.json'),JSON.stringify({status:'PASS',exact_required:'Web Audio OfflineAudioContext',parts,paid_generation_requests:0},null,2));
  console.log('ALL 15 SOUNDTRACK CHAPTERS SYNCHRONIZED TO MEASURED ORIGINAL VOICE AND GENERATED USING REQUIRED WEB AUDIO; ZERO API CREDITS');
 }finally{await browser.close()}
})().catch(e=>{console.error('MARKET_SIX_WEBAUDIO_BLOCKER',e.stack);process.exitCode=1});
