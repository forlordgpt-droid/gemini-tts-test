const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs=require('fs'),path=require('path');
(async()=>{
 const server=spawn(path.resolve('node_modules/.bin/vite'),['--host','127.0.0.1','--port','5197','--strictPort'],{stdio:['ignore','pipe','pipe']});
 let log='';server.stdout.on('data',b=>log+=b);server.stderr.on('data',b=>log+=b);
 let browser;try{
  let good=false;
  for(let i=0;i<140;i++){if(server.exitCode!==null)throw Error('Vite server died: '+log);try{if((await fetch('http://127.0.0.1:5197/')).ok){good=true;break;}}catch{}await new Promise(r=>setTimeout(r,400));}
  if(!good)throw Error('Vite server not ready: '+log);
  browser=await chromium.launch({channel:'chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:1920,height:1080},acceptDownloads:true});
  page.on('console',m=>console.log('[BROWSER '+m.type()+'] '+m.text()));
  page.on('pageerror',e=>console.error('[BROWSER ERROR]',e.stack||e.message));
  await page.goto('http://127.0.0.1:5197/',{waitUntil:'networkidle',timeout:60000});
  await page.waitForFunction('window.__HUNYUAN_READY===true || window.__HUNYUAN_ERROR',null,{timeout:120000});
  const err=await page.evaluate(()=>window.__HUNYUAN_ERROR);if(err)throw Error('Scene error: '+err);
  const configs=await page.evaluate(async()=>{
   const out=[];
   for(const codec of ['avc1.420028','avc1.42E01F']){
     for(const hardwareAcceleration of [undefined,'prefer-software']){
       const c={codec,width:1920,height:1080,bitrate:5000000,framerate:30};
       if(hardwareAcceleration)c.hardwareAcceleration=hardwareAcceleration;
       const r=await VideoEncoder.isConfigSupported(c);
       out.push({codec,hardwareAcceleration:hardwareAcceleration||'default',supported:r.supported});
     }
   }return out;
  });console.log('FULL CHROMIUM CODEC PROBES',JSON.stringify(configs));
  const diag=await page.evaluate(async()=>{
   const {quickSmoke}=await import('/smoke-encode.js');
   return await quickSmoke();
  });console.log('MEDIABUNNY TWO-FRAME PASS',JSON.stringify(diag));
  await page.locator('#stage').screenshot({path:'smoke-frame.png'});
  fs.writeFileSync('smoke-qc.json',JSON.stringify({codec:configs,diag,status:'TWO_FRAME_TECH_PASS_VISUAL_REVIEW_REQUIRED'},null,2));
 }finally{if(browser)await browser.close();server.kill('SIGTERM');}
})().catch(e=>{console.error(e.stack||String(e));process.exitCode=1;});
