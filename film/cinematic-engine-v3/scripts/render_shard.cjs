#!/usr/bin/env node
/* Scale-proof authored image-first 2.5D shard runner.
 * Uses prebuilt Playwright, Three.js/Gsap story module, injected shared
 * WebCodecs+Mediabunny absolute-animation/local-video-time exporter.
 * Zero paid generation, no npm or system installations on render jobs.
 */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),cp=require('node:child_process'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const args=process.argv.slice(2);
function opt(name,def){const idx=args.indexOf('--'+name);return idx>=0?args[idx+1]:def}
const project=path.resolve(opt('project',''));
const start=Number(opt('start-frame','-1')),count=Number(opt('frame-count','0'));
const out=path.resolve(opt('out','shard-output'));
const source=opt('main','main.js');
const fmt={'.html':'text/html','.js':'text/javascript','.webp':'image/webp','.jpg':'image/jpeg','.png':'image/png','.svg':'image/svg+xml','.json':'application/json'};
if(!fs.existsSync(project)||!fs.statSync(project).isDirectory())throw Error('Expected already prepared scene-specific project directory');
if(!Number.isInteger(start)||start<0||!Number.isInteger(count)||count<1||count>900)throw Error('Invalid absolute render interval');
fs.mkdirSync(out,{recursive:true});
// Story code must build with EXACT dependencies already in the Docker image.
const bundler='/opt/cinematic/node_modules/.bin/esbuild';
if(!fs.existsSync(bundler))throw Error('Prebuilt EXACT esbuild missing: STOP; do not npm install or swap tools');
const src=path.resolve(project,source);
if(!src.startsWith(project+path.sep)||!fs.existsSync(src))throw Error('Missing story-authored main.js; no generic flat substitute');
// Build a DERIVATIVE entry beside the story source. This does not edit the
// authoritative native 2D Hunyuan source and imports Mediabunny ONCE.
const sceneCode=fs.readFileSync(src,'utf8');
const entry=path.join(project,'.v3_merged_story_entry.js');
const v3SharedImport="import {Output as __v3Output, Mp4OutputFormat as __v3Mp4, BufferTarget as __v3Buffer, CanvasSource as __v3Canvas, Quality as __v3Quality} from 'mediabunny';\\n";
const exportApi="\\nwindow.__hunyuanV3Mediabunny={Output:__v3Output,Mp4OutputFormat:__v3Mp4,BufferTarget:__v3Buffer,CanvasSource:__v3Canvas,Quality:__v3Quality};\\n";
fs.writeFileSync(entry,v3SharedImport+sceneCode+exportApi);
cp.execFileSync(bundler,[entry,'--bundle','--format=esm','--outfile='+path.join(project,'app.js')],{
 env:{...process.env,NODE_PATH:'/opt/cinematic/node_modules'},stdio:'pipe'
});
const server=http.createServer((req,res)=>{
 try{
  const p=new URL(req.url,'http://127.0.0.1').pathname;
  if(p==='/favicon.ico'){res.writeHead(204);res.end();return}
  const file=path.resolve(project,'.'+decodeURIComponent(p==='/'?'/index.html':p));
  if(!file.startsWith(project+path.sep))throw Error('Outside project');
  const data=fs.readFileSync(file);
  res.writeHead(200,{'content-type':fmt[path.extname(file)]||'application/octet-stream'});res.end(data);
 }catch(e){res.writeHead(404);res.end('Not Found');}
});
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,channel:'chromium',args:['--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
 const page=await browser.newPage({viewport:{width:1920,height:1080},acceptDownloads:true});
 let fatal=[];page.on('pageerror',e=>fatal.push(e.message));page.on('console',m=>{if(m.type()==='error')fatal.push(m.text())});
 try{
  await page.goto('http://127.0.0.1:'+server.address().port+'/');
  await page.waitForFunction(()=>window.ready===true && typeof window.renderFrame==='function',null,{timeout:90000});
  const exportJs='/opt/cinematic/engine/scripts/temporal_export.bundle.js';
  if(!fs.existsSync(exportJs))throw Error('Missing prebuilt mandated Mediabunny exporter');
  await page.addScriptTag({path:exportJs,type:'module'});
  await page.waitForFunction(()=>typeof window.HunyuanV3Export==='function',null,{timeout:30000});
  const snapshots=[],ts=[start/30,(start+Math.floor(count*.50))/30,(start+count-1)/30];
  for(const t of ts){
   const state=await page.evaluate(t=>window.renderFrame(t),t);
   const img=await page.locator('#stage').screenshot();
   snapshots.push(img);
   fs.writeFileSync(path.join(out,'sample_'+t.toFixed(3).replace('.','_')+'.png'),img);
  }
  if(snapshots[0].equals(snapshots[1])&&snapshots[1].equals(snapshots[2]))
    throw Error('VISUAL QA FAIL: render is frozen for this shard; do not deliver static slideshow');
  // Confirm time-sampled output is deterministic after nonadjacent frame render.
  await page.evaluate(t=>window.renderFrame(t),ts[0]);
  const before=await page.locator('#stage').screenshot();
  await page.evaluate(t=>window.renderFrame(t),ts[2]);
  await page.evaluate(t=>window.renderFrame(t),ts[0]);
  const after=await page.locator('#stage').screenshot();
  if(!before.equals(after))throw Error('Camera/GSAP frame nondeterministic across seek');
  const pending=page.waitForEvent('download',{timeout:900000});
  const result=await page.evaluate(({start_frame,frame_count})=>window.HunyuanV3Export({start_frame,frame_count,fps:30}),{start_frame:start,frame_count:count});
  const download=await pending,mp4=path.join(out,'part_'+start+'_'+count+'.mp4');
  await download.saveAs(mp4);
  assert.equal(result.frame_count,count);
  if(fs.statSync(mp4).size<100000)throw Error('Empty H264 shard');
  const p=cp.execFileSync('ffprobe',['-v','error','-show_entries','stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames:format=duration','-of','json',mp4],{encoding:'utf8'});
  const q=JSON.parse(p),v=q.streams.find(s=>s.codec_type==='video');
  if(!v||v.codec_name!=='h264'||v.width!==1920||v.height!==1080||v.r_frame_rate!=='30/1'||Number(v.nb_frames)!==count)throw Error('Invalid H264 shard metadata');
  if(Math.abs(Number(q.format.duration)-count/30)>.1)throw Error('Shard duration mismatch');
  if(fatal.length)throw Error('Chromium rendering errors: '+fatal.join(';'));
  const audit={pass:true,start_frame:start,frame_count:count,first_pts:0,seconds:count/30,sha256:sha(mp4),bytes:fs.statSync(mp4).size,deterministic:true,visible_frame_change:true,format:'1920x1080 H264 30fps',all_required_tools:true,paid_generation_calls:0};
  fs.writeFileSync(path.join(out,'shard_qc.json'),JSON.stringify(audit,null,2));
  console.log('PASS',JSON.stringify(audit));
 }finally{await page.close();await browser.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error('HUNYUAN_V3_SHARD_FAILED',e.stack);process.exitCode=1;});
