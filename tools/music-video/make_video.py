#!/usr/bin/env python3
"""Beat-synced photo music video generator (ffmpeg only, no Python deps).

Builds a music video from still photos: every cut lands on a bar line,
each shot gets its own camera move (push-in / pull-out / pan), color grade,
optional white flash and on-beat zoom pulse, then everything is graded,
titled and muxed with the song.

Usage:
  python3 tools/music-video/make_video.py \
      --audio public/media/fifty-video.mp4 \
      --images img1.png img2.png img3.png \
      --out fifty-million-music-video.mp4
"""
import argparse, json, math, os, shutil, subprocess, sys, tempfile

FPS = 30
W, H = 1920, 1080
FONT = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
FONT_LIGHT = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"

# Per-photo crop that removes letterbox bars and leaves a clean 16:9 frame
# (w:h:x:y in source pixels). None = auto center-crop to 16:9.
CROPS = [None, "1528:860:72:32", "1600:900:36:0"]

# Camera framings per photo: (zoom_start, zoom_end, (cx0, cy0), (cx1, cy1))
# Centers are normalized to the cropped photo.
FRAMINGS = [
    {  # 0: graffiti wall, daylight
        "wide":  (1.00, 1.12, (0.50, 0.45), (0.50, 0.42)),
        "face":  (1.90, 2.15, (0.45, 0.29), (0.46, 0.26)),
        "pan":   (1.45, 1.50, (0.22, 0.45), (0.58, 0.40)),
        "detail": (1.85, 1.60, (0.60, 0.58), (0.55, 0.50)),
    },
    {  # 1: profile, night bokeh
        "wide":  (1.05, 1.18, (0.50, 0.50), (0.52, 0.46)),
        "face":  (1.90, 2.15, (0.58, 0.42), (0.58, 0.40)),
        "pan":   (1.50, 1.55, (0.88, 0.45), (0.58, 0.42)),
        "detail": (2.40, 2.15, (0.44, 0.48), (0.46, 0.46)),
    },
    {  # 2: cap, direct gaze
        "wide":  (1.00, 1.12, (0.45, 0.45), (0.43, 0.42)),
        "face":  (2.15, 2.50, (0.42, 0.31), (0.42, 0.29)),
        "pan":   (1.50, 1.55, (0.12, 0.50), (0.40, 0.42)),
        "detail": (1.80, 1.65, (0.41, 0.80), (0.42, 0.66)),
    },
]

LOOKS = {
    "natural": "eq=contrast=1.06:saturation=1.12",
    "warm":    "colorbalance=rs=0.08:gs=0.02:bs=-0.08,eq=contrast=1.08:saturation=1.22",
    "mono":    "hue=s=0,eq=contrast=1.25:brightness=-0.02",
    "neon":    "colorbalance=rs=0.05:bs=0.12:rh=0.06,eq=contrast=1.12:saturation=1.45",
    "glitch":  "eq=contrast=1.15:saturation=1.35,rgbashift=rh=-12:bh=12:gv=4",
}


def build_shots(bar, phase, total):
    """Return list of shots: dict(start, end, img, framing, look, flash, pulse)."""
    def at(b):
        return min(total, phase + b * bar)

    shots = []
    def add(b0, b1, img, fr, look="natural", flash=False, pulse=False):
        shots.append(dict(start=at(b0), end=at(b1), img=img, framing=fr,
                          look=look, flash=flash, pulse=pulse))

    # Intro (quiet build): one slow push on the cap photo, title over it.
    shots.append(dict(start=0.0, end=at(4), img=2, framing="wide",
                      look="warm", flash=False, pulse=False))

    cycle = [(0, "wide"), (2, "face"), (1, "wide"), (0, "face"),
             (2, "pan"), (1, "face"), (0, "pan"), (2, "detail"),
             (1, "pan"), (0, "detail"), (2, "wide"), (1, "detail")]
    looks = ["natural", "warm", "neon", "natural", "warm", "neon"]
    ci = [0]
    def nxt():
        img, fr = cycle[ci[0] % len(cycle)]
        ci[0] += 1
        return img, fr

    def run(b0, b1, step, look=None, flash_first=False, pulse=True, glitch_every=0):
        b, k = b0, 0
        while b < b1 - 1e-6:
            img, fr = nxt()
            lk = look or looks[k % len(looks)]
            if glitch_every and k % glitch_every == glitch_every - 1:
                lk = "glitch"
            add(b, min(b1, b + step), img, fr, lk,
                flash=(flash_first and k == 0) or step <= 1, pulse=pulse)
            b += step; k += 1

    run(4, 20, 2, flash_first=True)                  # drop: 2-bar cuts
    run(20, 24, 1, glitch_every=2)                   # turnaround: 1-bar cuts
    run(24, 40, 4, flash_first=True)                 # breathing: 4-bar shots
    run(40, 48, 2)
    run(48, 52, 0.5, glitch_every=3)                 # rapid half-bar burst
    run(52, 68, 2, flash_first=True)
    add(68, 72, 1, "detail", "mono", flash=True, pulse=False)  # breakdown
    run(72, 80, 2, flash_first=True)
    run(80, 88, 1, glitch_every=4)
    run(88, 92, 0.5, glitch_every=2)
    add(92, 98, 1, "face", "warm", flash=True, pulse=False)    # outro
    shots.append(dict(start=at(98), end=total, img=0, framing="wide",
                      look="warm", flash=False, pulse=False))
    # Last shot pulls out instead of pushing in.
    shots[-1]["reverse"] = True
    return [s for s in shots if s["end"] - s["start"] > 0.05]


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr[-3000:])
        raise SystemExit(f"ffmpeg failed: {' '.join(cmd[:6])}...")


def prep_images(images, work):
    out = []
    for i, src in enumerate(images):
        crop = CROPS[i] if i < len(CROPS) else None
        if crop:
            vf = f"crop={crop}"
        else:
            vf = "crop='min(iw,ih*16/9)':'min(ih,iw*9/16)'"
        dst = os.path.join(work, f"src{i}.png")
        run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf",
             f"{vf},scale=3840:2160:flags=lanczos,setsar=1", dst])
        out.append(dst)
    return out


def render_shot(i, s, src, beat, phase, work):
    n_frames = round(s["end"] * FPS) - round(s["start"] * FPS)
    dur = n_frames / FPS
    z0, z1, c0, c1 = FRAMINGS[s["img"]][s["framing"]]
    if s.get("reverse"):
        z0, z1 = max(z0, z1) + 0.35, min(z0, z1)
        c0, c1 = c1, c0
    # smoothstep easing over the shot
    p = f"(min(t/{dur:.4f},1))"
    e = f"({p}*{p}*(3-2*{p}))"
    z = f"({z0}+({z1}-{z0})*{e})"
    if s["pulse"]:
        g = f"(t+{s['start']:.4f}-{phase:.4f})"
        z = f"({z}*(1+0.035*exp(-9*mod({g}+{beat*4:.4f},{beat:.4f}))))"
    cx = f"({c0[0]}+({c1[0]}-{c0[0]})*{e})"
    cy = f"({c0[1]}+({c1[1]}-{c0[1]})*{e})"
    vf = [
        f"scale=w='2*trunc({W}*{z}/2)':h='2*trunc({H}*{z}/2)':eval=frame:flags=bicubic",
        f"crop={W}:{H}:x='clip({cx}*iw-{W}/2,0,iw-{W})':y='clip({cy}*ih-{H}/2,0,ih-{H})'",
        LOOKS[s["look"]],
    ]
    if s["flash"]:
        vf.append("fade=t=in:st=0:d=0.18:color=white")
    if i == 0:
        vf.append(f"fade=t=in:st=0:d=2.5")
    vf.append("format=yuv420p")
    dst = os.path.join(work, f"shot{i:03d}.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS),
         "-i", src, "-vf", ",".join(vf), "-frames:v", str(n_frames),
         "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "14",
         dst])
    return dst


def esc(t):
    return t.replace(":", r"\:").replace("'", r"\'")


def text(t, size, y, st, en, font=FONT, spacing=0):
    a = (f"if(lt(t,{st}),0,if(lt(t,{st}+0.8),(t-{st})/0.8,"
         f"if(lt(t,{en}-0.8),1,if(lt(t,{en}),({en}-t)/0.8,0))))")
    return (f"drawtext=fontfile={font}:text='{esc(t)}':fontsize={size}:"
            f"fontcolor=white:alpha='{a}':x=(w-text_w)/2:y={y}:"
            f"shadowcolor=black@0.6:shadowx=3:shadowy=3"
            + (f":line_spacing={spacing}" if spacing else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--images", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bpm", type=float, default=120.5)
    ap.add_argument("--phase", type=float, default=0.348, help="first downbeat, seconds")
    ap.add_argument("--title", default="FIFTY MILLION")
    ap.add_argument("--artist", default="JDP / JOHN DA POET")
    ap.add_argument("--web-out", help="also write a 1280x720 web-sized copy here")
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()

    total = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", a.audio]).strip())
    beat = 60 / a.bpm
    shots = build_shots(beat * 4, a.phase, total)
    work = tempfile.mkdtemp(prefix="mv_")
    print(f"{len(shots)} shots over {total:.1f}s, work dir {work}")
    srcs = prep_images(a.images, work)

    files = []
    for i, s in enumerate(shots):
        files.append(render_shot(i, s, srcs[s["img"] % len(srcs)], beat, a.phase, work))
        print(f"  shot {i+1}/{len(shots)} {s['start']:6.2f}-{s['end']:6.2f}s "
              f"img{s['img']} {s['framing']:6s} {s['look']}", flush=True)
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in files)

    end_st = total - 16
    post = ",".join([
        "vignette=angle=PI/4.5",
        "noise=alls=5:allf=t",
        text(a.title, 132, "h*0.40", 1.2, a.phase + 4 * beat * 4 - 0.3),
        text(a.artist, 46, "h*0.40+165", 1.8, a.phase + 4 * beat * 4 - 0.3, FONT_LIGHT),
        text(a.artist, 64, "h*0.44", end_st, total - 1.5),
        text(a.title, 40, "h*0.44+90", end_st + 0.6, total - 1.5, FONT_LIGHT),
        f"fade=t=out:st={total-3.5:.3f}:d=3.5",
        "format=yuv420p",
    ])
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-i", a.audio, "-map", "0:v", "-map", "1:a", "-vf", post,
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
         "-t", f"{total:.3f}", a.out])
    print("wrote", a.out)
    if a.web_out:
        run(["ffmpeg", "-v", "error", "-y", "-i", a.out, "-vf", "scale=1280:720:flags=lanczos",
             "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-c:a", "aac", "-b:a", "128k",
             "-movflags", "+faststart", a.web_out])
        print("wrote", a.web_out)
    if not a.keep:
        shutil.rmtree(work)


if __name__ == "__main__":
    main()
