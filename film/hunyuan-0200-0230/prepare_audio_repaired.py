#!/usr/bin/env python3
"""30s master from TWO ALREADY-APPROVED KIE Fola WAVs.
No new generation, speed changes, voiced-word truncation or tool swap:
only delete measured 20ms low-amplitude silence windows. Reproducible.
"""
from array import array
from pathlib import Path
import sys, json, wave
ROOT=Path(__file__).resolve().parent
AUD=ROOT/'audio'
SR=24000
WINDOW=480
THRESHOLD=150
GAP_SAMPLES=round(.18*SR)
MAX=30*SR

def read(path):
    with wave.open(str(path),'rb') as w:
        settings=(w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getcomptype())
        if settings != (SR,1,2,'NONE'):
            raise RuntimeError('Unexpected KIE audio settings '+str(settings))
        pcm=array('h');pcm.frombytes(w.readframes(w.getnframes()))
        if sys.byteorder!='little':pcm.byteswap()
    if len(pcm)<SR*10:raise RuntimeError('Unexpectedly short KIE clip '+str(path))
    return pcm

def trim_gaps(pcm, maximum_internal_gap_ms, external_ms=40):
    levels=[]
    for i in range(0,len(pcm),WINDOW):
        a=pcm[i:min(len(pcm),i+WINDOW)]
        levels.append(sum(abs(v) for v in a)/max(1,len(a)))
    keep=[True]*len(levels)
    i=0;gaps=[]
    while i<len(levels):
        if levels[i]>=THRESHOLD:i+=1;continue
        j=i
        while j<len(levels) and levels[j]<THRESHOLD:j+=1
        n=j-i;edge=(i==0 or j==len(levels))
        retain=min(n,max(1,round((external_ms if edge else maximum_internal_gap_ms)/20)))
        remove=n-retain
        if remove>0:
            left=(retain+1)//2
            for k in range(i+left,i+left+remove):keep[k]=False
            gaps.append({'start_s':round(i*.02,3),'duration_s':round(n*.02,3),
                         'removed_s':round(remove*.02,3),'edge':edge})
        i=j
    out=array('h')
    for idx,yes in enumerate(keep):
        if yes:out.extend(pcm[idx*WINDOW:min(len(pcm),(idx+1)*WINDOW)])
    return out,gaps

source=[read(AUD/f'segment_{i}.wav') for i in (0,1)]
for gap_ms in [180,160,140,120,100,80]:
    results=[trim_gaps(pcm,gap_ms) for pcm in source]
    total=sum(len(a) for a,g in results)+GAP_SAMPLES
    if total<=MAX-SR*.1:break
else:raise RuntimeError('Measured silence insufficient: refusing to cut speech')
master=array('h');entries=[]
for i,(pcm,gaps) in enumerate(results):
    if i:master.extend([0]*GAP_SAMPLES)
    start=len(master)/SR;master.extend(pcm)
    entries.append({'segment':i,
       'kie_task_id':['73a3af873fb9eeb935d7335e6bb5a1ad','be36a266dd54291568fc8717ee66ff73'][i],
       'original_seconds':round(len(source[i])/SR,3),
       'preserved_seconds':round(len(pcm)/SR,3),
       'start_seconds':round(start,3),'end_seconds':round(len(master)/SR,3),
       'silent_gaps_modified':gaps})
speech_end=len(master)/SR
if len(master)>MAX:raise RuntimeError('Audio over 30 seconds, cannot truncate voice')
master.extend([0]*(MAX-len(master)))
with wave.open(str(AUD/'narration_30s.wav'),'wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR)
    if sys.byteorder!='little':master.byteswap()
    w.writeframes(master.tobytes())
meta={'model':'google/gemini-3-8-flash-lite-tts','provider':'KIE.ai','voice':'Fola',
      'new_generation_requests':0,'duration_seconds':30,
      'spoken_audio_ends_at_seconds':round(speech_end,3),
      'sample_rate':SR,'original_total_seconds':sum(len(x) for x in source)/SR,
      'between_clips_silence_seconds':GAP_SAMPLES/SR,
      'silence_threshold_pcm16_mean_abs':THRESHOLD,
      'max_retained_internal_silence_ms':gap_ms,
      'removed_only_low_amplitude_silent_20ms_windows':True,
      'time_stretching':False,'voice_trimmed':False,'segments':entries}
(AUD/'AUDIO_QC.json').write_text(json.dumps(meta,indent=2))
print(json.dumps({'duration_seconds':30,'spoken_end_s':round(speech_end,3),
    'max_retained_gap_ms':gap_ms,'task_ids':[x['kie_task_id'] for x in entries],
    'parts':[{'part':x['segment'],'start':x['start_seconds'],
              'end':x['end_seconds'],
              'removed_low_level_s':round(sum(g['removed_s'] for g in x['silent_gaps_modified']),3)}
             for x in entries]},indent=2))
