#!/usr/bin/env node
/* Export exact new scene 0-10 ambient SFX from mandatory WebAudio OfflineAudioContext.
 * Ensures no ringtone before 10s; uses original illustrated Three.js GSAP application.
 * No chargeable API, no alternative audio generator, no new packages.
 */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),cp=require('node:child_process');
const {chromium}=require('/opt/cinematic/node_modules/playwright');
const project=path.resolve('film/story5-v3/narrated-first10');
const out=path.resolve('sfx');
fs.mkdirSync(out,{recursive:true});
const main=path.join(project,'main.js'),scene=fs.readFileSync(main,'utf8');
for(const forbidden of ["id:'PHONE'","'NOAH'","'INCOMING CALL'"]){
 if(scene.includes(forbidden)) throw Error('Invalid old story scene '+forbidden);
}
if(!scene.includes("OfflineAudioContext"))throw Error('Required Web Audio OfflineAudioContext missing');
const esbuild='/opt/cinematic/node_modules/.bin/esbuild';
if(!fs.existsSync(esbuild))throw Error('Exact esbuild unavailable; stop');
cp.execFileSync(esbuild,[main,'--bundle','--format=esm','--outfile='+path.join(project,'app.js')],{env:{...process.env,NODE_PATH:'/opt/cinematic/node_modules'}});
const types={'.html':'text/html','.js':'application/javascript','.webp':'image/webp','.jpg':'image/jpeg','.png':'image/png','.json':'application/json','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{
 try{
  const uri=new URL(req.url,'http://localhost').pathname;
  if(uri==='/favicon.ico'){res.writeHead(204);res.end();return}
  const file=path.resolve(project,'.'+decodeURIComponent(uri==='/'?'/index.html':uri));
  if(!file.startsWith(project+path.sep))throw Error('Bad file request');
  res.writeHead(200,{'content-type':types[path.extname(file)]||'application/octet-stream'});
  res.end(fs.readFileSync(file));
 }catch(e){res.writeHead(404);res.end('Not Found')}
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,channel:'chromium',args:['--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
 try{
  const page=await browser.newPage({viewport:{width:1920,height:1080},acceptDownloads:true});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',x=>{if(x.type()==='error')errors.push(x.text())});
  await page.goto('http://127.0.0.1:'+server.address().port+'/');
  await page.waitForFunction(()=>window.ready===true && typeof window.exportSfx==='function',null,{timeout:90000});
  const downloaded=page.waitForEvent('download',{timeout:60000});
  const info=await page.evaluate(()=>window.exportSfx());
  const file=await downloaded;
  const target=path.join(out,'story5_offline_web_audio_sfx_10.wav');
  await file.saveAs(target);
  if(errors.length)throw Error('WebAudio browser errors: '+errors.join(' | '));
  const data=JSON.parse(cp.execFileSync('ffprobe',['-v','error','-show_entries','stream=codec_name,channels,sample_rate:format=duration','-of','json',target],{encoding:'utf8'}));
  if(data.streams[0].codec_name!=='pcm_s16le'||Number(data.streams[0].channels)!==1||Number(data.streams[0].sample_rate)!==24000)throw Error('Mandatory offline WebAudio PCM failed');
  if(Math.abs(Number(data.format.duration)-10)>.02||fs.statSync(target).size<400000)throw Error('Unexpected original 10s SFX duration/bytes');
  fs.writeFileSync(path.join(out,'SFX_QA.json'),JSON.stringify({status:'PASS',provider:'Web Audio OfflineAudioContext',music_generated:false,ring_tone_in_first10:false,sfx_seconds:Number(data.format.duration),bytes:fs.statSync(target).size,render_state:info,payment:0},null,2));
  console.log('PASS exact WebAudio 10s ambience, no phone ring',fs.statSync(target).size);
 }finally{await browser.close();await new Promise(r=>server.close(r))}
})().catch(e=>{console.error('STORY5_OFFLINE_WEBAUDIO_SFX_ERROR',e.stack);process.exitCode=1});
