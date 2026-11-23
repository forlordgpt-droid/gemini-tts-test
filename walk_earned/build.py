#!/usr/bin/env python3
"""Build The Walk He Earned from existing GROK LOWER clips; no generation or spending."""
from __future__ import annotations
import json, math, os, subprocess, sys, wave
from pathlib import Path

ROOT = Path("walk_earned")
ASSETS = ROOT / "assets"
FINAL = ROOT / "final"
TEMP = ROOT / "tmp"
FINAL.mkdir(parents=True, exist_ok=True)
TEMP.mkdir(parents=True, exist_ok=True)
WIDTH, HEIGHT, FPS, LENGTH = 480, 854, 24, 45.0

def run(*args):
    cmd = list(map(str, args))
    print("RUN:", " ".join(cmd[:14]), "...", flush=True)
    subprocess.run(cmd, check=True)

def probe(path):
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,width,height,sample_rate,channels",
        "-of", "json", str(path)
    ], text=True)
    return json.loads(raw)

def normalize(name, src):
    dest = TEMP / (name + "_norm.mp4")
    vfx = (
        "scale=480:854:force_original_aspect_ratio=increase,"
        "crop=480:854,setsar=1,fps=24,"
        "trim=duration=15,setpts=PTS-STARTPTS,"
        "tpad=stop_mode=clone:stop_duration=2,format=yuv420p"
    )
    afx = "apad=pad_dur=3,atrim=duration=15,asetpts=PTS-STARTPTS,aresample=48000"
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src,
        "-vf", vfx, "-af", afx, "-t", "15",
        "-r", "24", "-ar", "48000", "-ac", "2",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart", dest)
    return dest

def score_to_wav(path):
    """Original low-volume warm chord/piano motif. No copyrighted melody."""
    sr, duration = 24000, 45
    chords = [
        (220.00, 261.63, 329.63), (174.61, 220.00, 261.63),
        (196.00, 246.94, 293.66), (164.81, 196.00, 261.63),
        (220.00, 261.63, 329.63), (174.61, 220.00, 261.63),
        (196.00, 246.94, 293.66), (261.63, 329.63, 392.00),
    ]
    import array
    data = array.array("h")
    for i in range(sr * duration):
        t = i / sr
        if t < 8.5:
            data.append(0)
            continue
        tt = t - 8.5
        chord = chords[int(tt // 4.8) % len(chords)]
        local = tt % 4.8
        swell = min(1.0, tt / 5.0) * min(1.0, max(0.0, 45.0 - t) / 1.8)
        crescendo = 0.50 + 0.50 * min(1, tt / 27.0)
        # Slow synth-pad + small decaying pianolike upper partial.
        warm = sum(math.sin(2 * math.pi * f * t + 0.2 * j) for j, f in enumerate(chord)) / 3.0
        pluck = math.exp(-local * 1.25) * math.sin(2 * math.pi * (chord[2] * 2) * local)
        sample = (warm * 0.020 + pluck * 0.007) * swell * crescendo
        data.append(int(max(-1.0, min(1.0, sample)) * 32767))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(data.tobytes())

def ass_stamp(t):
    cs = round(t * 100)
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, c = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"

CAPTIONS = [
 (0.15, 1.53, "I'M HER FATHER."),
 (1.54, 3.29, "I'LL WALK HER."),
 (6.42, 8.23, "Dad, I'm waiting"),
 (8.24, 10.14, "for you."),
 (15.22, 17.43, "At my first school dance,"),
 (17.43, 20.38, "you waited forty minutes"),
 (20.38, 22.43, "because I was scared."),
 (24.05, 26.98, "\"We go when you're ready.\""),
 (26.98, 29.45, "I need that dad today."),
 (30.18, 33.08, "Ready, sweetheart?"),
 (33.49, 35.95, "Now I am."),
]

def make_subtitles():
    ass = FINAL / "The_Walk_He_Earned_45s.ass"
    header = """[Script Info]
Title: The Walk He Earned – screen captions
ScriptType: v4.00+
PlayResX: 480
PlayResY: 854
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,DejaVu Sans,28,&H00FFFFFF,&H0000E5FF,&HCE0B0C0E,&H40000000,-1,0,0,0,100,100,0,0,1,3,1,2,26,26,190,1
Style: Hit,DejaVu Sans,29,&H0000D5FF,&H0000D5FF,&HCE0B0C0E,&H50000000,-1,0,0,0,100,100,0,0,1,3,1,2,26,26,190,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    hit_indices = {0, 2, 7, 8, 10}
    for j, (start, end, phrase) in enumerate(CAPTIONS):
        style = "Hit" if j in hit_indices else "Main"
        phrase = phrase.replace("\\", "\\\\").replace("{", "").replace("}", "")
        lines.append(f"Dialogue: 0,{ass_stamp(start)},{ass_stamp(end)},{style},,0,0,0,,{{\\fad(80,110)}}{phrase}\n")
    ass.write_text("".join(lines), encoding="utf-8")
    srt = FINAL / "The_Walk_He_Earned_45s.srt"
    def stamp(t):
        total = round(t * 1000)
        h, r = divmod(total, 3600000); m, r = divmod(r, 60000); s, ms = divmod(r, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    srt.write_text("".join(
        f"{i+1}\n{stamp(a)} --> {stamp(b)}\n{tx}\n\n"
        for i, (a,b,tx) in enumerate(CAPTIONS)
    ), encoding="utf-8")
    return ass, srt

def main():
    scene_files = [ASSETS / "video" / f"{name}.mp4" for name in ["A_SCENE", "B_SCENE", "C_SCENE"]]
    for p in scene_files:
        if not p.is_file() or p.stat().st_size < 10000:
            raise RuntimeError("Missing or empty original video: " + p.name)
    originals = {p.stem: probe(p) for p in scene_files}
    norm = [normalize(chr(ord("A")+j), p) for j,p in enumerate(scene_files)]
    concat_file = TEMP / "files.txt"
    concat_file.write_text("".join(f"file '{p.resolve()}'\n" for p in norm))
    merged = TEMP / "merged.mp4"
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat",
        "-safe", "0", "-i", concat_file, "-c", "copy", "-t", "45", merged)
    music = TEMP / "original_score.wav"
    score_to_wav(music)
    clean = FINAL / "The_Walk_He_Earned_45s_Clean_480p.mp4"
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", merged, "-i", music,
        "-filter_complex",
        "[0:a]volume=1.08[a];[1:a]volume=0.75,aresample=48000[m];"
        "[a][m]amix=inputs=2:duration=first:dropout_transition=2,"
        "alimiter=limit=0.96[out]",
        "-map", "0:v:0", "-map", "[out]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
        "-ar", "48000", "-ac", "2", "-t", "45",
        "-movflags", "+faststart", clean)
    ass, srt = make_subtitles()
    final = FINAL / "The_Walk_He_Earned_45s_480p_9x16.mp4"
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", clean,
        "-vf", "ass=" + str(ass) + ":fontsdir=/usr/share/fonts/truetype/dejavu",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-c:a", "copy", "-t", "45",
        "-movflags", "+faststart", final)
    cover = FINAL / "The_Walk_He_Earned_Cover.jpg"
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", "0.8", "-i", final, "-vframes", "1",
        "-vf",
        "scale=540:960,"
        "drawbox=x=0:y=0:w=iw:h=140:color=black@0.50:t=fill,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        "text='WHO WILL WALK HER?':fontcolor=white:fontsize=28:"
        "x=(w-text_w)/2:y=67",
        "-q:v", "3", cover)
    facts = {
        "title": "The Walk He Earned",
        "model_for_all_video": "grok-lower",
        "generation_resolution": "480p",
        "duration_target_seconds": LENGTH,
        "source_video_uuids": [
            "63243f1e-e759-11f1-b045-de2ad4e2690c",
            "bcc96d1e-e759-11f1-9bd0-0a31a5bde6b4",
            "d25d2fb2-e759-11f1-80f6-0e5c9cffef7c",
        ],
        "image_uuid": "01e44eec-e759-11f1-bc71-e6662a69bd87",
        "snapgen_credits_spent": 55,
        "source_probes": originals,
        "clean_probe": probe(clean),
        "captioned_probe": probe(final),
        "notes": "AI-generated fictional wedding microdrama; three existing 15s clips assembled and locally finished; no additional paid generations.",
    }
    duration = float(facts["captioned_probe"]["format"]["duration"])
    video_stream = next(s for s in facts["captioned_probe"]["streams"] if s["codec_type"]=="video")
    audio_ok = any(s["codec_type"]=="audio" for s in facts["captioned_probe"]["streams"])
    if not (44.75 <= duration <= 45.2 and video_stream["width"] == WIDTH and video_stream["height"] == HEIGHT and audio_ok):
        raise RuntimeError("Final export QA failed")
    report = FINAL / "The_Walk_He_Earned_QA.json"
    report.write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
    print("SUCCESS", json.dumps({"file":str(final),"seconds":duration, "width": WIDTH,"height": HEIGHT,"bytes":final.stat().st_size}))
if __name__ == "__main__":
    main()
