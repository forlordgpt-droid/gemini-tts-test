// V3 shared WebCodecs + Mediabunny video exporter. NO NEW PAID CALLS.
// Fixes the previous frozen-second-half bug by deliberately separating:
// (1) ABSOLUTE narrative time for GSAP sampling, from
// (2) LOCAL 0-based segment timestamps for WebCodecs MP4 frames.
// The scene's esbuild bundle imports the SINGLE original pinned Mediabunny instance.
// Shared exporter uses that SAME instance, never bundles a second copy.
const mb=window.__hunyuanV3Mediabunny;
if(!mb||!['Output','Mp4OutputFormat','BufferTarget','CanvasSource','Quality'].every(k=>typeof mb[k]==='function'))throw Error('Hunyuan V3 single-instance Mediabunny API not injected: STOP; no substitution');
const {Output,Mp4OutputFormat,BufferTarget,CanvasSource,Quality}=mb;
window.HunyuanV3Export=async ({start_frame,frame_count,fps=30,quality_bitrate=8500000})=>{
 const stage=document.getElementById('stage');
 if(!(stage instanceof HTMLCanvasElement)||stage.width!==1920||stage.height!==1080)
   throw Error('RENDER BLOCKED: real 1920x1080 Hunyuan cinematic canvas required');
 if(typeof window.renderFrame!=='function')throw Error('RENDER BLOCKED: no original-compatible deterministic renderFrame(t) authored for this story');
 if(!Number.isInteger(start_frame)||start_frame<0||!Number.isInteger(frame_count)||frame_count<1||frame_count>900)
   throw Error('RENDER BLOCKED: invalid frame window; max 30 seconds per shard');
 if(fps!==30)throw Error('RENDER BLOCKED: 30 fps user-required quality');
 const src=new CanvasSource(stage,{codec:'avc',quality:new Quality({bitrate:quality_bitrate})});
 const output=new Output({format:new Mp4OutputFormat(),target:new BufferTarget()});
 output.addVideoTrack(src,{frameRate:fps});
 await output.start();
 for(let f=0;f<frame_count;f++){
   const absolute=(start_frame+f)/fps;  // GSAP/Three.js always sample ABSOLUTE story time.
   await window.renderFrame(absolute);
   await src.add(f/fps,1/fps);           // WebCodecs PTS must be LOCAL, 0-based for EACH shard.
 }
 await output.finalize();
 const b=output.target.buffer;
 if(!b||b.byteLength<75000)throw Error('RENDER BLOCKED: WebCodecs H264 shard empty or malformed');
 const link=document.createElement('a');
 link.href=URL.createObjectURL(new Blob([b],{type:'video/mp4'}));
 link.download='hunyuan_v3_'+start_frame+'_'+frame_count+'.mp4';
 document.body.appendChild(link);link.click();link.remove();
 return {start_frame,frame_count,first_pts:0,last_pts:(frame_count-1)/fps,bytes:b.byteLength,codec:'avc',fps};
};
