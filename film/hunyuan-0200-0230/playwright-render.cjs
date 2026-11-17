const { chromium } = require('playwright');
const fs=require('node:fs'),path=require('node:path'),{spawn}=require('node:child_process');
const shard=Number(process.env.SHARD_INDEX||0), gate=process.env.GATE==='1', onlySfx=process.env.SFX_ONLY==='1';
const frames=gate?150:300, out=path.resolve('qc');
fs.mkdirSync(out,{recursive:true});
const server=spawn(path.resolve('node_modules/.bin/vite'),['--host','127.0.0.1','--port','5196','--strictPort'],{stdio:['ignore','pipe','pipe']});
let log=''; server.stdout.on('data',b=>log+=b.toString());server.stderr.on('data',b=>log+=b.toString());
const delay=t=>new Promise(r=>setTimeout(r,t));
async function waitServer(){for(let i=0;i<180;i++){if(server.exitCode!==null)throw Error('Vite exited: '+log);try{const r=await fetch('http://127.0.0.1:5196/');if(r.ok)return;}catch{}await delay(500);}throw Error('Required local browser server failed: '+log);}
(async()=>{
 const errors=[];let browser;try{
 await waitServer();
 browser=await chromium.launch({channel:'chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1920,height:1080},acceptDownloads:true,deviceScaleFactor:1});
 page.on('pageerror',e=>errors.push('PAGE '+e.message));page.on('console',m=>{if(m.type()==='error')errors.push('CONSOLE '+m.text());});
 page.on('response',r=>{if(r.status()>=400)errors.push('HTTP '+r.status()+' '+r.url());});
 await page.goto('http://127.0.0.1:5196/?shard='+shard+'&frames='+frames,{waitUntil:'networkidle',timeout:90000});
 await page.waitForFunction('window.__HUNYUAN_READY===true || !!window.__HUNYUAN_ERROR',null,{timeout:120000});
 if(await page.evaluate(()=>!!window.__HUNYUAN_ERROR))throw Error('Original-rig/Three.js scene initialization hard failure: '+await page.evaluate(()=>window.__HUNYUAN_ERROR));
 if(errors.length)throw Error('Browser asset/console failure '+errors.join('\n'));
 const checks=await page.evaluate(async()=>{
  const c=document.querySelector('#stage');const gl=c.getContext('webgl2')||c.getContext('webgl');
  const supported=await VideoEncoder.isConfigSupported({codec:'avc1.420028',width:1920,height:1080,bitrate:5000000,framerate:30});
  const checks=[];
  for(const hardwareAcceleration of [undefined,'prefer-software','prefer-hardware']){
    const cfg={codec:'avc1.420028',width:1920,height:1080,framerate:30,bitrate:5000000};
    if(hardwareAcceleration)cfg.hardwareAcceleration=hardwareAcceleration;
    try{checks.push({acceleration:hardwareAcceleration||'no-preference',...(await VideoEncoder.isConfigSupported(cfg))});}
    catch(e){checks.push({acceleration:hardwareAcceleration||'no-preference',error:String(e)});}
  }
  return {canvas:[c.width,c.height],videoEncoder:typeof VideoEncoder,h264:supported.supported,webcodecsProbes:checks,chromiumAgent:navigator.userAgent,isSecureContext,gl:!!gl,rig:typeof window.HunyuanArt,world:typeof window.HunyuanWorld2D,plans:window.__planSummary};
 });
 if(!checks.h264||!checks.gl||checks.rig!=='object'||checks.world!=='function')throw Error('Required codec/WebGL/native rig unavailable: '+JSON.stringify(checks));
 const base=shard*10;const times=gate?[0,2.5,4.966666]:[base,base+5,base+9.9666667];
 for(let i=0;i<times.length;i++){await page.evaluate(t=>window.renderAt(t),times[i]);await page.locator('#stage').screenshot({path:path.join(out,'frame_'+shard+'_'+i+'.png'),animations:'disabled'});}
 if(!onlySfx){
  const downloadPromise=page.waitForEvent('download',{timeout:25*60*1000});
  await page.click('#export');const d=await downloadPromise;
  const fn=gate?'gate_5s.mp4':'part_'+shard+'.mp4';await d.saveAs(path.join(out,fn));
  if(fs.statSync(path.join(out,fn)).size<20000)throw Error('Encoded MP4 too small');
 }
 if(gate||onlySfx){
  const sfxDownload=page.waitForEvent('download',{timeout:180000});
  await page.click('#sfx');const d=await sfxDownload;await d.saveAs(path.join(out,'original_sfx_30s.wav'));
  if(fs.statSync(path.join(out,'original_sfx_30s.wav')).size<100000)throw Error('Original OfflineAudioContext effects invalid');
 }
 if(errors.length)throw Error('Browser errors '+errors.join('\n'));
 const summary=await page.evaluate(()=>window.__qc);
 fs.writeFileSync(path.join(out,'browser_qc.json'),JSON.stringify({status:'BROWSER_TECH_PASS_VISUAL_REVIEW_REQUIRED',shard,gate,checks,summary,errors},null,2));
 console.log('BROWSER PASS',JSON.stringify({shard,gate,checks,summary}));
 } finally {if(browser)await browser.close();server.kill('SIGTERM');}
})().catch(e=>{console.error(e.stack||e);server.kill('SIGTERM');process.exitCode=1;});
