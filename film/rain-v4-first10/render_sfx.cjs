#!/usr/bin/env node
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),cp=require('node:child_process');
const {chromium}=require('playwright');
const project=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
if(!fs.existsSync(path.join(project,'main.js')))throw Error('Missing authored scene');
const entry=path.join(project,'.sfx_entry.js');fs.copyFileSync(path.join(project,'main.js'),entry);
cp.execFileSync('/opt/cinematic/node_modules/.bin/esbuild',[entry,'--bundle','--format=esm','--outfile='+path.join(project,'app.js')],{env:{...process.env,NODE_PATH:'/opt/cinematic/node_modules'},stdio:'inherit'});
const fmt={'.html':'text/html','.js':'text/javascript','.webp':'image/webp'};
const server=http.createServer((req,res)=>{const q=new URL(req.url,'http://127.0.0.1').pathname;
 const f=path.resolve(project,'.'+(q==='/'?'/index.html':q));if(!f.startsWith(project+'/')){res.writeHead(403);return res.end();}
 try{res.writeHead(200,{'content-type':fmt[path.extname(f)]||'application/octet-stream'});res.end(fs.readFileSync(f));}
 catch(e){res.writeHead(404);res.end();}});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,channel:'chromium',args:['--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
 try{const page=await browser.newPage({viewport:{width:1920,height:1080}});
  await page.goto('http://127.0.0.1:'+server.address().port+'/');
  await page.waitForFunction(()=>window.ready===true&&typeof window.exportRainSfx==='function',null,{timeout:90000});
  const b64=await page.evaluate(()=>window.exportRainSfx());const data=Buffer.from(b64,'base64');
  if(data.byteLength<400000)throw Error('OfflineAudioContext returned no WAV');
  fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,data);console.log('WAV_EXPORTED',data.byteLength);await page.close();
 }finally{await browser.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
