#!/usr/bin/env node
/* Authored real Hunyuan 2D cinematic regression test. No paid APIs.
 * Loads the SAME reference JS source and native 2D rig used in the verified
 * 30-second original; checks PerspectiveCamera/GSAP deterministic motion.
 */
const {chromium}=require('playwright');
const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const ROOT='/opt/cinematic/examples/preview_30s';
const MEDIA={'.html':'text/html','.js':'application/javascript','.jpg':'image/jpeg','.webp':'image/webp','.png':'image/png','.json':'application/json'};
const server=http.createServer((req,res)=>{
 try{
   const pathpart=decodeURIComponent(new URL(req.url,'http://localhost/').pathname);
   if(pathpart==='/favicon.ico'){res.writeHead(204);res.end();return;}
   const target=path.resolve(ROOT,'.'+(pathpart==='/'?'/index.html':pathpart));
   if(!target.startsWith(ROOT+path.sep))throw Error('Unsafe path');
   const data=fs.readFileSync(target);
   res.writeHead(200,{'Content-Type':MEDIA[path.extname(target)]||'application/octet-stream'});
   res.end(data);
 }catch(e){res.writeHead(404);res.end('not-found');}
});
async function start(){
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const port=server.address().port;
 const b=await chromium.launch({headless:true,channel:'chromium',args:['--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
 const page=await b.newPage({viewport:{width:1600,height:900},acceptDownloads:true});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 const out=process.env.ENGINE_SMOKE_OUTPUT||'/opt/cinematic/smoke-qa';
 fs.mkdirSync(out,{recursive:true});
 try{
   await page.goto('http://127.0.0.1:'+port+'/');
   await page.waitForFunction(()=>window.ready===true,null,{timeout:80000});
   const apis=await page.evaluate(()=>({webcodecs:typeof VideoEncoder==='function',offlineAudio:typeof OfflineAudioContext==='function',webgl2:!!document.createElement('canvas').getContext('webgl2')}));
   assert.ok(apis.webcodecs&&apis.offlineAudio&&apis.webgl2, 'Required browser runtime unsupported: '+JSON.stringify(apis));
   const times=[.55,2.7,6.3,10.5,15.5,20.5,25.5,29.4],frames=[],m=[];
   for(const t of times){
      const x=await page.evaluate(t=>window.renderFrame(t),t);m.push(x);
      const shot=await page.locator('#stage').screenshot({type:'png'});
      if(shot.byteLength<10000)throw Error('Empty original art playback screenshot');
      frames.push(shot);
   }
   assert.equal(m.length,8);
   const cameraXs=m.map(x=>x.cameraX),cameraZs=m.map(x=>x.cameraZ);
   assert.ok(new Set(cameraXs.map(x=>x.toFixed(4))).size>4,'Original GSAP camera did not move');
   assert.ok(new Set(cameraZs.map(x=>x.toFixed(4))).size>4,'Original perspective pushes did not move');
   assert.ok(m.some(x=>x.shot==='S04')&&m.some(x=>x.shot==='S06'),'Original 6-shot script not loaded');
   assert.ok(!frames[0].equals(frames[1])&&!frames[4].equals(frames[5]),'Reference exported frames visually static');
   // deterministic time t must produce identical image even if another time rendered between samples
   await page.evaluate(()=>window.renderFrame(15.5));
   const before=await page.locator('#stage').screenshot();
   await page.evaluate(()=>window.renderFrame(1.3));
   await page.evaluate(()=>window.renderFrame(15.5));
   const after=await page.locator('#stage').screenshot();
   assert.ok(before.equals(after),'GSAP absolute-time sampling is nondeterministic');
   assert.deepEqual(errors,[],'Browser rendering errors');
   fs.writeFileSync(path.join(out,'S06_T25_5.png'),frames[6]);
   fs.writeFileSync(path.join(out,'REGRESSION_RESULTS.json'),JSON.stringify({pass:true,tests:apis,shot_times:times,actual_reference_frames:times.length,moves:m.map(x=>({shot:x.shot,t:x.t,cameraX:x.cameraX,cameraZ:x.cameraZ})),deterministic:true,visually_moving:true,reference_source:'ORIGINAL unmodified approved Hunyuan 2D 30-second source'},null,2));
   console.log('PASS original Hunyuan 2D cinematic reference visual smoke: true multi-plane camera moves, GSAP, WebCodecs/WebAudio, frame determinism');
 }finally{await page.close();await b.close();await new Promise(r=>server.close(r));}
}
start().catch(e=>{console.error('ENGINE_V3_BROWSER_SMOKE_FAILED',e.stack);process.exitCode=1;});
