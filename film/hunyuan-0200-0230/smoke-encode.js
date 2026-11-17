import { Output, Mp4OutputFormat, BufferTarget, CanvasSource, Quality } from 'mediabunny';
export async function quickSmoke(){
 const c=document.getElementById('stage');
 if(!window.__HUNYUAN_READY)throw Error('Original rig and illustrated planes not initialized');
 const probe={phase:'start',dimensions:[c.width,c.height],frameCount:0};
 const target=new BufferTarget();
 const output=new Output({format:new Mp4OutputFormat(),target});
 const source=new CanvasSource(c,{codec:'avc',bitrate:6500000});
 output.addVideoTrack(source,{frameRate:30});
 console.log('[SMOKE] Mediabunny configured');
 const timeout=(p,phase,ms=35000)=>Promise.race([p,new Promise((_,reject)=>setTimeout(()=>reject(Error(phase+' timed out after '+ms+' ms')),ms))]);
 await timeout(output.start(),'output.start');
 console.log('[SMOKE] Output started');
 for(let i=0;i<2;i++){
  await timeout(window.renderAt(i/30),'nativeRigAndThree.jsFrame');
  console.log('[SMOKE] rendered '+i);
  await timeout(source.add(i/30,1/30,{keyFrame:i===0}),'mediabunnyCanvasSource.add frame '+i);
  console.log('[SMOKE] AVC encoded '+i);
  probe.frameCount++;
 }
 await timeout(output.finalize(),'mp4.finalize');
 probe.bytes=target.buffer?.byteLength||0;
 if(probe.bytes<1000)throw Error('Mediabunny produced fewer than 1000 bytes');
 return probe;
}
