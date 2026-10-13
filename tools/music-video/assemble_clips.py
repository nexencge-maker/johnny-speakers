#!/usr/bin/env python3
"""Cut AI-generated clips onto the Fifty Million beat grid.

Each slot in AI_PROMPT_KIT.md maps to a file in --clips. A clip longer than
its slot is trimmed; a shorter one is slowed down to fit. Missing slots are
filled from --fallback (the cut-out animation) at the same timestamp.
"""
import argparse, os, subprocess, tempfile, shutil

BPM, PHASE = 120.5, 0.348
BAR = 4 * 60 / BPM
# (start_bar, file) - same grid as animate.py SHOTS
SLOTS = [(0, "01_cube_wide"), (4, "02_cube_dance_cap"), (8, "03_cube_wide2"), (10, "04_cube_dance_shades"),
         (14, "05_cube_profile"), (16, "06_cube_trio"), (20, "07_cube_fireworks"), (24, "08_birds_wide"),
         (28, "09_bird_rap_cap"), (32, "10_bird_rap_profile"), (36, "11_birds_low"), (40, "12_bird_rap_shades"),
         (44, "13_bird_tight"), (48, "14_birds_wide2"), (52, "15_city_walk_profile"), (56, "16_city_walk_front"),
         (60, "17_city_walk_shades"), (64, "18_city_front2"), (68, "19_city_rain"), (72, "20_city_walk_final"),
         (76, "21_cube_trio2"), (80, "22_cube_cap"), (84, "23_cube_fireworks"), (86, "24_cube_shades"),
         (88, "25_cube_trio_final"), (92, "26_outro_birds")]
EXTS = (".mp4", ".mov", ".webm", ".mkv")


def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path]).strip())


def find(clips, name):
    for e in EXTS:
        p = os.path.join(clips, name + e)
        if os.path.exists(p):
            return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--clips", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fallback", help="video to fill missing slots from")
    ap.add_argument("--size", default="1920x1080")
    a = ap.parse_args()
    total = dur(a.audio)
    w, h = a.size.split("x")
    norm = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps=30,format=yuv420p,setsar=1"
    work = tempfile.mkdtemp(prefix="assemble_")
    parts = []
    for i, (bar, name) in enumerate(SLOTS):
        st = 0.0 if i == 0 else PHASE + bar * BAR
        en = PHASE + SLOTS[i + 1][0] * BAR if i + 1 < len(SLOTS) else total
        n = round(en * 30) - round(st * 30)
        slot = n / 30
        src = find(a.clips, name)
        out = os.path.join(work, f"{i:02d}.mp4")
        if src:
            speed = min(1.0, dur(src) / slot)  # <1 slows a short clip down
            vf = f"setpts=PTS/{speed:.5f},{norm}"
            cmd = ["-i", src]
            tag = f"{name} ({'slowed' if speed < 1 else 'trimmed'})"
        elif a.fallback:
            vf, cmd, tag = norm, ["-ss", f"{st:.3f}", "-i", a.fallback], "fallback"
        else:
            raise SystemExit(f"missing clip {name} and no --fallback")
        subprocess.run(["ffmpeg", "-v", "error", "-y", *cmd, "-an", "-vf", vf, "-frames:v", str(n),
                        "-c:v", "libx264", "-preset", "fast", "-crf", "18", out], check=True)
        parts.append(out)
        print(f"{i + 1:2d}. {st:7.2f}-{en:7.2f}s  {tag}", flush=True)
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", a.audio,
                    "-map", "0:v", "-map", "1:a", "-vf", f"fade=t=out:st={total - 3:.2f}:d=3",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-t", f"{total:.3f}", a.out], check=True)
    shutil.rmtree(work)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
