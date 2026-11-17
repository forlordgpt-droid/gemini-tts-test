#!/usr/bin/env python3
"""Combine ONLY the two user-authorized KIE WAVs, preserving every voiced sample.

Uses Python standard library, and the project's required FFmpeg later muxes audio.
Do not substitute voice model, speed speech, remove voiced words or retry paid tasks.
"""
from array import array
from pathlib import Path
import wave, json, sys

ROOT = Path(__file__).resolve().parent
SR = 24000
TARGET = 30 * SR
MIN_GAP = int(.17 * SR)
THRESHOLD = 200
WINDOW = 480  # 20 ms

def open_pcm(path):
    with wave.open(str(path),'rb') as w:
        if (w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getcomptype()) != (SR,1,2,'NONE'):
            raise RuntimeError('Exact KIE output must be uncompressed 24000 Hz mono PCM16: '+str(path))
        a=array('h');a.frombytes(w.readframes(w.getnframes()))
    if sys.byteorder!='little':a.byteswap()
    if len(a)<SR*4:raise RuntimeError('Narration suspiciously short '+str(path))
    return a

def trim_only_long_silences(a, max_silence_ms=160):
    """Low-energy windows shorter than 160ms are untouched; never discard speech windows."""
    envelope=[]
    for i in range(0,len(a),WINDOW):
        z=a[i:i+WINDOW]
        envelope.append(sum(abs(x) for x in z)/max(1,len(z)))
    keep=[True]*len(envelope)
    cursor=0;deleted=0;limit=max_silence_ms//20
    while cursor<len(envelope):
        if envelope[cursor]>THRESHOLD:
            cursor+=1;continue
        end=cursor+1
        while end<len(envelope) and envelope[end]<=THRESHOLD:end+=1
        length=end-cursor
        if length>limit+4:
            left=2;right=2
            # Keep 40ms of guard at the leading and trailing edge, plus up to 160ms silence.
            allowance=max(limit,length//20)
            start=cursor+left+allowance
            stop=end-right
            for j in range(start,stop):keep[j]=False;deleted+=1
        cursor=end
    result=array('h')
    for i,k in enumerate(keep):
        if k:result.extend(a[i*WINDOW:(i+1)*WINDOW])
    return result,deleted*WINDOW/SR

parts=[];provenance=[]
for i in (0,1):
    p=ROOT/'audio'/('segment_'+str(i)+'.wav')
    if not p.exists():raise RuntimeError('Missing approved KIE narration '+str(p))
    raw=open_pcm(p)
    cleaned,deleted=trim_only_long_silences(raw)
    parts.append(cleaned)
    provenance.append({'segment':i,'original_s':round(len(raw)/SR,3),
      'silence_removed_s':round(deleted,3),'preserved_s':round(len(cleaned)/SR,3)})

total=sum(len(x) for x in parts)+MIN_GAP
if total>TARGET-int(.18*SR):
    raise RuntimeError('Narration is too long to fit 02:00–02:30 without clipping/speedup. HARD STOP. '+str(provenance))
master=array('h')
for i,p in enumerate(parts):
    if i:master.extend([0]*MIN_GAP)
    master.extend(p)
spoken_end=len(master)/SR
master.extend([0]*(TARGET-len(master)))
if len(master)!=TARGET:raise RuntimeError('Expected exactly 30 seconds PCM')
out=ROOT/'audio'/'narration_30s.wav'
with wave.open(str(out),'wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR)
    if sys.byteorder!='little':master.byteswap()
    w.writeframes(master.tobytes())
q={'source':'KIE.ai google/gemini-3-8-flash-lite-tts; Fola','approved_outputs':2,
 'actual_generated_outputs':2,'master_duration_seconds':30,'spoken_end_seconds':spoken_end,
 'segments':provenance,'voice_samples_preserved':True,'voice_time_stretching':False,
 'note':'Low-energy long pauses reduced; waveform otherwise preserved. Manual listening required.'}
(ROOT/'audio'/'AUDIO_QC.json').write_text(json.dumps(q,indent=2))
print(json.dumps(q,indent=2))
