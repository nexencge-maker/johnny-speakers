#!/usr/bin/env python3
"""Animated cut-out music video: glass-cube party on the water, giant birds
over the ocean, and a rapping walk through the city.

The character comes from background-removed cut-outs of the photos
(see cutout.py). Everything else is drawn in code. Motion is driven by the
song: bounces land on the beat and lights, rings and confetti follow the
loudness.

Needs: numpy, Pillow, ffmpeg.
  python3 tools/music-video/animate.py --audio public/media/fifty-video.mp4 \
      --out fifty-million-animated.mp4
"""
import argparse, math, os, subprocess, sys
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1280, 720, 30
HERE = os.path.dirname(os.path.abspath(__file__))
CUTS = [os.path.join(HERE, "cutouts", f) for f in
        ("01-graffiti.png", "02-night-profile.png", "03-night-cap.png")]
# Mouth position (fraction of cut-out w/h) and which way each face looks.
MOUTH = [(0.36, 0.33, -1), (0.79, 0.51, 1), (0.75, 0.375, 1)]
FONT_B = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
FONT_R = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
FONT_SYM = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BPM, PHASE = 120.5, 0.348
BEAT = 60 / BPM
BAR = 4 * BEAT

# (start_bar, scene, params). Each shot runs to the next one's start.
SHOTS = [
    (-1, "cube_wide", dict(zoom=(0.35, 0.8), intro=True)),
    (4, "cube_in", dict(chars=[2])),
    (8, "cube_wide", dict(zoom=(0.8, 1.0))),
    (10, "cube_in", dict(chars=[0])),
    (14, "cube_in", dict(chars=[1])),
    (16, "cube_in", dict(chars=[0, 2, 1])),
    (20, "cube_wide", dict(zoom=(1.0, 1.25), drift=True)),
    (24, "birds_wide", dict()),
    (28, "bird_close", dict(char=2)),
    (32, "bird_close", dict(char=1)),
    (36, "birds_wide", dict(low=True)),
    (40, "bird_close", dict(char=0)),
    (44, "bird_close", dict(char=2, tight=True)),
    (48, "birds_wide", dict()),
    (52, "city_side", dict(char=1)),
    (56, "city_front", dict(char=2)),
    (60, "city_side", dict(char=0)),
    (64, "city_front", dict(char=2)),
    (68, "city_side", dict(char=1, rain=True)),
    (72, "city_side", dict(char=0)),
    (76, "cube_in", dict(chars=[0, 2, 1], confetti=True)),
    (80, "cube_in", dict(chars=[2], confetti=True)),
    (84, "cube_wide", dict(zoom=(1.1, 1.3), drift=True, fireworks=True)),
    (86, "cube_in", dict(chars=[0], confetti=True)),
    (88, "cube_in", dict(chars=[0, 2, 1], confetti=True)),
    (92, "outro", dict()),
]

G = {}  # per-process assets


# ---------------------------------------------------------------- helpers
def at(bar):
    return max(0.0, PHASE + bar * BAR)


def vgrad(h, stops, w=W):
    ys = np.linspace(0, 1, h)
    cols = np.zeros((h, 3))
    for c in range(3):
        cols[:, c] = np.interp(ys, [s[0] for s in stops], [s[1][c] for s in stops])
    return Image.fromarray(np.repeat(cols[:, None, :], w, axis=1).astype(np.uint8)).convert("RGBA")


def comp(base, im, x, y):
    """alpha-composite im onto base at (x, y), clipping to the canvas."""
    x, y = int(round(x)), int(round(y))
    l, t = max(0, -x), max(0, -y)
    r, b = min(im.width, base.width - x), min(im.height, base.height - y)
    if r <= l or b <= t:
        return
    base.alpha_composite(im.crop((l, t, r, b)) if (l, t, r, b) != (0, 0, im.width, im.height) else im,
                         (x + l, y + t))


def rng(seed):
    return np.random.default_rng(seed)


def ease(p):
    p = min(1, max(0, p))
    return p * p * (3 - 2 * p)


class Ctx:
    def __init__(self, t):
        self.t = t
        b = (t - PHASE) / BEAT
        self.beatn = math.floor(b)
        self.bp = b - self.beatn            # 0..1 within beat
        self.e = float(G["energy"][min(len(G["energy"]) - 1, int(t * FPS))])
        self.hit = math.exp(-6 * self.bp)   # decays after each beat


# ---------------------------------------------------------------- character
def char_img(i, h, mirror=False):
    key = (i, int(h) // 4 * 4, mirror)
    c = G["char_cache"]
    if key not in c:
        src = G["cuts"][i]
        im = src.resize((max(1, int(src.width * key[1] / src.height)), key[1]), Image.LANCZOS)
        if mirror:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if len(c) > 120:
            c.clear()
        c[key] = im
    return c[key]


def draw_char(base, i, cx, bottom, h, angle=0.0, squash=0.0, mirror=False, glow=None):
    """Paste character; returns the mouth point in canvas coords and facing."""
    im = char_img(i, h, mirror)
    if squash:
        im = im.resize((int(im.width * (1 + squash)), int(im.height * (1 - squash))), Image.BILINEAR)
    w0, h0 = im.size
    ox, oy = w0 / 2, h0  # rotate around bottom-centre
    if angle:
        big = Image.new("RGBA", (w0, h0 * 2), (0, 0, 0, 0))
        big.paste(im, (0, 0))
        im = big.rotate(angle, resample=Image.BICUBIC, expand=True)
        ox, oy = im.width / 2, im.height / 2
    if glow:
        a = im.getchannel("A").filter(ImageFilter.GaussianBlur(14))
        g = Image.new("RGBA", im.size, glow)
        g.putalpha(a.point(lambda v: int(v * 0.55)))
        comp(base, g, cx - ox, bottom - oy)
    comp(base, im, cx - ox, bottom - oy)
    mx, my, face = MOUTH[i]
    if mirror:
        mx, face = 1 - mx, -face
    dx, dy = (mx - 0.5) * w0, (my - 1) * h0
    a = math.radians(angle)
    px = cx + dx * math.cos(a) + dy * math.sin(a)
    py = bottom - dx * math.sin(a) + dy * math.cos(a)
    return px, py, face


def dance(ctx, k, amp=1.0):
    """bounce (px up), sway angle, squash, side-step for dancer k."""
    bp = (ctx.bp + 0.12 * k) % 1
    bounce = abs(math.sin(math.pi * bp)) * (14 + 30 * ctx.e) * amp
    beats = ctx.beatn + bp
    sway = 7 * math.sin(math.pi * beats / 2 + k) * amp
    squash = 0.05 * (1 - abs(math.sin(math.pi * bp))) ** 6 * amp
    step = 22 * math.sin(math.pi * beats / 4 + k * 2) * amp
    return bounce, sway, squash, step


def sing(layer, ctx, mouth, scale=1.0, seed=0):
    """Sound rings and music notes coming out of the mouth."""
    px, py, face = mouth
    d = ImageDraw.Draw(layer)
    for k in range(3):
        p = ((ctx.t * 1.6 + k / 3) % 1)
        r = (14 + 90 * p) * scale
        a = int(230 * (1 - p) * (0.35 + ctx.e))
        cx = px + face * r * 0.35
        box = [cx - r, py - r, cx + r, py + r]
        start = -50 if face > 0 else 130
        d.arc(box, start, start + 100, fill=(255, 240, 200, min(255, a)), width=max(2, int(4 * scale)))
    f = G["font_sym"]
    for k in range(3):
        p = ((ctx.t * 0.55 + k / 3 + seed * 0.13) % 1)
        x = px + face * (40 + 160 * p) * scale + 18 * math.sin(p * 9 + k) * scale
        y = py - (20 + 150 * p) * scale
        a = int(255 * math.sin(math.pi * p) * (0.4 + 0.6 * ctx.e))
        d.text((x, y), "♪♫"[k % 2], font=f, fill=(255, 225, 140, a), anchor="mm")


# ---------------------------------------------------------------- assets
def init(energy):
    G["energy"] = energy
    G["cuts"] = [Image.open(p).convert("RGBA") for p in CUTS]
    G["char_cache"] = {}
    G["font_sym"] = ImageFont.truetype(FONT_SYM, 44)
    G["font_t"] = ImageFont.truetype(FONT_B, 86)
    G["font_s"] = ImageFont.truetype(FONT_R, 30)

    # Night sea
    night = vgrad(H, [(0, (6, 8, 28)), (0.58, (46, 30, 86)), (0.6, (18, 26, 58)), (1, (2, 6, 18))])
    d = ImageDraw.Draw(night)
    r = rng(1)
    for _ in range(260):
        x, y = r.uniform(0, W), r.uniform(0, H * 0.55)
        s = r.uniform(0.6, 2.0)
        d.ellipse([x - s, y - s, x + s, y + s], fill=(255, 255, 255, int(r.uniform(90, 255))))
    moon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(moon)
    md.ellipse([1010 - 90, 120 - 90, 1010 + 90, 120 + 90], fill=(180, 190, 255, 70))
    moon = moon.filter(ImageFilter.GaussianBlur(30))
    md = ImageDraw.Draw(moon)
    md.ellipse([1010 - 38, 120 - 38, 1010 + 38, 120 + 38], fill=(245, 242, 225, 255))
    night.alpha_composite(moon)
    G["night"] = night

    # Sunset sea
    sun = vgrad(H, [(0, (34, 26, 84)), (0.35, (150, 60, 120)), (0.58, (255, 150, 90)),
                    (0.66, (255, 200, 130)), (0.665, (90, 80, 130)), (1, (18, 26, 60))])
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([900 - 220, 470 - 220, 900 + 220, 470 + 220], fill=(255, 200, 120, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    sun.alpha_composite(glow)
    gd = ImageDraw.Draw(sun)
    gd.ellipse([900 - 70, 470 - 70, 900 + 70, 470 + 70], fill=(255, 236, 190, 255))
    sun.paste(vgrad(H - 478, [(0, (110, 90, 140)), (1, (18, 26, 60))]), (0, 478))
    G["sunset"] = sun

    clouds = []
    for k in range(5):
        c = Image.new("RGBA", (520, 200), (0, 0, 0, 0))
        cd = ImageDraw.Draw(c)
        rr = rng(10 + k)
        for _ in range(9):
            x, y = rr.uniform(80, 440), rr.uniform(70, 130)
            s = rr.uniform(40, 80)
            cd.ellipse([x - s, y - s * 0.6, x + s, y + s * 0.6], fill=(255, 190, 170, 150))
        clouds.append(c.filter(ImageFilter.GaussianBlur(12)))
    G["clouds"] = clouds

    # City strips (tileable)
    G["city_far"] = city_strip(2600, 420, (24, 22, 60), 0.06, 3, seed=5)
    G["city_mid"] = city_strip(2600, 560, (14, 10, 34), 0.18, 1, seed=6, neon=True)
    G["city_sky"] = vgrad(H, [(0, (8, 6, 26)), (0.7, (70, 26, 80)), (1, (120, 50, 90))])


def city_strip(w, h, col, lit, minw, seed, neon=False):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = rng(seed)
    x = 0
    while x < w:
        bw = int(r.uniform(70, 180))
        bh = int(r.uniform(h * 0.35, h))
        if x + bw > w:
            bw = w - x
        d.rectangle([x, h - bh, x + bw - minw, h], fill=col + (255,))
        for wy in range(h - bh + 14, h - 10, 18):
            for wx in range(x + 8, x + bw - 12, 14):
                if r.random() < lit:
                    c = [(255, 214, 140), (255, 240, 200), (140, 200, 255)][int(r.integers(0, 3))]
                    d.rectangle([wx, wy, wx + 6, wy + 9], fill=c + (int(r.uniform(150, 255)),))
        if neon and r.random() < 0.45:
            c = [(255, 60, 170), (60, 220, 255), (255, 200, 60)][int(r.integers(0, 3))]
            ny = h - bh + int(r.uniform(20, 90))
            d.rounded_rectangle([x + 10, ny, x + bw - 16, ny + 16], 6, fill=c + (230,))
        x += bw
    glow = im.filter(ImageFilter.GaussianBlur(6))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(im)
    return out


# ---------------------------------------------------------------- water
def water(base, ctx, top, col, spec_x, n=140, seed=3, speed=40):
    d = ImageDraw.Draw(base)
    r = rng(seed)
    for k in range(n):
        y = top + (H - top) * (r.random() ** 1.6)
        depth = (y - top) / (H - top)
        x0 = (r.uniform(-200, W + 200) - ctx.t * speed * (0.3 + depth)) % (W + 400) - 200
        ln = 10 + 70 * depth
        near = math.exp(-((x0 - spec_x) / 220) ** 2)
        a = int((40 + 160 * near) * (0.6 + 0.4 * math.sin(ctx.t * 3 + k)))
        d.line([x0, y, x0 + ln, y], fill=col + (max(0, a),), width=1 + int(2 * depth))


def reflect(base, box, top, strength=0.45, t=0.0):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, x1 = max(0, x0), min(W, x1)
    y0 = max(0, y0)
    if x1 <= x0 or y1 <= y0:
        return
    reg = np.asarray(base.crop((x0, y0, x1, y1))).copy()[::-1]
    for i in range(reg.shape[0]):
        reg[i] = np.roll(reg[i], int(5 * math.sin(i * 0.25 + t * 4)), axis=0)
    hh = min(reg.shape[0], H - top)
    if hh <= 0:
        return
    reg = reg[:hh]
    fade = np.linspace(strength, 0, hh)[:, None]
    reg[..., 3] = (reg[..., 3] * fade).astype(np.uint8)
    comp(base, Image.fromarray(reg), x0, top)


# ---------------------------------------------------------------- party
def beams(w, h, ctx, n=6, top=0, alpha=1.0):
    lay = Image.new("RGBA", (w // 2, h // 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cols = [(255, 50, 200), (40, 220, 255), (255, 210, 60), (120, 90, 255), (60, 255, 160), (255, 90, 60)]
    for k in range(n):
        ox = (k + 0.5) / n * w / 2
        ang = math.radians(90 + 32 * math.sin(ctx.t * (0.7 + 0.13 * k) + k * 1.7))
        ln, sp = h, math.radians(7)
        p1 = (ox + ln * math.cos(ang - sp), top + ln * math.sin(ang - sp))
        p2 = (ox + ln * math.cos(ang + sp), top + ln * math.sin(ang + sp))
        a = int((60 + 120 * ctx.e + 60 * ctx.hit) * alpha)
        c = cols[(k + ctx.beatn // 4) % len(cols)]
        d.polygon([(ox, top), p1, p2], fill=c + (min(255, a),))
    return lay.filter(ImageFilter.GaussianBlur(6)).resize((w, h), Image.BILINEAR)


def crowd(w, h, ctx, scale=1.0, n=13, seed=4):
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    r = rng(seed)
    for k in range(n):
        x = (k + r.uniform(-0.3, 0.3)) / (n - 1) * w
        hs = r.uniform(0.85, 1.15) * scale
        bp = (ctx.bp + r.uniform(0, 0.3)) % 1
        y = h - (90 + 40 * r.random()) * scale - abs(math.sin(math.pi * bp)) * 16 * scale
        col = (14, 10, 26, 255)
        d.ellipse([x - 22 * hs, y - 60 * hs, x + 22 * hs, y - 14 * hs], fill=col)
        d.rounded_rectangle([x - 52 * hs, y - 16 * hs, x + 52 * hs, h + 10], int(30 * hs), fill=col)
        if r.random() < 0.55:  # arms up
            sgn = 1 if r.random() < 0.5 else -1
            wave = 14 * math.sin(ctx.t * 6 + k) * hs
            d.line([x + sgn * 40 * hs, y, x + sgn * (60 * hs + wave), y - 120 * hs], fill=col, width=int(16 * hs))
    return lay


def confetti(base, ctx, n=90, seed=8):
    d = ImageDraw.Draw(base)
    r = rng(seed)
    cols = [(255, 80, 180), (80, 220, 255), (255, 220, 80), (160, 255, 120), (255, 255, 255)]
    for k in range(n):
        x0, sp, ph = r.uniform(0, W), r.uniform(60, 160), r.uniform(0, 100)
        y = ((ctx.t + ph) * sp) % (H + 40) - 20
        x = x0 + 30 * math.sin(ctx.t * 2 + k)
        a = ctx.t * 5 + k
        dx, dy = 7 * math.cos(a), 4 * math.sin(a)
        d.polygon([(x - dx, y - dy), (x + dy, y - dx), (x + dx, y + dy), (x - dy, y + dx)],
                  fill=cols[k % len(cols)] + (230,))


def party_room(w, h, ctx, chars, p, small=False):
    """Inside the glass cube: sea view through glass, beams, dancers, crowd."""
    if small:
        room = vgrad(h, [(0, (40, 16, 70)), (1, (14, 6, 30))], w)
    else:
        room = G["night"].copy()
        room.alpha_composite(Image.new("RGBA", (W, H), (30, 0, 50, 90)))
    room.alpha_composite(beams(w, h, ctx, alpha=0.9 if small else 1.0))
    n = len(chars)
    for k, ci in enumerate(chars):
        bounce, sway, squash, step = dance(ctx, k, 0.6 if small else 1.0)
        hgt = h * ((0.62 if n == 1 else 0.5) if small else (0.98 if n == 1 else 0.74))
        cx = w * (k + 1) / (n + 1) + step * (w / W)
        if n == 1:
            cx = w * 0.5 + step * (w / W)
        bottom = h * (0.98 if small else (1.28 if n == 1 else 1.2)) - bounce * (h / H)
        glow = [(255, 80, 200, 255), (60, 220, 255, 255), (255, 200, 80, 255)][(k + ctx.beatn // 8) % 3]
        mouth = draw_char(room, ci, cx, bottom, hgt, sway, squash, glow=None if small else glow)
        if not small and (n == 1 or k == 1):
            sing(room, ctx, mouth, scale=hgt / 600, seed=k)
    room.alpha_composite(crowd(w, h, ctx, scale=h / H * (1.0 if small else 0.62), n=11 if small else 15))
    if p.get("confetti") and not small:
        confetti(room, ctx)
    if not small:  # glass mullions + reflections
        d = ImageDraw.Draw(room)
        for x in (W * 0.18, W * 0.82):
            d.line([x, 0, x, H], fill=(200, 240, 255, 70), width=6)
        d.line([0, H * 0.08, W, H * 0.08], fill=(200, 240, 255, 60), width=5)
        sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sheen)
        sx = (ctx.t * 120) % (W + 600) - 300
        sd.polygon([(sx, 0), (sx + 140, 0), (sx - 160, H), (sx - 300, H)], fill=(255, 255, 255, 18))
        room.alpha_composite(sheen)
    # strobe on downbeats
    if ctx.beatn % 4 == 0 and ctx.e > 0.5:
        room.alpha_composite(Image.new("RGBA", (w, h), (255, 255, 255, int(60 * ctx.hit))))
    return room


def scene_cube_wide(ctx, lt, dur, p):
    img = G["night"].copy()
    z0, z1 = p.get("zoom", (1, 1))
    z = z0 + (z1 - z0) * ease(lt / dur)
    s = 300 * z
    cx = W / 2 + (60 * math.sin(lt * 0.4) if p.get("drift") else 0)
    horizon = H * 0.6
    base_y = horizon + 40 * z
    # light spill on the water
    spill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(spill)
    c = [(255, 60, 200), (60, 200, 255), (255, 200, 80)][(ctx.beatn // 4) % 3]
    sd.ellipse([cx - s * 1.3, base_y - 20, cx + s * 1.3, base_y + s * 0.7], fill=c + (int(70 + 80 * ctx.e),))
    img.alpha_composite(spill.filter(ImageFilter.GaussianBlur(40)))
    water(img, ctx, int(horizon), (200, 210, 255), 1010)
    # cube faces
    fw, fh = int(s), int(s * 0.82)
    x0, y0 = cx - fw / 2, base_y - fh
    side = s * 0.28
    room = party_room(fw, fh, ctx, [2] if ctx.beatn % 16 < 8 else [0, 2, 1], p, small=True)
    comp(img, room, x0, y0)
    d = ImageDraw.Draw(img)
    d.polygon([(x0 + fw, y0), (x0 + fw + side, y0 - side * 0.5), (x0 + fw + side, base_y - side * 0.5),
               (x0 + fw, base_y)], fill=(70, 40, 120, 160))
    d.polygon([(x0, y0), (x0 + side, y0 - side * 0.5), (x0 + fw + side, y0 - side * 0.5), (x0 + fw, y0)],
              fill=(150, 200, 255, 70))
    tint = Image.new("RGBA", (fw, fh), (160, 220, 255, 36))
    comp(img, tint, x0, y0)
    edges = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ed = ImageDraw.Draw(edges)
    lines = [((x0, y0), (x0 + fw, y0)), ((x0 + fw, y0), (x0 + fw, base_y)), ((x0, base_y), (x0 + fw, base_y)),
             ((x0, y0), (x0, base_y)), ((x0, y0), (x0 + side, y0 - side * 0.5)),
             ((x0 + fw, y0), (x0 + fw + side, y0 - side * 0.5)),
             ((x0 + side, y0 - side * 0.5), (x0 + fw + side, y0 - side * 0.5)),
             ((x0 + fw + side, y0 - side * 0.5), (x0 + fw + side, base_y - side * 0.5)),
             ((x0 + fw, base_y), (x0 + fw + side, base_y - side * 0.5))]
    for a, b in lines:
        ed.line([a, b], fill=(210, 245, 255, 255), width=max(2, int(3 * z)))
    img.alpha_composite(edges.filter(ImageFilter.GaussianBlur(5)))
    img.alpha_composite(edges)
    reflect(img, (x0 - 4, y0 - side * 0.5, x0 + fw + side + 4, base_y), int(base_y), 0.5, ctx.t)
    if p.get("fireworks"):
        fireworks(img, ctx)
    return img


def fireworks(img, ctx):
    d = ImageDraw.Draw(img)
    for k in range(3):
        period = 2 * BAR
        tt = (ctx.t + k * period / 3) % period
        r = rng(int((ctx.t + k * period / 3) // period) * 7 + k)
        cx, cy = r.uniform(200, W - 200), r.uniform(80, 260)
        c = [(255, 90, 200), (90, 220, 255), (255, 220, 100)][k]
        rad = 160 * ease(tt / 1.2)
        a = int(255 * max(0, 1 - tt / 1.8))
        for j in range(26):
            ang = j / 26 * 2 * math.pi
            x, y = cx + rad * math.cos(ang), cy + rad * math.sin(ang) + 30 * (tt ** 2)
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=c + (a,))


def scene_cube_in(ctx, lt, dur, p):
    img = party_room(W, H, ctx, p["chars"], p)
    # camera punch on the beat
    z = 1 + 0.025 * ctx.hit * ctx.e
    if z > 1.001:
        cw, ch = int(W / z), int(H / z)
        img = img.crop(((W - cw) // 2, (H - ch) // 2, (W - cw) // 2 + cw, (H - ch) // 2 + ch)).resize((W, H), Image.BILINEAR)
    return img


# ---------------------------------------------------------------- birds
def draw_bird(lay, x, y, s, flap, face=1, rider=None, ctx=None, dark=False):
    """Original giant sea-bird, side view. Returns rider mouth if any."""
    d = ImageDraw.Draw(lay)
    X = lambda dx: x + face * dx * s
    Y = lambda dy: y + dy * s
    body = (238, 236, 244) if not dark else (180, 170, 200)
    wing = (190, 192, 214) if not dark else (140, 130, 170)
    tip = (52, 50, 70)
    rim = (255, 190, 130)

    def wing_poly(f, off, col):
        pts = [(X(0.10 + off), Y(-0.04)), (X(0.02 + off), Y(-0.05 - 0.32 * f)),
               (X(-0.30 + off), Y(-0.02 - 0.58 * f)), (X(-0.24 + off), Y(-0.40 * f + 0.02)),
               (X(-0.20 + off), Y(-0.28 * f + 0.03)), (X(-0.16 + off), Y(-0.16 * f + 0.03)),
               (X(-0.14 + off), Y(0.0))]
        d.polygon(pts, fill=col)
        tpts = [pts[2], (X(-0.24 + off), Y(-0.40 * f + 0.02)),
                (X(-0.18 + off), Y(-0.02 - 0.48 * f)), ]
        d.polygon(tpts, fill=tip)
        d.line(pts[:3], fill=rim, width=max(2, int(s * 0.006)))
        for q in (0.35, 0.6):
            a0, a1 = pts[1], pts[2]
            d.line([(pts[6][0] + (a0[0] - pts[6][0]) * q, pts[6][1] + (a0[1] - pts[6][1]) * q),
                    (pts[5][0] + (a1[0] - pts[5][0]) * q, pts[5][1] + (a1[1] - pts[5][1]) * q)],
                   fill=tuple(int(c * 0.85) for c in col), width=max(1, int(s * 0.004)))

    wing_poly(flap * 0.9, 0.05, tuple(int(c * 0.78) for c in wing))  # far wing
    wing_poly(flap, -0.02, wing)  # near wing
    d = ImageDraw.Draw(lay)
    mouth = None
    if rider is not None:
        i, mirror = rider
        bounce = abs(math.sin(math.pi * ctx.bp)) * 8 * s / 900
        sway = 4 * math.sin(math.pi * (ctx.beatn + ctx.bp) / 2)
        mouth = draw_char(lay, i, X(-0.02), Y(0.035) - bounce, 0.36 * s, sway * face, 0, mirror)
        d = ImageDraw.Draw(lay)
    d.polygon([(X(-0.18), Y(-0.03)), (X(-0.34), Y(-0.08)), (X(-0.33), Y(0.0)), (X(-0.34), Y(0.05))], fill=body)
    d.ellipse(sorted_box(X(-0.22), Y(-0.07), X(0.19), Y(0.075)), fill=body)
    d.chord(sorted_box(X(-0.20), Y(-0.03), X(0.17), Y(0.075)), 0, 180, fill=tuple(int(c * 0.82) for c in body))
    d.ellipse(sorted_box(X(0.15), Y(-0.12), X(0.27), Y(-0.01)), fill=body)
    d.polygon([(X(0.255), Y(-0.085)), (X(0.37), Y(-0.05)), (X(0.255), Y(-0.035))], fill=(255, 170, 40))
    d.ellipse(sorted_box(X(0.215), Y(-0.085), X(0.233), Y(-0.067)), fill=(20, 20, 30))
    d.arc(sorted_box(X(-0.22), Y(-0.07), X(0.19), Y(0.075)), 180 if face > 0 else 0, 360 if face > 0 else 180,
          fill=rim, width=max(2, int(s * 0.006)))
    return mouth


def sorted_box(a, b, c, e):
    return [min(a, c), min(b, e), max(a, c), max(b, e)]


def sky_sea(ctx, speed=1.0):
    img = G["sunset"].copy()
    for k, c in enumerate(G["clouds"]):
        y = 20 + 48 * k
        x = (900 + k * 380 - ctx.t * (25 + 12 * k) * speed) % (W + 600) - 520
        img.alpha_composite(c, (int(x), int(y))) if 0 <= x <= W - c.width else comp(img, c, x, y)
    water(img, ctx, 478, (255, 215, 160), 900, n=170, speed=160 * speed)
    return img


def flap(t, ph=0.0):
    # one full flap per bar, snappy down-stroke
    p = ((t - PHASE) / BAR + ph) % 1
    return math.cos(2 * math.pi * p) * 0.68 + 0.32


def scene_birds_wide(ctx, lt, dur, p, outro=False):
    img = sky_sea(ctx)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    birds = [(0, 0.62, 0.30, 420, 2, False, 0.0), (1, 0.34, 0.42, 520, 1, False, 0.33),
             (2, 0.72, 0.58, 640, 0, True, 0.66)]
    if p.get("low"):
        birds = [(0, 0.25, 0.25, 380, 0, True, 0.2), (1, 0.55, 0.35, 470, 2, False, 0.5),
                 (2, 0.40, 0.62, 700, 1, False, 0.8)]
    mouths = []
    for k, fx, fy, s, ci, mir, ph in birds:
        drift = 40 * math.sin(ctx.t * 0.5 + k * 2)
        x = W * fx + drift + (lt / dur - 0.5) * 120
        y = H * fy + 22 * math.sin(ctx.t * 1.3 + k)
        if outro:
            pr = ease(lt / dur)
            x += pr * 500 * (1 + k * 0.4)
            y -= pr * 140 * (1 + k * 0.2)
            s *= 1 - 0.55 * pr
        m = draw_bird(lay, x, y, s, flap(ctx.t, ph), 1, (ci, mir), ctx)
        mouths.append((m, s))
    img.alpha_composite(lay)
    fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m, s = mouths[-1]
    sing(fx, ctx, m, scale=s / 1100)
    img.alpha_composite(fx)
    return img


def scene_bird_close(ctx, lt, dur, p):
    img = sky_sea(ctx, speed=1.6)
    # wind streaks
    d = ImageDraw.Draw(img)
    r = rng(12)
    for k in range(18):
        y0 = r.uniform(0, H)
        x0 = (r.uniform(0, W) - ctx.t * 900) % (W + 300) - 150
        d.line([x0, y0, x0 + 120, y0], fill=(255, 255, 255, 50), width=2)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ci = p["char"]
    mirror = ci == 0  # graffiti photo looks left; mirror so he faces forward
    s = 1500 if not p.get("tight") else 1850
    x = W * 0.52 + 30 * math.sin(ctx.t * 0.7)
    y = H * 0.86 + 26 * math.sin(ctx.t * 1.2) + (60 if p.get("tight") else 0)
    m = draw_bird(lay, x, y, s, flap(ctx.t), 1, (ci, mirror), ctx)
    # a second bird keeping pace in the distance
    draw_bird(lay, W * 0.16 + 20 * math.sin(ctx.t), H * 0.30, 260, flap(ctx.t, 0.4), 1,
              ((ci + 1) % 3, False), ctx, dark=True)
    img.alpha_composite(lay)
    fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sing(fx, ctx, m, scale=1.2)
    img.alpha_composite(fx)
    return img


# ---------------------------------------------------------------- city
def scene_city_side(ctx, lt, dur, p):
    img = G["city_sky"].copy()
    for strip, spd, y in ((G["city_far"], 30, H - 420 - 60), (G["city_mid"], 110, H - 560 + 20)):
        off = int(ctx.t * spd) % strip.width
        comp(img, strip, -off, y)
        comp(img, strip, strip.width - off, y)
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 70, W, H], fill=(30, 22, 44, 255))
    # bokeh
    bok = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bok)
    r = rng(21)
    for k in range(40):
        x = (r.uniform(0, W * 2) - ctx.t * 200) % (W + 200) - 100
        y = r.uniform(H * 0.3, H * 0.9)
        rad = r.uniform(10, 34)
        c = [(255, 200, 120), (255, 90, 160), (110, 200, 255)][k % 3]
        bd.ellipse([x - rad, y - rad, x + rad, y + rad], fill=c + (60,))
    img.alpha_composite(bok.filter(ImageFilter.GaussianBlur(3)))
    # walking: one step per beat
    ci = p["char"]
    mirror = ci == 0
    bob = abs(math.sin(math.pi * ctx.bp)) * 18
    tilt = 2.5 * math.sin(math.pi * (ctx.beatn + ctx.bp))
    m = draw_char(img, ci, W * 0.46, H + 150 - bob, H * 0.98, tilt, 0, mirror)
    fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sing(fx, ctx, m, scale=1.1)
    img.alpha_composite(fx)
    # street lamps passing in the foreground
    lamps = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lamps)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for k in range(3):
        x = (k * 620 - ctx.t * 420) % (W + 600) - 300
        ld.rectangle([x, 70, x + 22, H], fill=(16, 12, 24, 255))
        ld.rounded_rectangle([x - 30, 52, x + 52, 76], 10, fill=(20, 16, 30, 255))
        ld.ellipse([x - 22, 70, x + 44, 92], fill=(255, 236, 190, 255))
        gd.ellipse([x - 140, -40, x + 160, 220], fill=(255, 210, 140, 110))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(40)))
    img.alpha_composite(lamps)
    if p.get("rain"):
        d = ImageDraw.Draw(img)
        r = rng(31)
        for k in range(160):
            x = (r.uniform(0, W) - ctx.t * 140) % W
            y = (r.uniform(0, H) + ctx.t * 900) % H
            d.line([x, y, x - 6, y + 24], fill=(200, 220, 255, 90), width=1)
    return img


def scene_city_front(ctx, lt, dur, p):
    img = G["city_sky"].copy()
    z = 1 + 0.25 * lt / dur
    for strip, y, k in ((G["city_far"], H - 420 - 60, 0.6), (G["city_mid"], H - 560 + 30, 1.0)):
        zz = 1 + (z - 1) * k
        cw = int(W / zz)
        crop = strip.crop((600, 0, 600 + cw, strip.height)).resize((W, int(strip.height * zz)), Image.BILINEAR)
        comp(img, crop, 0, y - (crop.height - strip.height) / 2)
    d = ImageDraw.Draw(img)
    d.polygon([(0, H), (W * 0.42, H * 0.70), (W * 0.58, H * 0.70), (W, H)], fill=(40, 28, 52, 255))
    bok = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bok)
    r = rng(41)
    for k in range(36):
        ang = r.uniform(0, 2 * math.pi)
        prog = (r.random() + ctx.t * 0.25) % 1
        dist = 80 + prog ** 2 * 900
        x, y = W / 2 + math.cos(ang) * dist, H * 0.55 + math.sin(ang) * dist * 0.6
        rad = 6 + 40 * prog
        c = [(255, 200, 120), (255, 90, 160), (110, 200, 255)][k % 3]
        bd.ellipse([x - rad, y - rad, x + rad, y + rad], fill=c + (int(90 * prog),))
    img.alpha_composite(bok.filter(ImageFilter.GaussianBlur(4)))
    bob = abs(math.sin(math.pi * ctx.bp)) * 16
    sway = 3 * math.sin(math.pi * (ctx.beatn + ctx.bp))
    hgt = H * (0.92 + 0.08 * lt / dur)
    m = draw_char(img, p["char"], W * 0.5 + 10 * math.sin(math.pi * (ctx.beatn + ctx.bp)), H + 130 - bob, hgt, sway)
    fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sing(fx, ctx, m, scale=1.2)
    img.alpha_composite(fx)
    return img


def scene_outro(ctx, lt, dur, p):
    return scene_birds_wide(ctx, lt, dur, p, outro=True)


SCENES = dict(cube_wide=scene_cube_wide, cube_in=scene_cube_in, birds_wide=scene_birds_wide,
              bird_close=scene_bird_close, city_side=scene_city_side, city_front=scene_city_front,
              outro=scene_outro)


# ---------------------------------------------------------------- titles / frame
def title(img, text, sub, alpha, y):
    if alpha <= 0:
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a = int(255 * alpha)
    d.text((W / 2 + 3, y + 3), text, font=G["font_t"], fill=(0, 0, 0, a // 2), anchor="mm")
    d.text((W / 2, y), text, font=G["font_t"], fill=(255, 255, 255, a), anchor="mm")
    d.text((W / 2, y + 70), sub, font=G["font_s"], fill=(255, 230, 200, a), anchor="mm")
    img.alpha_composite(lay)


def window(t, a, b, f=0.8):
    return max(0, min(1, (t - a) / f, (b - t) / f))


def render(fi):
    t = fi / FPS
    ctx = Ctx(t)
    starts = [at(s[0]) if s[0] >= 0 else 0 for s in SHOTS]
    k = max(i for i, s in enumerate(starts) if s <= t)
    st = starts[k]
    en = starts[k + 1] if k + 1 < len(starts) else G["total"]
    _, name, p = SHOTS[k]
    img = SCENES[name](ctx, t - st, en - st, p)
    if t < 2.5:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - t / 2.5)))))
    if k > 0 and t - st < 0.25:
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(220 * (1 - (t - st) / 0.25)))))
    title(img, "FIFTY MILLION", "JDP / JOHN DA POET", window(t, 1.5, at(4) - 0.4), H * 0.2)
    tot = G["total"]
    title(img, "JDP / JOHN DA POET", "Fifty Million", window(t, tot - 16, tot - 1.5), H * 0.78)
    if t > tot - 3.5:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * min(1, (t - tot + 3.5) / 3.5)))))
    return img.convert("RGB").tobytes()


def worker_init(energy, total):
    init(energy)
    G["total"] = total


def load_energy(audio, total):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", audio, "-vn", "-ac", "1", "-ar", "12000",
                          "-f", "s16le", "-"], stdout=subprocess.PIPE, check=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32)
    hop = 12000 // FPS
    n = int(total * FPS) + 1
    a = np.pad(a, (0, max(0, n * hop - len(a))))[: n * hop].reshape(n, hop)
    rms = np.sqrt((a ** 2).mean(1))
    rms /= np.percentile(rms, 95) + 1e-6
    out, v = np.zeros(n, np.float32), 0.0
    for i, x in enumerate(np.clip(rms, 0, 1.2)):
        v = x if x > v else v * 0.88 + x * 0.12
        out[i] = v
    return np.clip(out, 0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--dur", type=float, help="render only this many seconds (preview)")
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--crf", type=int, default=20)
    a = ap.parse_args()
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", a.audio]).strip())
    energy = load_energy(a.audio, total)
    f0 = int(a.start * FPS)
    f1 = int(min(total, a.start + a.dur) * FPS) if a.dur else int(total * FPS)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-ss", str(a.start), "-t", str((f1 - f0) / FPS), "-i", a.audio,
                            "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium",
                            "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                            "-movflags", "+faststart", "-shortest", a.out], stdin=subprocess.PIPE)
    with Pool(a.jobs, worker_init, (energy, total)) as pool:
        for i, fr in enumerate(pool.imap(render, range(f0, f1), chunksize=8)):
            enc.stdin.write(fr)
            if i % 300 == 0:
                print(f"frame {i}/{f1 - f0}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", a.out)


if __name__ == "__main__":
    main()
